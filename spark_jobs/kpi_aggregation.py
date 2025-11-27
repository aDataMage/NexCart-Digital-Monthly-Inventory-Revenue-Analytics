from pyspark.sql import SparkSession
from pyspark.sql.functions import sum, count, avg, col, lit, current_timestamp, to_date
from src.db_client import DBClient
import logging
import sys
import os

# Ensure project root is in path
sys.path.append(os.getcwd())

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_kpi_aggregation():
    spark = SparkSession.builder \
        .appName("KPIAggregation") \
        .getOrCreate()

    db_client = DBClient()

    try:
        # 1. Load Cleaned Data
        logger.info("Loading cleaned data...")
        orders_pdf = db_client.read_table("orders_clean")
        transactions_pdf = db_client.read_table("transactions_clean")
        
        orders_clean = spark.createDataFrame(orders_pdf)
        transactions_clean = spark.createDataFrame(transactions_pdf)

        # 2. Aggregate KPIs
        logger.info("Aggregating KPIs...")
        
        # Channel KPIs
        channel_kpis = orders_clean.groupBy("channel_id") \
            .agg(
                sum("total_amount").alias("total_revenue"),
                count("order_id").alias("order_count"),
                avg("total_amount").alias("avg_order_value")
            ) \
            .withColumn("month_start_date", to_date(lit("2023-10-01"))) \
            .withColumn("processing_timestamp", current_timestamp())

        # Customer KPIs (Calculated but not stored in DB for now, just logged)
        customer_revenue = orders_clean.groupBy("customer_id") \
            .agg(sum("total_amount").alias("total_spent"), count("order_id").alias("order_count"))
        
        logger.info("Top 5 Customers:")
        customer_revenue.orderBy(col("total_spent").desc()).limit(5).show()

        # Transaction KPIs (Payment Method Stats)
        payment_stats = transactions_clean.groupBy("payment_method") \
            .agg(count("transaction_id").alias("txn_count"), sum("amount").alias("total_amount"))
        
        logger.info("Payment Method Stats:")
        payment_stats.show()

        # 3. Load KPIs
        logger.info("Loading KPIs...")
        channel_kpis_pdf = channel_kpis.toPandas()
        
        db_client.write_table(channel_kpis_pdf, "channel_kpis", if_exists="replace")

        logger.info("KPI Aggregation Completed Successfully")

    except Exception as e:
        logger.error(f"KPI Job Failed: {e}")
        raise
    finally:
        spark.stop()

if __name__ == "__main__":
    run_kpi_aggregation()
