# Data Model

## Overview
The database simulates a retail inventory and order management system. It consists of raw tables (simulating ingestion from source systems) and cleaned tables (produced by the ETL pipeline).

## Raw Tables
These tables represent data as it might arrive from upstream systems (e.g., Shopify, WMS).

### `channels_raw`
- `channel_id` (PK): Unique identifier for the sales channel.
- `channel_name`: Display name.
- `platform`: Underlying platform (e.g., Shopify, Amazon).
- `commission_rate`: Platform fee percentage.

### `inventory_snapshots_raw`
- `snapshot_id` (PK): Auto-incrementing ID.
- `sku`: Stock Keeping Unit.
- `warehouse_id`: Warehouse identifier.
- `quantity_on_hand`: Current stock level.
- `snapshot_date`: Date of the snapshot (YYYY-MM-DD).

### `orders_raw`
- `order_id` (PK): Unique order identifier.
- `customer_id`: Customer identifier.
- `order_date`: Timestamp of the order.
- `channel_id` (FK): Source channel.
- `total_amount`: Total order value.
- `status`: Order status (e.g., COMPLETED, SHIPPED).

### `order_items_raw`
- `item_id` (PK): Unique item identifier.
- `order_id` (FK): Parent order.
- `sku`: Product SKU.
- `quantity`: Quantity ordered.
- `unit_price`: Price per unit.

## Cleaned Tables
These tables are the result of the Spark ETL process, ready for analysis and reporting.

### `orders_clean`
- Standardized order data with consistent types and formats.
- `processing_timestamp`: When the record was processed.

### `inventory_clean`
- Deduplicated and validated inventory snapshots.
- PK is composite: `(sku, warehouse_id, snapshot_date)`.

## KPI Tables
Aggregated metrics for reporting.

### `channel_kpis`
- Monthly aggregation of revenue and order counts per channel.
- `month_start_date`: The month being reported.
