"""
Generate fake data for multiple months to populate the database with historical data.
This creates realistic multi-month data for testing and demonstration.
"""
from faker import Faker
import random
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import sqlite3
from pathlib import Path

fake = Faker()
random.seed(42)  # For reproducibility

# Configuration
DB_PATH = "inventory_v2.db"
MONTHS_TO_GENERATE = ["2025-07", "2025-08", "2025-09", "2025-10"]  # Jul, Aug, Sep, Oct 2025
ORDERS_PER_MONTH = 300
CUSTOMERS_BASE = 100  # Base customers, we'll add more each month

# Product SKUs
SKUS = [f"SKU-{str(i).zfill(4)}" for i in range(1, 51)]  # 50 SKUs

# Channels
CHANNELS = [
    ("CH-001", "Amazon", "Marketplace", 0.15),
    ("CH-002", "Shopify", "Direct", 0.03),
    ("CH-003", "eBay", "Marketplace", 0.12),
    ("CH-004", "Walmart", "Marketplace", 0.10)
]

# Warehouses
WAREHOUSES = ["WH-EAST", "WH-WEST", "WH-CENTRAL"]

# Payment methods
PAYMENT_METHODS = ["Credit Card", "Debit Card", "PayPal", "Bank Transfer"]


def create_month_date_range(month_str):
    """Create date range for a given month (YYYY-MM)."""
    start = datetime.strptime(month_str, "%Y-%m")
    next_month = start + relativedelta(months=1)
    end = next_month - timedelta(days=1)
    return start, end


def random_date_in_range(start, end):
    """Generate random datetime between start and end."""
    delta = end - start
    random_days = random.randint(0, delta.days)
    random_seconds = random.randint(0, 86400)
    return start + timedelta(days=random_days, seconds=random_seconds)


