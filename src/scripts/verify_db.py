import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from src.db_client import DBClient

db = DBClient()
try:
    customers = db.read_table('customers')
    transactions = db.read_table('transactions')
    orders = db.read_table('orders_raw')
    print(f"Customers: {len(customers)}")
    print(f"Transactions: {len(transactions)}")
    print(f"Orders: {len(orders)}")
except Exception as e:
    print(f"Error: {e}")
