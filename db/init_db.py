import sqlite3
import os
from pathlib import Path

DB_FILE = "inventory_v2.db"
SCHEMA_FILE = "db/schema.sql"
SEED_FILE = "db/seed_data.sql"

def init_db():
    print(f"Initializing database: {DB_FILE}")
    
    # Remove existing DB if needed (optional, for clean slate)
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        print("Removed existing database.")

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Read and execute schema
    print(f"Applying schema from {SCHEMA_FILE}...")
    with open(SCHEMA_FILE, 'r') as f:
        schema_sql = f.read()
        cursor.executescript(schema_sql)

    # Read and execute seed data
    print(f"Seeding data from {SEED_FILE}...")
    with open(SEED_FILE, 'r') as f:
        seed_sql = f.read()
        cursor.executescript(seed_sql)

    conn.commit()
    conn.close()
    print("Database initialization complete.")

if __name__ == "__main__":
    init_db()
