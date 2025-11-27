"""
SQL-based report query functions for analytical reporting.
Each function executes SQL queries and returns DataFrames for visualization.
"""
import pandas as pd
from datetime import datetime
from src.db_client import DBClient
import logging

logger = logging.getLogger(__name__)


def get_sales_channel_performance(db_client: DBClient, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Analyzes sales and channel performance including gross revenue, net revenue, and order volume.
    
    Args:
        db_client: Database client instance
        start_date: Start date for analysis (YYYY-MM-DD)
        end_date: End date for analysis (YYYY-MM-DD)
    
    Returns:
        DataFrame with columns: channel_id, channel_name, commission_rate, 
                                gross_revenue, net_revenue, order_count, avg_order_value
    """
    query = f"""
    SELECT 
        c.channel_id,
        c.channel_name,
        c.commission_rate,
        SUM(o.total_amount) as gross_revenue,
        SUM(o.total_amount * (1 - c.commission_rate)) as net_revenue,
        COUNT(o.order_id) as order_count,
        AVG(o.total_amount) as avg_order_value
    FROM orders_clean o
    JOIN channels_raw c ON o.channel_id = c.channel_id
    WHERE o.order_date BETWEEN '{start_date}' AND '{end_date}'
    GROUP BY c.channel_id, c.channel_name, c.commission_rate
    ORDER BY gross_revenue DESC
    """
    
    logger.info(f"Executing Sales & Channel Performance query for {start_date} to {end_date}")
    return db_client.execute_query(query)


def get_product_performance(db_client: DBClient, start_date: str, end_date: str) -> dict:
    """
    Analyzes product performance including top sellers, revenue drivers, and AOV.
    
    Returns:
        Dictionary with:
        - 'top_skus': Top selling SKUs by quantity
        - 'revenue_drivers': SKUs by revenue contribution
        - 'aov': Overall average order value
    """
    # Top SKUs by quantity
    top_skus_query = f"""
    SELECT 
        oi.sku,
        SUM(oi.quantity) as total_quantity_sold,
        SUM(oi.quantity * oi.unit_price) as total_revenue,
        AVG(oi.unit_price) as avg_unit_price
    FROM order_items_raw oi
    JOIN orders_clean o ON oi.order_id = o.order_id
    WHERE o.order_date BETWEEN '{start_date}' AND '{end_date}'
    GROUP BY oi.sku
    ORDER BY total_quantity_sold DESC
    LIMIT 20
    """
    
    # Revenue drivers
    revenue_drivers_query = f"""
    SELECT 
        oi.sku,
        SUM(oi.quantity * oi.unit_price) as total_revenue,
        SUM(oi.quantity) as total_quantity_sold,
        COUNT(DISTINCT oi.order_id) as order_count
    FROM order_items_raw oi
    JOIN orders_clean o ON oi.order_id = o.order_id
    WHERE o.order_date BETWEEN '{start_date}' AND '{end_date}'
    GROUP BY oi.sku
    ORDER BY total_revenue DESC
    LIMIT 20
    """
    
    # AOV
    aov_query = f"""
    SELECT 
        SUM(total_amount) / COUNT(order_id) as avg_order_value,
        SUM(total_amount) as total_revenue,
        COUNT(order_id) as total_orders
    FROM orders_clean
    WHERE order_date BETWEEN '{start_date}' AND '{end_date}'
    """
    
    logger.info(f"Executing Product Performance queries for {start_date} to {end_date}")
    
    return {
        'top_skus': db_client.execute_query(top_skus_query),
        'revenue_drivers': db_client.execute_query(revenue_drivers_query),
        'aov': db_client.execute_query(aov_query)
    }


def get_inventory_health(db_client: DBClient, snapshot_date: str = None) -> dict:
    """
    Analyzes inventory health including warehouse distribution, low stock alerts, and value.
    
    Args:
        snapshot_date: Specific snapshot date, defaults to most recent
    
    Returns:
        Dictionary with:
        - 'warehouse_distribution': Stock distribution by warehouse
        - 'low_stock_alerts': SKUs below threshold
        - 'inventory_value': Total inventory value by warehouse
    """
    # Get latest snapshot date if not provided
    if not snapshot_date:
        latest_date_query = "SELECT MAX(snapshot_date) as latest_date FROM inventory_clean"
        snapshot_date = db_client.execute_query(latest_date_query).iloc[0]['latest_date']
    
    # Warehouse distribution
    warehouse_dist_query = f"""
    SELECT 
        warehouse_id,
        COUNT(DISTINCT sku) as unique_skus,
        SUM(quantity_on_hand) as total_units
    FROM inventory_clean
    WHERE snapshot_date = '{snapshot_date}'
    GROUP BY warehouse_id
    ORDER BY total_units DESC
    """
    
    # Low stock alerts
    low_stock_query = f"""
    SELECT 
        i.sku,
        i.warehouse_id,
        i.quantity_on_hand,
        AVG(oi.unit_price) as avg_price
    FROM inventory_clean i
    LEFT JOIN order_items_raw oi ON i.sku = oi.sku
    WHERE i.snapshot_date = '{snapshot_date}'
        AND i.quantity_on_hand < 10
    GROUP BY i.sku, i.warehouse_id, i.quantity_on_hand
    ORDER BY i.quantity_on_hand ASC
    """
    
    # Inventory value
    inventory_value_query = f"""
    SELECT 
        i.warehouse_id,
        SUM(i.quantity_on_hand * COALESCE(oi.avg_price, 0)) as inventory_value,
        COUNT(DISTINCT i.sku) as sku_count
    FROM inventory_clean i
    LEFT JOIN (
        SELECT sku, AVG(unit_price) as avg_price
        FROM order_items_raw
        GROUP BY sku
    ) oi ON i.sku = oi.sku
    WHERE i.snapshot_date = '{snapshot_date}'
    GROUP BY i.warehouse_id
    ORDER BY inventory_value DESC
    """
    
    logger.info(f"Executing Inventory Health queries for {snapshot_date}")
    
    return {
        'warehouse_distribution': db_client.execute_query(warehouse_dist_query),
        'low_stock_alerts': db_client.execute_query(low_stock_query),
        'inventory_value': db_client.execute_query(inventory_value_query),
        'snapshot_date': snapshot_date
    }


def get_customer_demographics(db_client: DBClient, start_date: str, end_date: str) -> dict:
    """
    Analyzes customer demographics and behavior including geography, acquisition, and latency.
    
    Returns:
        Dictionary with:
        - 'geographic_distribution': Sales by state/city
        - 'new_customers': Customer acquisition trends over time
        - 'purchase_latency': Time between signup and first purchase
    """
    # Geographic distribution
    geo_query = f"""
    SELECT 
        c.state,
        c.city,
        COUNT(DISTINCT o.customer_id) as customer_count,
        SUM(o.total_amount) as total_sales,
        COUNT(o.order_id) as order_count
    FROM orders_clean o
    JOIN customers c ON o.customer_id = c.customer_id
    WHERE o.order_date BETWEEN '{start_date}' AND '{end_date}'
    GROUP BY c.state, c.city
    ORDER BY total_sales DESC
    LIMIT 50
    """
    
    # New customer acquisition (by signup month)
    acquisition_query = f"""
    SELECT 
        strftime('%Y-%m', signup_date) as signup_month,
        COUNT(customer_id) as new_customers
    FROM customers
    WHERE signup_date BETWEEN '{start_date}' AND '{end_date}'
    GROUP BY signup_month
    ORDER BY signup_month
    """
    
    # Purchase latency
    latency_query = f"""
    SELECT 
        c.customer_id,
        c.signup_date,
        MIN(o.order_date) as first_order_date,
        julianday(MIN(o.order_date)) - julianday(c.signup_date) as days_to_first_purchase
    FROM customers c
    JOIN orders_clean o ON c.customer_id = o.customer_id
    WHERE o.order_date BETWEEN '{start_date}' AND '{end_date}'
    GROUP BY c.customer_id, c.signup_date
    HAVING days_to_first_purchase >= 0
    ORDER BY days_to_first_purchase
    """
    
    logger.info(f"Executing Customer Demographics queries for {start_date} to {end_date}")
    
    return {
        'geographic_distribution': db_client.execute_query(geo_query),
        'new_customers': db_client.execute_query(acquisition_query),
        'purchase_latency': db_client.execute_query(latency_query)
    }


def get_payment_analysis(db_client: DBClient, start_date: str, end_date: str) -> dict:
    """
    Analyzes payment methods, unsettled orders, and cash flow.
    
    Returns:
        Dictionary with:
        - 'payment_methods': Distribution of payment methods
        - 'unsettled_orders': Orders without successful transactions
        - 'daily_cashflow': Daily transaction amounts
    """
    # Payment method distribution
    payment_methods_query = f"""
    SELECT 
        t.payment_method,
        COUNT(t.transaction_id) as transaction_count,
        SUM(t.amount) as total_amount,
        AVG(t.amount) as avg_transaction_amount
    FROM transactions_clean t
    WHERE t.transaction_date BETWEEN '{start_date}' AND '{end_date}'
        AND t.status = 'SUCCESS'
    GROUP BY t.payment_method
    ORDER BY total_amount DESC
    """
    
    # Unsettled orders
    unsettled_query = f"""
    SELECT 
        o.order_id,
        o.order_date,
        o.channel_id,
        o.total_amount,
        o.status as order_status,
        COALESCE(t.status, 'NO_TRANSACTION') as transaction_status
    FROM orders_clean o
    LEFT JOIN transactions_clean t ON o.order_id = t.order_id AND t.status = 'SUCCESS'
    WHERE o.order_date BETWEEN '{start_date}' AND '{end_date}'
        AND o.status IN ('PENDING', 'SHIPPED')
        AND t.transaction_id IS NULL
    ORDER BY o.order_date DESC
    """
    
    # Daily cash flow
    cashflow_query = f"""
    SELECT 
        transaction_date,
        SUM(amount) as daily_total,
        COUNT(transaction_id) as transaction_count,
        AVG(amount) as avg_transaction
    FROM transactions_clean
    WHERE transaction_date BETWEEN '{start_date}' AND '{end_date}'
        AND status = 'SUCCESS'
    GROUP BY transaction_date
    ORDER BY transaction_date
    """
    
    logger.info(f"Executing Payment Analysis queries for {start_date} to {end_date}")
    
    return {
        'payment_methods': db_client.execute_query(payment_methods_query),
        'unsettled_orders': db_client.execute_query(unsettled_query),
        'daily_cashflow': db_client.execute_query(cashflow_query)
    }
