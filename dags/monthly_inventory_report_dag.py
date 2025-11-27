from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from datetime import timedelta, datetime
from pathlib import Path
import sys
import os

# Add project root to path so we can import src modules
PROJECT_ROOT = "d:/Projects/NOV-2025"
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from spark_jobs.etl_raw_to_cleaned import run_etl
from spark_jobs.kpi_aggregation import run_kpi_aggregation
from src.reporting.report_builder import ReportBuilder
from src.email_client import EmailClient

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'monthly_inventory_report',
    default_args=default_args,
    description='End-of-month inventory and revenue reporting pipeline',
    schedule_interval='@monthly',
    start_date=days_ago(1),
    catchup=False,
) as dag:

    t1_etl = PythonOperator(
        task_id='run_spark_etl',
        python_callable=run_etl,
    )

    t2_kpi = PythonOperator(
        task_id='calculate_kpis',
        python_callable=run_kpi_aggregation,
    )

    def create_monthly_folder(**context):
        """Create monthly folder for reports."""
        # Get execution date or use current month
        execution_date = context.get('execution_date') or datetime.now()
        month_folder = execution_date.strftime('%Y-%m')
        
        reports_dir = Path(PROJECT_ROOT) / 'reports' / month_folder
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Store the month in XCom for other tasks
        return month_folder

    def generate_monthly_report(**context):
        """Generate SQL-based analytical reports."""
        # Get the month from XCom
        ti = context['ti']
        report_month = ti.xcom_pull(task_ids='create_monthly_folder')
        
        # Build reports for the specified month
        builder = ReportBuilder(report_month=report_month)
        builder.build_report()
        
        return str(builder.output_dir)
        
    def send_report_email(**context):
        """Send email notification with report link."""
        ti = context['ti']
        report_dir = ti.xcom_pull(task_ids='generate_reports')
        report_month = ti.xcom_pull(task_ids='create_monthly_folder')
        
        email_client = EmailClient()
        
        # Read index file
        index_path = Path(report_dir) / 'index.html'
        
        with open(index_path, 'r', encoding='utf-8') as f:
            body = f.read()
            
        email_client.send_email(
            subject=f"Monthly Inventory Analytics Report - {report_month}",
            body=body,
            attachment_path=str(index_path)
        )

    t3_create_folder = PythonOperator(
        task_id='create_monthly_folder',
        python_callable=create_monthly_folder,
    )

    t4_report = PythonOperator(
        task_id='generate_reports',
        python_callable=generate_monthly_report,
    )

    t5_email = PythonOperator(
        task_id='send_email',
        python_callable=send_report_email,
    )

    t1_etl >> t2_kpi >> t3_create_folder >> t4_report >> t5_email
