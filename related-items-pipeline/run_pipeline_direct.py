#!/usr/bin/env python3
"""
Direct pipeline runner that bypasses Airflow.
Tests the complete pipeline end-to-end.
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def run_pipeline():
    """Run the complete pipeline directly."""
    print("🚀 Running Related Items Pipeline Directly...")
    print()
    
    try:
        # Step 1: Extract data
        print("📊 Step 1: Extracting CSV data...")
        from extract import extract_orders_from_csv
        
        csv_path = Path(__file__).parent / "data" / "ordersData.csv"
        orders_data = extract_orders_from_csv(str(csv_path))
        
        if not orders_data:
            raise ValueError("No data extracted from CSV")
        
        print(f"✅ Extracted {len(orders_data)} orders with items")
        print()
        
        # Step 2: Load to database
        print("🗄️ Step 2: Loading data to PostgreSQL...")
        from load import DatabaseLoader
        
        loader = DatabaseLoader()
        loader.create_tables_if_not_exist()
        loader.load_orders_data(orders_data)
        loader.close()
        
        print("✅ Data loaded to PostgreSQL successfully")
        print()
        
        # Step 3: Transform data
        print("🔄 Step 3: Generating item associations...")
        from transform import ItemAssociationTransformer
        
        transformer = ItemAssociationTransformer()
        confidence_scores = transformer.transform_data()
        transformer.close()
        
        if not confidence_scores:
            raise ValueError("No confidence scores generated")
        
        total_associations = sum(len(related) for related in confidence_scores.values())
        print(f"✅ Generated {total_associations} item associations for {len(confidence_scores)} items")
        print()
        
        # Step 4: Export results
        print("📤 Step 4: Exporting recommendations...")
        from recommend import RecommendationExporter
        
        exporter = RecommendationExporter()
        json_path = exporter.export_recommendations(confidence_scores)
        exporter.close()
        
        print(f"✅ Recommendations exported to {json_path} and PostgreSQL")
        print()
        
        # Display results
        print("🎉 Pipeline completed successfully!")
        print()
        print("📊 Results Summary:")
        print(f"   - Orders processed: {len(orders_data)}")
        print(f"   - Items analyzed: {len(confidence_scores)}")
        print(f"   - Associations generated: {total_associations}")
        print(f"   - Output file: {json_path}")
        print()
        print("🔍 Sample recommendations:")
        for base_sku, related_items in list(confidence_scores.items())[:3]:
            print(f"   {base_sku}: {related_items[:3]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Pipeline failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_pipeline()
    sys.exit(0 if success else 1)
