#!/usr/bin/env python3
"""
Recommend script for Shopify orders data pipeline.
Outputs transformation results as JSON and writes to PostgreSQL.
"""

import json
import logging
from typing import Dict, List, Tuple, Any
from sqlalchemy import create_engine, text
import os
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RecommendationExporter:
    """Handles exporting recommendations to JSON and PostgreSQL."""
    
    def __init__(self, connection_string: str = None):
        """
        Initialize database connection.
        
        Args:
            connection_string: PostgreSQL connection string
        """
        if connection_string is None:
            # Use Docker hostname when running in containers, localhost for local development
            import os
            if os.environ.get('AIRFLOW_HOME'):
                # Running in Airflow container
                connection_string = "postgresql://airflow:airflow@postgres:5432/airflow"
            else:
                # Running locally
                connection_string = "postgresql://airflow:airflow@localhost:5433/airflow"
        
        self.engine = create_engine(connection_string)
    
    def export_to_json(self, confidence_scores: Dict[str, List[Tuple[str, float]]], output_path: str = None) -> str:
        """
        Export confidence scores to JSON file.
        
        Args:
            confidence_scores: Dictionary with base SKU as key and list of (related_sku, confidence) tuples
            output_path: Path to output JSON file
            
        Returns:
            Path to the created JSON file
        """
        try:
            if output_path is None:
                # Default output path
                output_path = Path(__file__).parent.parent / "data" / "related_items.json"
            
            # Ensure output directory exists
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert tuples to lists for JSON serialization
            json_data = {}
            for base_sku, related_items in confidence_scores.items():
                json_data[base_sku] = [[sku, confidence] for sku, confidence in related_items]
            
            # Write to JSON file
            with open(output_path, 'w') as f:
                json.dump(json_data, f, indent=2)
            
            logger.info(f"Recommendations exported to JSON: {output_path}")
            logger.info(f"Exported {len(json_data)} item associations")
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error exporting to JSON: {str(e)}")
            raise
    
    def clear_related_items_table(self):
        """Clear the related_items table before inserting new data."""
        try:
            with self.engine.begin() as conn:
                conn.execute(text("DELETE FROM related_items"))
            
            logger.info("Cleared related_items table")
            
        except Exception as e:
            logger.error(f"Error clearing related_items table: {str(e)}")
            raise
    
    def insert_recommendations(self, confidence_scores: Dict[str, List[Tuple[str, float]]]):
        """
        Insert recommendations into the related_items table.
        
        Args:
            confidence_scores: Dictionary with base SKU as key and list of (related_sku, confidence) tuples
        """
        try:
            logger.info("Inserting recommendations into database...")
            
            # Clear existing data
            self.clear_related_items_table()
            
            # Insert new recommendations
            with self.engine.begin() as conn:
                inserted_count = 0
                
                for base_sku, related_items in confidence_scores.items():
                    for related_sku, confidence in related_items:
                        try:
                            conn.execute(
                                text("""
                                    INSERT INTO related_items (base_sku, related_sku, confidence)
                                    VALUES (:base_sku, :related_sku, :confidence)
                                """),
                                {
                                    "base_sku": base_sku,
                                    "related_sku": related_sku,
                                    "confidence": confidence
                                }
                            )
                            inserted_count += 1
                            
                        except Exception as e:
                            logger.warning(f"Error inserting {base_sku} -> {related_sku}: {str(e)}")
                            continue
            
            logger.info(f"Successfully inserted {inserted_count} recommendations")
            
        except Exception as e:
            logger.error(f"Error inserting recommendations: {str(e)}")
            raise
    
    def export_recommendations(self, confidence_scores: Dict[str, List[Tuple[str, float]]]) -> str:
        """
        Main export method - exports to both JSON and PostgreSQL.
        
        Args:
            confidence_scores: Dictionary with base SKU as key and list of (related_sku, confidence) tuples
            
        Returns:
            Path to the created JSON file
        """
        try:
            logger.info("Starting recommendation export...")
            
            # Export to JSON
            json_path = self.export_to_json(confidence_scores)
            
            # Export to PostgreSQL
            self.insert_recommendations(confidence_scores)
            
            logger.info("Recommendation export completed successfully")
            return json_path
            
        except Exception as e:
            logger.error(f"Recommendation export failed: {str(e)}")
            raise
    
    def get_recommendations_from_db(self, base_sku: str = None) -> List[Dict[str, Any]]:
        """
        Retrieve recommendations from the database.
        
        Args:
            base_sku: Optional base SKU to filter by
            
        Returns:
            List of recommendation dictionaries
        """
        try:
            if base_sku:
                query = """
                    SELECT base_sku, related_sku, confidence, created_at
                    FROM related_items
                    WHERE base_sku = :base_sku
                    ORDER BY confidence DESC
                """
                params = {"base_sku": base_sku}
            else:
                query = """
                    SELECT base_sku, related_sku, confidence, created_at
                    FROM related_items
                    ORDER BY base_sku, confidence DESC
                """
                params = {}
            
            with self.engine.connect() as conn:
                result = conn.execute(text(query), params)
                recommendations = [
                    {
                        "base_sku": row[0],
                        "related_sku": row[1],
                        "confidence": float(row[2]),
                        "created_at": str(row[3])
                    }
                    for row in result.fetchall()
                ]
            
            logger.info(f"Retrieved {len(recommendations)} recommendations from database")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error retrieving recommendations: {str(e)}")
            return []
    
    def close(self):
        """Close database connection."""
        self.engine.dispose()
        logger.info("Database connection closed")


def main():
    """Main function for standalone execution."""
    from transform import ItemAssociationTransformer
    
    try:
        # Get transformation results
        transformer = ItemAssociationTransformer()
        confidence_scores = transformer.transform_data()
        transformer.close()
        
        if not confidence_scores:
            logger.error("No confidence scores to export")
            return
        
        # Export recommendations
        exporter = RecommendationExporter()
        json_path = exporter.export_recommendations(confidence_scores)
        exporter.close()
        
        logger.info(f"Recommendations exported successfully to: {json_path}")
        
        # Display sample results
        logger.info("Sample recommendations:")
        for base_sku, related_items in list(confidence_scores.items())[:3]:
            logger.info(f"{base_sku}: {related_items[:3]}")
        
    except Exception as e:
        logger.error(f"Recommendation export failed: {str(e)}")


if __name__ == "__main__":
    main()
