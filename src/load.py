#!/usr/bin/env python3
"""
Load script for Shopify orders data pipeline.
Inserts extracted data into PostgreSQL database.
"""

import logging
from typing import Dict, List, Any
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseLoader:
    """Handles loading of orders data into PostgreSQL database."""
    
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
        self.Session = sessionmaker(bind=self.engine)
        
        # Test connection
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection established successfully")
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            raise
    
    def create_tables_if_not_exist(self):
        """Create database tables if they don't exist."""
        try:
            # Check if tables exist
            inspector = inspect(self.engine)
            existing_tables = inspector.get_table_names()
            
            required_tables = ['orders', 'items', 'order_items', 'related_items']
            
            if not all(table in existing_tables for table in required_tables):
                logger.info("Creating database tables...")
                
                # Read and execute init.sql
                init_sql_path = os.path.join(
                    os.path.dirname(__file__), '..', 'db', 'init.sql'
                )
                
                with open(init_sql_path, 'r') as f:
                    init_sql = f.read()
                
                with self.engine.connect() as conn:
                    # Split SQL by semicolon and execute each statement
                    statements = [stmt.strip() for stmt in init_sql.split(';') if stmt.strip()]
                    for statement in statements:
                        if statement:
                            conn.execute(text(statement))
                    conn.commit()
                
                logger.info("Database tables created successfully")
            else:
                logger.info("Database tables already exist")
                
        except Exception as e:
            logger.error(f"Error creating tables: {str(e)}")
            raise
    
    def load_orders_data(self, orders_data: Dict[str, List[Dict[str, Any]]]):
        """
        Load orders data into the database.
        
        Args:
            orders_data: Dictionary with order_number as key and list of items as value
        """
        try:
            logger.info("Starting to load orders data into database...")
            
            session = self.Session()
            
            # Track statistics
            orders_created = 0
            items_created = 0
            order_items_created = 0
            
            for order_number, items in orders_data.items():
                try:
                    # Insert order
                    order_result = session.execute(
                        text("""
                            INSERT INTO orders (order_number) 
                            VALUES (:order_number) 
                            ON CONFLICT (order_number) DO NOTHING 
                            RETURNING id
                        """),
                        {"order_number": order_number}
                    )
                    
                    order_row = order_result.fetchone()
                    if order_row:
                        order_id = order_row[0]
                        orders_created += 1
                    else:
                        # Order already exists, get its ID
                        order_result = session.execute(
                            text("SELECT id FROM orders WHERE order_number = :order_number"),
                            {"order_number": order_number}
                        )
                        order_id = order_result.fetchone()[0]
                    
                    # Process items for this order
                    for item in items:
                        # Insert item
                        item_result = session.execute(
                            text("""
                                INSERT INTO items (sku, name) 
                                VALUES (:sku, :name) 
                                ON CONFLICT (sku) DO NOTHING 
                                RETURNING id
                            """),
                            {"sku": item['sku'], "name": item['name']}
                        )
                        
                        item_row = item_result.fetchone()
                        if item_row:
                            item_id = item_row[0]
                            items_created += 1
                        else:
                            # Item already exists, get its ID
                            item_result = session.execute(
                                text("SELECT id FROM items WHERE sku = :sku"),
                                {"sku": item['sku']}
                            )
                            item_id = item_result.fetchone()[0]
                        
                        # Insert order_item
                        session.execute(
                            text("""
                                INSERT INTO order_items (order_id, item_id, quantity) 
                                VALUES (:order_id, :item_id, :quantity) 
                                ON CONFLICT (order_id, item_id) DO UPDATE 
                                SET quantity = :quantity
                            """),
                            {
                                "order_id": order_id,
                                "item_id": item_id,
                                "quantity": item['quantity']
                            }
                        )
                        order_items_created += 1
                
                except IntegrityError as e:
                    logger.warning(f"Integrity error for order {order_number}: {str(e)}")
                    session.rollback()
                    continue
                except Exception as e:
                    logger.error(f"Error processing order {order_number}: {str(e)}")
                    session.rollback()
                    continue
            
            # Commit all changes
            session.commit()
            session.close()
            
            logger.info(f"Data loading completed successfully:")
            logger.info(f"  - Orders created: {orders_created}")
            logger.info(f"  - Items created: {items_created}")
            logger.info(f"  - Order items created: {order_items_created}")
            
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            if 'session' in locals():
                session.rollback()
                session.close()
            raise
    
    def close(self):
        """Close database connection."""
        self.engine.dispose()
        logger.info("Database connection closed")


def main():
    """Main function for standalone execution."""
    from extract import extract_orders_from_csv
    import os
    
    try:
        # Extract data
        csv_path = os.path.join(
            os.path.dirname(__file__), '..', 'data', 'orders.csv'
        )
        orders_data = extract_orders_from_csv(csv_path)
        
        if not orders_data:
            logger.error("No data to load")
            return
        
        # Load data into database
        loader = DatabaseLoader()
        loader.create_tables_if_not_exist()
        loader.load_orders_data(orders_data)
        loader.close()
        
        logger.info("Data loading completed successfully")
        
    except Exception as e:
        logger.error(f"Data loading failed: {str(e)}")


if __name__ == "__main__":
    main()
