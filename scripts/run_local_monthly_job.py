import sys
import os
import logging

# Add project root to path
sys.path.append(os.getcwd())

# Set PySpark Python variables to use the current executable
os.environ['PYSPARK_PYTHON'] = sys.executable
os.environ['PYSPARK_DRIVER_PYTHON'] = sys.executable

from spark_jobs.etl_raw_to_cleaned import run_etl
from spark_jobs.kpi_aggregation import run_kpi_aggregation
from src.reporting.report_builder import ReportBuilder
from src.email_client import EmailClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting local monthly job run...")

    # 1. Run ETL
    logger.info(">>> Step 1: Running ETL...")
    run_etl()

    # 2. Run KPI Aggregation
    logger.info(">>> Step 2: Running KPI Aggregation...")
    run_kpi_aggregation()

    # 3. Generate Report
    logger.info(">>> Step 3: Generating Report...")
    builder = ReportBuilder()
    builder.build_report()

    # 4. Send Email (Mock)
    logger.info(">>> Step 4: Sending Email...")
    email_client = EmailClient()
    # Hardcoded path for local run
    report_path = "reports/artifacts/monthly_report.html"
    
    with open(report_path, "r") as f:
        body = f.read()
        
    email_client.send_email(
        subject="Monthly Inventory Report (Local Run)",
        body=body,
        attachment_path=report_path
    )

    logger.info("Local monthly job run completed successfully.")

if __name__ == "__main__":
    main()
