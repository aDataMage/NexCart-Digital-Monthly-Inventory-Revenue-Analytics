from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import current_timestamp, to_date, col, mean, stddev, when, lit
from src.db_client import DBClient
from src.utils.validation import validate_data_quality
import logging
import sys
import os

# Ensure project root is in path
sys.path.append(os.getcwd())

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def flag_outliers(df: DataFrame, col_name: str, threshold: float = 3.0) -> DataFrame:
    """
    Flags rows where the value in `col_name` is more than `threshold` standard deviations from the mean.
    Adds a column `is_outlier_{col_name}`.
    """
    stats = df.select(mean(col(col_name)).alias('mean'), stddev(col(col_name)).alias('stddev')).collect()[0]
    mean_val = stats['mean']
    stddev_val = stats['stddev']
    
    if stddev_val is None or stddev_val == 0:
        return df.withColumn(f"is_outlier_{col_name}", lit(False))
        
    upper_bound = mean_val + (threshold * stddev_val)
    lower_bound = mean_val - (threshold * stddev_val)
    
    return df.withColumn(f"is_outlier_{col_name}", 
                         when((col(col_name) > upper_bound) | (col(col_name) < lower_bound), True)
                         .otherwise(False))

def flag_missing(df: DataFrame, cols: list[str]) -> DataFrame:
    """
    Flags rows where any of the specified columns are null.
    Adds a column `has_missing_values`.
    """
    condition = col(cols[0]).isNull()
    for c in cols[1:]:
        condition = condition | col(c).isNull()
        
    return df.withColumn("has_missing_values", when(condition, True).otherwise(False))

def run_etl():
    spark = SparkSession.builder \
        .appName("InventoryETL") \
        .config("spark.python.worker.faulthandler.enabled", "true") \
        .config("spark.driver.host", "127.0.0.1") \
        .config("spark.bindAddress", "127.0.0.1") \
        .getOrCreate()

    db_client = DBClient()

    try:
        # 1. Extract
        logger.info("Extracting raw data...")
        orders_pdf = db_client.read_table("orders_raw")
        inventory_pdf = db_client.read_table("inventory_snapshots_raw")
        customers_pdf = db_client.read_table("customers")
        transactions_pdf = db_client.read_table("transactions")

        orders_df = spark.createDataFrame(orders_pdf)
        inventory_df = spark.createDataFrame(inventory_pdf)
        customers_df = spark.createDataFrame(customers_pdf)
        transactions_df = spark.createDataFrame(transactions_pdf)

        # 2. Transform Orders
        logger.info("Transforming Orders...")
        orders_clean = orders_df \
            .withColumn("order_date", to_date(col("order_date"))) \
            .withColumn("processing_timestamp", current_timestamp()) \
            .dropDuplicates(["order_id"])
            
        orders_clean = flag_outliers(orders_clean, "total_amount")
        orders_clean = flag_missing(orders_clean, ["order_date", "customer_id"])

        # Validate Orders (Soft check via flags, hard check for PKs)
        validate_data_quality(orders_clean, ["order_id"], ["order_id"])

        # 3. Transform Inventory
        logger.info("Transforming Inventory...")
        inventory_clean = inventory_df \
            .withColumn("snapshot_date", to_date(col("snapshot_date"))) \
            .withColumn("processing_timestamp", current_timestamp()) \
            .dropDuplicates(["sku", "warehouse_id", "snapshot_date"])
            
        inventory_clean = flag_outliers(inventory_clean, "quantity_on_hand")
        inventory_clean = flag_missing(inventory_clean, ["sku", "warehouse_id"])

        # Validate Inventory
        validate_data_quality(inventory_clean, ["sku", "warehouse_id", "snapshot_date"], ["sku"])

        # 4. Transform Customers
        logger.info("Transforming Customers...")
        customers_clean = customers_df \
            .withColumn("processing_timestamp", current_timestamp()) \
            .dropDuplicates(["customer_id"])
            
        customers_clean = flag_missing(customers_clean, ["email", "name"])
        
        validate_data_quality(customers_clean, ["customer_id"], ["customer_id"])

        # 5. Transform Transactions
        logger.info("Transforming Transactions...")
        transactions_clean = transactions_df \
            .withColumn("transaction_date", to_date(col("transaction_date"))) \
            .withColumn("processing_timestamp", current_timestamp()) \
            .dropDuplicates(["transaction_id"])
            
        transactions_clean = flag_outliers(transactions_clean, "amount")
        transactions_clean = flag_missing(transactions_clean, ["order_id", "payment_method"])

        validate_data_quality(transactions_clean, ["transaction_id"], ["transaction_id"])

        # 6. Load
        logger.info("Loading cleaned data...")
        # Convert back to pandas for SQLite write (simulating write to DB)
        orders_clean_pdf = orders_clean.toPandas()
        inventory_clean_pdf = inventory_clean.toPandas()
        customers_clean_pdf = customers_clean.toPandas()
        transactions_clean_pdf = transactions_clean.toPandas()

        db_client.write_table(orders_clean_pdf, "orders_clean", if_exists="replace")
        db_client.write_table(inventory_clean_pdf, "inventory_clean", if_exists="replace")
        db_client.write_table(customers_clean_pdf, "customers_clean", if_exists="replace")
        db_client.write_table(transactions_clean_pdf, "transactions_clean", if_exists="replace")

        logger.info("ETL Job Completed Successfully")

    except Exception as e:
        logger.error(f"ETL Job Failed: {e}")
        raise
    finally:
        spark.stop()

if __name__ == "__main__":
    run_etl()
