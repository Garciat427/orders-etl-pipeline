#!/usr/bin/env python3
"""
Reset Database Script
Drops all tables and recreates them fresh to ensure clean data loading.
"""

import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

def get_connection_string():
    """Get the appropriate connection string based on environment."""
    if os.environ.get('AIRFLOW_HOME'):
        # Running in Airflow/Docker
        return "postgresql://airflow:airflow@postgres:5432/airflow"
    else:
        # Running locally
        return "postgresql://airflow:airflow@localhost:5433/airflow"

def reset_database():
    """Drop all tables and recreate them fresh."""
    connection_string = get_connection_string()
    print(f"🔗 Connecting to: {connection_string}")
    
    try:
        engine = create_engine(connection_string)
        
        with engine.begin() as conn:
            print("🗑️  Dropping all tables...")
            
            # Drop tables in reverse dependency order
            drop_queries = [
                "DROP TABLE IF EXISTS related_items CASCADE;",
                "DROP TABLE IF EXISTS order_items CASCADE;", 
                "DROP TABLE IF EXISTS items CASCADE;",
                "DROP TABLE IF EXISTS orders CASCADE;"
            ]
            
            for query in drop_queries:
                print(f"   Executing: {query}")
                conn.execute(text(query))
            
            print("✅ All tables dropped successfully!")
            
            print("🏗️  Recreating tables...")
            
            # Read and execute the init.sql file
            init_sql_path = Path(__file__).parent / "db" / "init.sql"
            if init_sql_path.exists():
                with open(init_sql_path, 'r') as f:
                    init_sql = f.read()
                
                # Execute the entire SQL file as one statement
                print("   Executing init.sql...")
                conn.execute(text(init_sql))
                
                print("✅ Tables recreated successfully!")
            else:
                print("❌ init.sql file not found!")
                return False
                
        print("🎉 Database reset complete!")
        return True
        
    except SQLAlchemyError as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting database reset...")
    success = reset_database()
    
    if success:
        print("\n✅ Database reset successful!")
        print("📊 You can now run the pipeline with fresh tables.")
    else:
        print("\n❌ Database reset failed!")
        sys.exit(1)
