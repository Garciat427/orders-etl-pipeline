#!/usr/bin/env python3
"""
Extract script for Shopify orders data pipeline.
Reads CSV file and groups items by order number.
"""

import pandas as pd
import logging
from typing import Dict, List, Any
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_orders_from_csv(csv_path: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Extract orders data from Shopify CSV export and group by order number.
    Filters out unfulfilled orders based on fulfillment status.
    
    Args:
        csv_path: Path to the CSV file
        
    Returns:
        Dictionary with order_number as key and list of items as value
    """
    try:
        logger.info(f"Reading CSV file from: {csv_path}")
        
        # Read CSV file
        df = pd.read_csv(csv_path)
        
        # Clean column names (remove spaces and special characters)
        df.columns = df.columns.str.strip().str.replace(' ', '_').str.replace('-', '_')
        
        logger.info(f"CSV loaded successfully. Shape: {df.shape}")
        logger.info(f"Columns: {list(df.columns)}")
        
        # Filter orders based on fulfillment status
        logger.info("Filtering orders based on fulfillment status...")
        
        # Group by order number and check fulfillment status
        order_status = {}
        for _, row in df.iterrows():
            order_name = row['Name']
            fulfillment_status = str(row['Fulfillment_Status']).strip().lower()
            
            if order_name not in order_status:
                order_status[order_name] = {'has_fulfilled': False, 'items': []}
            
            # If any item in the order is fulfilled, mark the order as fulfilled
            if fulfillment_status == 'fulfilled':
                order_status[order_name]['has_fulfilled'] = True
            
            # Store item details (skip items with NaN or empty SKUs)
            sku = row['Lineitem_sku']
            if pd.isna(sku) or str(sku).strip() == '' or str(sku).lower() == 'nan':
                logger.debug(f"Skipping item with invalid SKU: {sku}")
                continue
                
            order_status[order_name]['items'].append({
                'sku': str(sku).strip(),
                'name': str(row['Lineitem_name']).strip() if not pd.isna(row['Lineitem_name']) else 'Unknown',
                'quantity': int(row['Lineitem_quantity']) if not pd.isna(row['Lineitem_quantity']) else 1
            })
        
        # Filter to keep only orders with at least one fulfilled item
        filtered_orders = {}
        removed_orders = 0
        
        for order_name, order_data in order_status.items():
            if order_data['has_fulfilled'] and len(order_data['items']) > 0:
                # Keep fulfilled orders that have valid items
                filtered_orders[order_name] = order_data['items']
            else:
                # Remove unfulfilled orders or orders with no valid items
                removed_orders += 1
                if not order_data['has_fulfilled']:
                    logger.debug(f"Removing unfulfilled order: {order_name}")
                else:
                    logger.debug(f"Removing order with no valid items: {order_name}")
        
        logger.info(f"Filtered orders: {len(filtered_orders)} kept, {removed_orders} removed")
        
        # Group items by order number and handle duplicates
        orders_dict = {}
        
        for order_name, items in filtered_orders.items():
            orders_dict[order_name] = []
            
            for item in items:
                # Check if item already exists in this order (avoid duplicates)
                existing_item = next(
                    (existing for existing in orders_dict[order_name] if existing['sku'] == item['sku']), 
                    None
                )
                
                if existing_item:
                    existing_item['quantity'] += item['quantity']
                else:
                    orders_dict[order_name].append({
                        'sku': item['sku'],
                        'name': item['name'],
                        'quantity': item['quantity']
                    })
        
        logger.info(f"Extracted {len(orders_dict)} fulfilled orders with items")
        
        # Log some statistics
        total_items = sum(len(items) for items in orders_dict.values())
        logger.info(f"Total unique items across all orders: {total_items}")
        
        return orders_dict
        
    except FileNotFoundError:
        logger.error(f"CSV file not found: {csv_path}")
        raise
    except Exception as e:
        logger.error(f"Error extracting data: {str(e)}")
        raise


def main():
    """Main function for standalone execution."""
    # Default path to orders CSV
    csv_path = Path(__file__).parent.parent / "data" / "orders.csv"
    
    try:
        orders_data = extract_orders_from_csv(str(csv_path))
        
        # Print sample output
        logger.info("Sample extracted data:")
        for order_num, items in list(orders_data.items())[:3]:
            logger.info(f"Order {order_num}: {items}")
            
        return orders_data
        
    except Exception as e:
        logger.error(f"Extraction failed: {str(e)}")
        return None


if __name__ == "__main__":
    main()
