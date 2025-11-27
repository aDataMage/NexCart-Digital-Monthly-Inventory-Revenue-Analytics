import sys
import os
import random
import logging
from datetime import datetime, timedelta
from faker import Faker
import pandas as pd

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from src.db_client import DBClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

fake = Faker()

def generate_data():
    db = DBClient()
    
    # Ensure tables exist (including new ones)
    with open(os.path.join(os.path.dirname(__file__), "../../db/schema.sql"), "r") as f:
        schema = f.read()
        # Split by semicolon to execute statements individually
        statements = schema.split(";")
        for stmt in statements:
            if stmt.strip():
                db.execute_query(stmt)
    
    # 1. Generate Channels
    channels = [
        {"channel_id": "CH_AMZ", "channel_name": "Amazon", "platform": "Amazon", "commission_rate": 0.15},
        {"channel_id": "CH_SHP", "channel_name": "Shopify Store", "platform": "Shopify", "commission_rate": 0.03},
        {"channel_id": "CH_RET", "channel_name": "Retail POS", "platform": "Physical", "commission_rate": 0.00},
        {"channel_id": "CH_EBY", "channel_name": "eBay", "platform": "eBay", "commission_rate": 0.10},
    ]
    df_channels = pd.DataFrame(channels)
    db.write_table(df_channels, "channels_raw", if_exists="replace")
    logger.info("Generated channels_raw")

    # 2. Generate SKUs
    skus = [f"SKU-{fake.unique.bothify(text='??###')}" for _ in range(50)]
    warehouses = ["WH_NY", "WH_CA", "WH_TX"]

    # 3. Generate Inventory Snapshots
    snapshots = []
    start_date = datetime.now() - timedelta(days=30)
    for i in range(30):
        current_date = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
        for sku in skus:
            for wh in warehouses:
                snapshots.append({
                    "sku": sku,
                    "warehouse_id": wh,
                    "quantity_on_hand": random.randint(0, 100),
                    "snapshot_date": current_date
                })
    df_snapshots = pd.DataFrame(snapshots)
    db.write_table(df_snapshots, "inventory_snapshots_raw", if_exists="replace")
    logger.info(f"Generated {len(df_snapshots)} inventory snapshots")

    # 4. Generate Customers
    customers = []
    customer_ids = []
    for _ in range(200): # Generate 200 customers
        c_id = f"CUST-{fake.unique.bothify(text='#####')}"
        customer_ids.append(c_id)
        customers.append({
            "customer_id": c_id,
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "email": fake.email(),
            "address": fake.street_address(),
            "city": fake.city(),
            "state": fake.state_abbr(),
            "zip_code": fake.zipcode(),
            "signup_date": fake.date_between(start_date="-1y", end_date="today").strftime("%Y-%m-%d")
        })
    df_customers = pd.DataFrame(customers)
    db.write_table(df_customers, "customers", if_exists="replace")
    logger.info(f"Generated {len(df_customers)} customers")

    # 5. Generate Orders and Transactions
    orders = []
    order_items = []
    transactions = []
    
    # Generate at least 300 orders
    num_orders = 350 
    
    for _ in range(num_orders):
        order_id = f"ORD-{fake.unique.bothify(text='????####')}"
        order_date = fake.date_time_between(start_date="-30d", end_date="now").strftime("%Y-%m-%d %H:%M:%S")
        channel = random.choice(channels)
        customer_id = random.choice(customer_ids)
        
        items_in_order = random.randint(1, 5)
        total_amount = 0
        
        for _ in range(items_in_order):
            sku = random.choice(skus)
            qty = random.randint(1, 3)
            price = round(random.uniform(10.0, 200.0), 2)
            total_amount += price * qty
            
            order_items.append({
                "order_id": order_id,
                "sku": sku,
                "quantity": qty,
                "unit_price": price
            })
            
        orders.append({
            "order_id": order_id,
            "customer_id": customer_id,
            "order_date": order_date,
            "channel_id": channel["channel_id"],
            "total_amount": round(total_amount, 2),
            "status": random.choice(["COMPLETED", "SHIPPED", "PENDING", "CANCELLED"])
        })

        # Generate Transaction
        if random.random() > 0.1: # 90% chance of transaction
            transactions.append({
                "transaction_id": f"TXN-{fake.unique.bothify(text='????####')}",
                "order_id": order_id,
                "payment_method": random.choice(["Credit Card", "PayPal", "Debit Card"]),
                "amount": round(total_amount, 2),
                "transaction_date": order_date,
                "status": "SUCCESS" if random.random() > 0.05 else "FAILED"
            })

    df_orders = pd.DataFrame(orders)
    df_items = pd.DataFrame(order_items)
    df_transactions = pd.DataFrame(transactions)
    
    db.write_table(df_orders, "orders_raw", if_exists="replace")
    db.write_table(df_items, "order_items_raw", if_exists="replace")
    db.write_table(df_transactions, "transactions", if_exists="replace")
    
    logger.info(f"Generated {len(df_orders)} orders, {len(df_items)} items, and {len(df_transactions)} transactions")

if __name__ == "__main__":
    generate_data()
