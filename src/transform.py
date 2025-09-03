#!/usr/bin/env python3
"""
Transform script for Shopify orders data pipeline.
Builds item association matrix and calculates confidence scores.
"""

import logging
from typing import Dict, List, Tuple, Any
from sqlalchemy import create_engine, text
from collections import defaultdict, Counter
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ItemAssociationTransformer:
    """Handles transformation of order data into item associations."""
    
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
    
    def get_order_items_data(self) -> List[Tuple[str, str]]:
        """
        Retrieve order items data from database.
        
        Returns:
            List of tuples (order_number, sku)
        """
        try:
            query = """
                SELECT o.order_number, i.sku
                FROM orders o
                JOIN order_items oi ON o.id = oi.order_id
                JOIN items i ON oi.item_id = i.id
                ORDER BY o.order_number, i.sku
            """
            
            with self.engine.connect() as conn:
                result = conn.execute(text(query))
                data = [(row[0], row[1]) for row in result.fetchall()]
            
            logger.info(f"Retrieved {len(data)} order-item combinations")
            return data
            
        except Exception as e:
            logger.error(f"Error retrieving order items data: {str(e)}")
            raise
    
    def build_co_occurrence_matrix(self, order_items: List[Tuple[str, str]]) -> Dict[str, Dict[str, int]]:
        """
        Build co-occurrence matrix from order items data.
        
        Args:
            order_items: List of (order_number, sku) tuples
            
        Returns:
            Dictionary with SKU as key and dict of related SKUs with counts as value
        """
        try:
            logger.info("Building co-occurrence matrix...")
            
            # Group items by order
            orders_dict = defaultdict(set)
            for order_number, sku in order_items:
                orders_dict[order_number].add(sku)
            
            # Build co-occurrence matrix
            co_occurrence = defaultdict(lambda: defaultdict(int))
            item_counts = Counter()
            
            for order_items_set in orders_dict.values():
                # Count individual items
                for sku in order_items_set:
                    item_counts[sku] += 1
                
                # Count co-occurrences
                items_list = list(order_items_set)
                for i, sku1 in enumerate(items_list):
                    for sku2 in items_list[i+1:]:
                        co_occurrence[sku1][sku2] += 1
                        co_occurrence[sku2][sku1] += 1
            
            logger.info(f"Co-occurrence matrix built for {len(co_occurrence)} items")
            return dict(co_occurrence)
            
        except Exception as e:
            logger.error(f"Error building co-occurrence matrix: {str(e)}")
            raise
    
    def calculate_confidence_scores(self, co_occurrence: Dict[str, Dict[str, int]]) -> Dict[str, List[Tuple[str, float]]]:
        """
        Calculate confidence scores for item associations.
        
        Args:
            co_occurrence: Co-occurrence matrix
            
        Returns:
            Dictionary with base SKU as key and list of (related_sku, confidence) tuples
        """
        try:
            logger.info("Calculating confidence scores...")
            
            # Get total counts for each item
            item_counts = {}
            for base_sku, related_items in co_occurrence.items():
                item_counts[base_sku] = sum(related_items.values())
            
            # Calculate confidence scores
            confidence_scores = {}
            
            for base_sku, related_items in co_occurrence.items():
                base_count = item_counts[base_sku]
                related_scores = []
                
                for related_sku, co_count in related_items.items():
                    # Confidence = P(related_sku | base_sku) = co_occurrence / base_sku_count
                    confidence = co_count / base_count
                    related_scores.append((related_sku, round(confidence, 4)))
                
                # Sort by confidence (descending) and take top 10
                related_scores.sort(key=lambda x: x[1], reverse=True)
                confidence_scores[base_sku] = related_scores[:10]
            
            logger.info(f"Confidence scores calculated for {len(confidence_scores)} items")
            return confidence_scores
            
        except Exception as e:
            logger.error(f"Error calculating confidence scores: {str(e)}")
            raise
    
    def get_item_names(self, skus: set) -> Dict[str, str]:
        """
        Get item names for given SKUs.
        
        Args:
            skus: Set of SKUs
            
        Returns:
            Dictionary mapping SKU to name
        """
        try:
            if not skus:
                return {}
            
            placeholders = ','.join([f"'{sku}'" for sku in skus])
            query = f"SELECT sku, name FROM items WHERE sku IN ({placeholders})"
            
            with self.engine.connect() as conn:
                result = conn.execute(text(query))
                return {row[0]: row[1] for row in result.fetchall()}
                
        except Exception as e:
            logger.error(f"Error retrieving item names: {str(e)}")
            return {}
    
    def transform_data(self) -> Dict[str, List[Tuple[str, float]]]:
        """
        Main transformation method.
        
        Returns:
            Dictionary with base SKU as key and list of (related_sku, confidence) tuples
        """
        try:
            # Get order items data
            order_items = self.get_order_items_data()
            
            if not order_items:
                logger.warning("No order items data found")
                return {}
            
            # Build co-occurrence matrix
            co_occurrence = self.build_co_occurrence_matrix(order_items)
            
            # Calculate confidence scores
            confidence_scores = self.calculate_confidence_scores(co_occurrence)
            
            # Log some statistics
            total_associations = sum(len(related) for related in confidence_scores.values())
            logger.info(f"Generated {total_associations} item associations")
            
            # Log sample results
            sample_items = list(confidence_scores.keys())[:3]
            for sku in sample_items:
                if sku in confidence_scores:
                    logger.info(f"Sample associations for {sku}: {confidence_scores[sku][:3]}")
            
            return confidence_scores
            
        except Exception as e:
            logger.error(f"Transformation failed: {str(e)}")
            raise
    
    def close(self):
        """Close database connection."""
        self.engine.dispose()
        logger.info("Database connection closed")


def main():
    """Main function for standalone execution."""
    try:
        transformer = ItemAssociationTransformer()
        confidence_scores = transformer.transform_data()
        transformer.close()
        
        if confidence_scores:
            logger.info("Transformation completed successfully")
            logger.info(f"Generated associations for {len(confidence_scores)} items")
            
            # Print sample results
            for base_sku, related_items in list(confidence_scores.items())[:3]:
                logger.info(f"{base_sku}: {related_items[:3]}")
        else:
            logger.warning("No associations generated")
            
        return confidence_scores
        
    except Exception as e:
        logger.error(f"Transformation failed: {str(e)}")
        return None


if __name__ == "__main__":
    main()
