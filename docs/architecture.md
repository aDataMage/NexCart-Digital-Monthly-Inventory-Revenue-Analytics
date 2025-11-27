# System Architecture

## Overview
The Monthly Inventory & Revenue Analytics Pipeline is designed to automate the end-of-month reporting process. It ingests raw data from a SQL database, processes it using Apache Spark, generates insights using an LLM, and distributes reports via email.

## Components

### 1. Data Source (SQLite)
- Simulates a production SQL database.
- Contains raw tables: `orders_raw`, `inventory_snapshots_raw`, `channels_raw`.
- Seeded with realistic sample data.

### 2. Data Processing (PySpark)
- **ETL Job (`spark_jobs/etl_raw_to_cleaned.py`)**:
    - Reads raw data.
    - Cleans and standardizes types.
    - Deduplicates records.
    - Validates data quality.
    - Writes to `orders_clean` and `inventory_clean`.
- **KPI Job (`spark_jobs/kpi_aggregation.py`)**:
    - Aggregates revenue and order counts by channel.
    - Computes monthly metrics.
    - Writes to `channel_kpis`.

### 3. Insight Generation (LLM)
- **LLM Client (`src/llm_client.py`)**:
    - Abstraction over LLM provider (e.g., OpenAI).
    - Generates narrative summaries based on computed KPIs.

### 4. Reporting
- **Report Builder (`src/reporting/report_builder.py`)**:
    - Combines KPIs and LLM insights.
    - Renders Jinja2 templates (`text_report.j2`, `html_report.j2`).
- **Email Client (`src/email_client.py`)**:
    - Sends the final report to stakeholders.

### 5. Orchestration (Airflow)
- **DAG (`dags/monthly_inventory_report_dag.py`)**:
    - Schedules the pipeline to run monthly.
    - Manages dependencies between tasks.
    - Handles retries and failures.

## Data Flow
1. **Ingest**: Raw data -> Spark DataFrame.
2. **Clean**: Spark DataFrame -> Cleaned Tables (SQLite).
3. **Aggregate**: Cleaned Tables -> KPI Tables (SQLite).
4. **Analyze**: KPI Data -> LLM -> Narrative Insights.
5. **Report**: Insights + KPIs -> HTML/Text Report.
6. **Deliver**: Report -> Email -> Stakeholders.
