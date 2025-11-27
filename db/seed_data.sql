-- Channels
INSERT INTO channels_raw (channel_id, channel_name, platform, commission_rate) VALUES
('CH001', 'Official Store', 'Shopify', 0.02),
('CH002', 'Amazon US', 'Amazon', 0.15),
('CH003', 'Etsy Shop', 'Etsy', 0.05);

-- Inventory Snapshots (Sample for last month)
INSERT INTO inventory_snapshots_raw (sku, warehouse_id, quantity_on_hand, snapshot_date) VALUES
('SKU001', 'WH01', 100, '2023-10-01'),
('SKU001', 'WH01', 95, '2023-10-02'),
('SKU002', 'WH01', 50, '2023-10-01'),
('SKU002', 'WH02', 200, '2023-10-01');

-- Orders
INSERT INTO orders_raw (order_id, customer_id, order_date, channel_id, total_amount, status) VALUES
('ORD001', 'CUST001', '2023-10-01 10:00:00', 'CH001', 150.00, 'COMPLETED'),
('ORD002', 'CUST002', '2023-10-01 11:30:00', 'CH002', 45.50, 'SHIPPED'),
('ORD003', 'CUST003', '2023-10-02 09:15:00', 'CH001', 300.00, 'PENDING');

-- Order Items
INSERT INTO order_items_raw (order_id, sku, quantity, unit_price) VALUES
('ORD001', 'SKU001', 2, 50.00),
('ORD001', 'SKU002', 1, 50.00),
('ORD002', 'SKU001', 1, 45.50),
('ORD003', 'SKU002', 6, 50.00);

-- Customers
INSERT INTO customers (customer_id, first_name, last_name, email, address, city, state, zip_code, signup_date) VALUES
('CUST001', 'John', 'Doe', 'john@example.com', '123 Main St', 'New York', 'NY', '10001', '2023-01-15'),
('CUST002', 'Jane', 'Smith', 'jane@example.com', '456 Oak Ave', 'Los Angeles', 'CA', '90001', '2023-02-20'),
('CUST003', 'Bob', 'Johnson', 'bob@example.com', '789 Pine Rd', 'Chicago', 'IL', '60601', '2023-03-10');

-- Transactions
INSERT INTO transactions (transaction_id, order_id, payment_method, amount, transaction_date, status) VALUES
('TXN001', 'ORD001', 'Credit Card', 150.00, '2023-10-01 10:05:00', 'SUCCESS'),
('TXN002', 'ORD002', 'PayPal', 45.50, '2023-10-01 11:35:00', 'SUCCESS'),
('TXN003', 'ORD003', 'Credit Card', 300.00, '2023-10-02 09:20:00', 'PENDING');
