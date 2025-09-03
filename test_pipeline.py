#!/usr/bin/env python3
"""
Test script for the related items pipeline.
Tests all components individually to ensure they work correctly.
"""

import sys
import os
import json
from pathlib import Path

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_extract():
    """Test the extract functionality."""
    print("🧪 Testing extract.py...")
    try:
        from extract import extract_orders_from_csv
        
        csv_path = Path(__file__).parent / "data" / "ordersData.csv"
        orders_data = extract_orders_from_csv(str(csv_path))
        
        if orders_data and len(orders_data) > 0:
            print(f"✅ Extract test passed: {len(orders_data)} orders extracted")
            return orders_data
        else:
            print("❌ Extract test failed: No data extracted")
            return None
            
    except Exception as e:
        print(f"❌ Extract test failed: {str(e)}")
        return None

def test_load(orders_data):
    """Test the load functionality."""
    print("🧪 Testing load.py...")
    try:
        from load import DatabaseLoader
        
        # Test database connection
        loader = DatabaseLoader()
        loader.create_tables_if_not_exist()
        print("✅ Database connection and table creation successful")
        
        # Test data loading
        loader.load_orders_data(orders_data)
        loader.close()
        print("✅ Load test passed: Data loaded successfully")
        return True
        
    except Exception as e:
        print(f"❌ Load test failed: {str(e)}")
        return False

def test_transform():
    """Test the transform functionality."""
    print("🧪 Testing transform.py...")
    try:
        from transform import ItemAssociationTransformer
        
        transformer = ItemAssociationTransformer()
        confidence_scores = transformer.transform_data()
        transformer.close()
        
        if confidence_scores and len(confidence_scores) > 0:
            print(f"✅ Transform test passed: {len(confidence_scores)} items processed")
            return confidence_scores
        else:
            print("❌ Transform test failed: No confidence scores generated")
            return None
            
    except Exception as e:
        print(f"❌ Transform test failed: {str(e)}")
        return None

def test_recommend(confidence_scores):
    """Test the recommend functionality."""
    print("🧪 Testing recommend.py...")
    try:
        from recommend import RecommendationExporter
        
        exporter = RecommendationExporter()
        json_path = exporter.export_recommendations(confidence_scores)
        exporter.close()
        
        if json_path and os.path.exists(json_path):
            print(f"✅ Recommend test passed: Results exported to {json_path}")
            
            # Verify JSON content
            with open(json_path, 'r') as f:
                data = json.load(f)
            
            print(f"✅ JSON verification passed: {len(data)} item associations exported")
            return True
        else:
            print("❌ Recommend test failed: No output file created")
            return False
            
    except Exception as e:
        print(f"❌ Recommend test failed: {str(e)}")
        return False

def test_database_queries():
    """Test database queries to verify data integrity."""
    print("🧪 Testing database queries...")
    try:
        from sqlalchemy import create_engine, text
        
        engine = create_engine("postgresql://airflow:airflow@localhost:5433/airflow")
        
        with engine.connect() as conn:
            # Test orders table
            result = conn.execute(text("SELECT COUNT(*) FROM orders"))
            orders_count = result.fetchone()[0]
            print(f"✅ Orders table: {orders_count} records")
            
            # Test items table
            result = conn.execute(text("SELECT COUNT(*) FROM items"))
            items_count = result.fetchone()[0]
            print(f"✅ Items table: {items_count} records")
            
            # Test order_items table
            result = conn.execute(text("SELECT COUNT(*) FROM order_items"))
            order_items_count = result.fetchone()[0]
            print(f"✅ Order_items table: {order_items_count} records")
            
            # Test related_items table
            result = conn.execute(text("SELECT COUNT(*) FROM related_items"))
            related_items_count = result.fetchone()[0]
            print(f"✅ Related_items table: {related_items_count} records")
            
            # Test sample recommendation query
            result = conn.execute(text("""
                SELECT base_sku, related_sku, confidence 
                FROM related_items 
                ORDER BY confidence DESC 
                LIMIT 3
            """))
            
            recommendations = result.fetchall()
            print("✅ Sample recommendations:")
            for rec in recommendations:
                print(f"   {rec[0]} -> {rec[1]} (confidence: {rec[2]})")
        
        engine.dispose()
        return True
        
    except Exception as e:
        print(f"❌ Database query test failed: {str(e)}")
        return False

def main():
    """Run all tests."""
    print("🚀 Starting Related Items Pipeline Tests\n")
    
    # Test 1: Extract
    orders_data = test_extract()
    if not orders_data:
        print("\n❌ Pipeline test failed at extract stage")
        return False
    
    print()
    
    # Test 2: Load
    if not test_load(orders_data):
        print("\n❌ Pipeline test failed at load stage")
        return False
    
    print()
    
    # Test 3: Transform
    confidence_scores = test_transform()
    if not confidence_scores:
        print("\n❌ Pipeline test failed at transform stage")
        return False
    
    print()
    
    # Test 4: Recommend
    if not test_recommend(confidence_scores):
        print("\n❌ Pipeline test failed at recommend stage")
        return False
    
    print()
    
    # Test 5: Database Queries
    if not test_database_queries():
        print("\n❌ Pipeline test failed at database query stage")
        return False
    
    print("\n🎉 All tests passed! The pipeline is working correctly.")
    print("\n📊 Pipeline Summary:")
    print(f"   - Orders processed: {len(orders_data)}")
    print(f"   - Items analyzed: {len(confidence_scores)}")
    print(f"   - Associations generated: {sum(len(related) for related in confidence_scores.values())}")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
