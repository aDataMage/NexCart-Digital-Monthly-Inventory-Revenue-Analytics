"""
Simple pandas-based ETL to clean raw data and populate clean tables.
This avoids the Spark Python version mismatch issue.
"""
import pandas as pd
import sqlite3
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = "inventory_v2.db"


def clean_and_load():
    """Clean raw data and load into clean tables."""
    conn = sqlite3.connect(DB_PATH)
    
    logger.info("Starting ETL process...")
    
    # 1. Clean Orders
    logger.info("Cleaning orders...")
    orders_raw = pd.read_sql("SELECT * FROM orders_raw", conn)
    
    orders_clean = orders_raw.copy()
    orders_clean['order_date'] = pd.to_datetime(orders_clean['order_date']).dt.strftime('%Y-%m-%d')
    orders_clean = orders_clean.drop_duplicates(subset=['order_id'])
    orders_clean = orders_clean.dropna(subset=['order_id', 'order_date'])
    
    # Write to clean table (replace existing)
    orders_clean.to_sql('orders_clean', conn, if_exists='replace', index=False)
    logger.info(f"  ✓ Cleaned {len(orders_clean)} orders")
    
    # 2. Clean Inventory
    logger.info("Cleaning inventory...")
    inventory_raw = pd.read_sql("SELECT * FROM inventory_snapshots_raw", conn)
    
    inventory_clean = inventory_raw.copy()
    inventory_clean['snapshot_date'] = pd.to_datetime(inventory_clean['snapshot_date']).dt.strftime('%Y-%m-%d')
    inventory_clean = inventory_clean.drop_duplicates(subset=['sku', 'warehouse_id', 'snapshot_date'])
    inventory_clean = inventory_clean.dropna(subset=['sku', 'warehouse_id', 'snapshot_date'])
    
    # Rename to match schema
    inventory_clean = inventory_clean[['sku', 'warehouse_id', 'snapshot_date', 'quantity_on_hand']]
    
    # Write to clean table
    inventory_clean.to_sql('inventory_clean', conn, if_exists='replace', index=False)
    logger.info(f"  ✓ Cleaned {len(inventory_clean)} inventory snapshots")
    
    # 3. Clean Customers
    logger.info("Cleaning customers...")
    customers_raw = pd.read_sql("SELECT * FROM customers", conn)
    
    customers_clean = customers_raw.copy()
    customers_clean = customers_clean.drop_duplicates(subset=['customer_id'])
    customers_clean = customers_clean.dropna(subset=['customer_id'])
    
    # Keep only needed columns
    customers_clean = customers_clean[['customer_id', 'first_name', 'last_name', 'email', 'city', 'state']]
    
    # Write to clean table
    customers_clean.to_sql('customers_clean', conn, if_exists='replace', index=False)
    logger.info(f"  ✓ Cleaned {len(customers_clean)} customers")
    
    # 4. Clean Transactions
    logger.info("Cleaning transactions...")
    transactions_raw = pd.read_sql("SELECT * FROM transactions", conn)
    
    transactions_clean = transactions_raw.copy()
    transactions_clean['transaction_date'] = pd.to_datetime(transactions_clean['transaction_date']).dt.strftime('%Y-%m-%d')
    transactions_clean = transactions_clean.drop_duplicates(subset=['transaction_id'])
    transactions_clean = transactions_clean.dropna(subset=['transaction_id'])
    
    # Write to clean table
    transactions_clean.to_sql('transactions_clean', conn, if_exists='replace', index=False)
    logger.info(f"  ✓ Cleaned {len(transactions_clean)} transactions")
    
    conn.close()
    
    logger.info("✅ ETL complete!")
    logger.info(f"Clean tables populated in {DB_PATH}")


if __name__ == "__main__":
    clean_and_load()
