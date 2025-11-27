-- Raw Tables
CREATE TABLE IF NOT EXISTS channels_raw (
    channel_id TEXT PRIMARY KEY,
    channel_name TEXT NOT NULL,
    platform TEXT,
    commission_rate REAL
);

CREATE TABLE IF NOT EXISTS inventory_snapshots_raw (
    snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku TEXT NOT NULL,
    warehouse_id TEXT NOT NULL,
    quantity_on_hand INTEGER,
    snapshot_date TEXT NOT NULL -- ISO8601 YYYY-MM-DD
);

CREATE TABLE IF NOT EXISTS orders_raw (
    order_id TEXT PRIMARY KEY,
    customer_id TEXT,
    order_date TEXT NOT NULL, -- ISO8601 YYYY-MM-DD HH:MM:SS
    channel_id TEXT,
    total_amount REAL,
    status TEXT,
    FOREIGN KEY(channel_id) REFERENCES channels_raw(channel_id)
);

CREATE TABLE IF NOT EXISTS order_items_raw (
    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT,
    sku TEXT,
    quantity INTEGER,
    unit_price REAL,
    FOREIGN KEY(order_id) REFERENCES orders_raw(order_id)
);

CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,
    first_name TEXT,
    last_name TEXT,
    email TEXT,
    address TEXT,
    city TEXT,
    state TEXT,
    zip_code TEXT,
    signup_date TEXT
);

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id TEXT PRIMARY KEY,
    order_id TEXT,
    payment_method TEXT,
    amount REAL,
    transaction_date TEXT,
    status TEXT,
    FOREIGN KEY(order_id) REFERENCES orders_raw(order_id)
);

-- Cleaned Tables
CREATE TABLE IF NOT EXISTS orders_clean (
    order_id TEXT PRIMARY KEY,
    customer_id TEXT,
    order_date DATE,
    channel_id TEXT,
    total_amount REAL,
    status TEXT,
    processing_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS inventory_clean (
    sku TEXT,
    warehouse_id TEXT,
    snapshot_date DATE,
    quantity_on_hand INTEGER,
    processing_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (sku, warehouse_id, snapshot_date)
);

CREATE TABLE IF NOT EXISTS customers_clean (
    customer_id TEXT PRIMARY KEY,
    first_name TEXT,
    last_name TEXT,
    email TEXT,
    city TEXT,
    state TEXT,
    processing_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS transactions_clean (
    transaction_id TEXT PRIMARY KEY,
    order_id TEXT,
    payment_method TEXT,
    amount REAL,
    transaction_date DATE,
    status TEXT,
    processing_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- KPI Tables
CREATE TABLE IF NOT EXISTS channel_kpis (
    channel_id TEXT,
    month_start_date DATE,
    total_revenue REAL,
    order_count INTEGER,
    avg_order_value REAL,
    processing_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (channel_id, month_start_date)
);