def generate_data_for_month(conn, month_str, existing_customers):
    """Generate all data for a single month."""
    print(f"\n📅 Generating data for {month_str}...")
    
    start_date, end_date = create_month_date_range(month_str)
    cursor = conn.cursor()
    
    # Add some new customers each month (20-30 new customers)
    new_customer_count = random.randint(20, 30)
    new_customers = []
    
    for i in range(new_customer_count):
        customer_id = f"CUST-{len(existing_customers) + i + 1:05d}"
        signup_date = random_date_in_range(start_date, end_date)
        
        cursor.execute("""
            INSERT OR IGNORE INTO customers (customer_id, first_name, last_name, email, address, city, state, zip_code, signup_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            customer_id,
            fake.first_name(),
            fake.last_name(),
            fake.email(),
            fake.street_address(),
            fake.city(),
            fake.state_abbr(),
            fake.zipcode(),
            signup_date.strftime("%Y-%m-%d")
        ))
        new_customers.append(customer_id)
    
    all_customers = existing_customers + new_customers
    print(f"  ✓ Added {new_customer_count} new customers (total: {len(all_customers)})")
    
    # Generate orders for the month
    orders_generated = 0
    transactions_generated = 0
    order_items_generated = 0
    
    for _ in range(ORDERS_PER_MONTH):
        order_id = f"ORD-{month_str}-{random.randint(10000, 99999)}"
        order_date = random_date_in_range(start_date, end_date)
        customer_id = random.choice(all_customers)
        channel_id = random.choice([ch[0] for ch in CHANNELS])
        status = random.choices(
            ["COMPLETED", "SHIPPED", "PENDING", "CANCELLED"],
            weights=[70, 20, 8, 2]
        )[0]
        
        # Generate order items
        num_items = random.randint(1, 5)
        total_amount = 0
        
        for _ in range(num_items):
            sku = random.choice(SKUS)
            quantity = random.randint(1, 10)
            unit_price = round(random.uniform(10, 200), 2)
            total_amount += quantity * unit_price
            
            cursor.execute("""
                INSERT INTO order_items_raw (order_id, sku, quantity, unit_price)
                VALUES (?, ?, ?, ?)
            """, (order_id, sku, quantity, unit_price))
            order_items_generated += 1
        
        total_amount = round(total_amount, 2)
        
        # Insert order
        cursor.execute("""
            INSERT INTO orders_raw (order_id, customer_id, order_date, channel_id, total_amount, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (order_id, customer_id, order_date.strftime("%Y-%m-%d %H:%M:%S"), channel_id, total_amount, status))
        orders_generated += 1
        
        # Generate transaction if order is not cancelled
        if status != "CANCELLED":
            transaction_id = f"TXN-{order_id}"
            payment_method = random.choice(PAYMENT_METHODS)
            transaction_date = order_date + timedelta(hours=random.randint(0, 48))
            txn_status = random.choices(
                ["SUCCESS", "PENDING", "FAILED"],
                weights=[85, 10, 5]
            )[0]
            
            cursor.execute("""
                INSERT INTO transactions (transaction_id, order_id, payment_method, amount, transaction_date, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (transaction_id, order_id, payment_method, total_amount, transaction_date.strftime("%Y-%m-%d %H:%M:%S"), txn_status))
            transactions_generated += 1
    
    print(f"  ✓ Generated {orders_generated} orders")
    print(f"  ✓ Generated {order_items_generated} order items")
    print(f"  ✓ Generated {transactions_generated} transactions")
    
    # Generate inventory snapshots (3 snapshots per month: start, mid, end)
    snapshot_dates = [
        start_date,
        start_date + timedelta(days=15),
        end_date
    ]
    
    snapshots_generated = 0
    for snapshot_date in snapshot_dates:
        for sku in SKUS:
            for warehouse in WAREHOUSES:
                quantity = random.randint(0, 100)
                
                cursor.execute("""
                    INSERT INTO inventory_snapshots_raw (sku, warehouse_id, quantity_on_hand, snapshot_date)
                    VALUES (?, ?, ?, ?)
                """, (sku, warehouse, quantity, snapshot_date.strftime("%Y-%m-%d")))
                snapshots_generated += 1
    
    print(f"  ✓ Generated {snapshots_generated} inventory snapshots")
    
    conn.commit()
    return all_customers


def main():
    """Generate multi-month data."""
    print("🚀 Multi-Month Data Generator")
    print("=" * 50)
    
    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Insert channels (one time)
    print("\n📦 Setting up channels...")
    for channel in CHANNELS:
        cursor.execute("""
            INSERT OR IGNORE INTO channels_raw (channel_id, channel_name, platform, commission_rate)
            VALUES (?, ?, ?, ?)
        """, channel)
    conn.commit()
    print(f"  ✓ Configured {len(CHANNELS)} sales channels")
    
    # Generate base customers
    print("\n👥 Creating base customer set...")
    customers = []
    for i in range(CUSTOMERS_BASE):
        customer_id = f"CUST-{i+1:05d}"
        # Signup dates before our first month
        signup_date = datetime(2025, 6, random.randint(1, 30))
        
        cursor.execute("""
            INSERT OR IGNORE INTO customers (customer_id, first_name, last_name, email, address, city, state, zip_code, signup_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            customer_id,
            fake.first_name(),
            fake.last_name(),
            fake.email(),
            fake.street_address(),
            fake.city(),
            fake.state_abbr(),
            fake.zipcode(),
            signup_date.strftime("%Y-%m-%d")
        ))
        customers.append(customer_id)
    
    conn.commit()
    print(f"  ✓ Created {CUSTOMERS_BASE} base customers")
    
    # Generate data for each month
    for month in MONTHS_TO_GENERATE:
        customers = generate_data_for_month(conn, month, customers)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Generation Complete!")
    print("=" * 50)
    
    cursor.execute("SELECT COUNT(*) FROM customers")
    print(f"Total Customers: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM orders_raw")
    print(f"Total Orders: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM order_items_raw")
    print(f"Total Order Items: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM transactions")
    print(f"Total Transactions: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM inventory_snapshots_raw")
    print(f"Total Inventory Snapshots: {cursor.fetchone()[0]}")
    
    print("\n✅ Database populated with multi-month data!")
    print(f"📁 Database: {DB_PATH}")
    
    conn.close()


if __name__ == "__main__":
    main()
