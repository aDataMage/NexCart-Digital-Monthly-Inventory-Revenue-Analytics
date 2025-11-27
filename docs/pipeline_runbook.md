# Pipeline Runbook

## Schedule
The pipeline runs automatically on the 1st of every month at 00:00 UTC via Airflow.

## Manual Execution
To run the pipeline manually (e.g., for ad-hoc reporting or testing):

### Local Run (No Airflow)
```bash
python scripts/run_local_monthly_job.py
```

### Airflow Run
Trigger the `monthly_inventory_report` DAG from the Airflow UI.

## Failure Recovery
1. **ETL Failure**:
    - Check logs for data quality errors or connection issues.
    - Fix data issues in source or update validation logic.
    - Clear the task in Airflow to retry.
2. **KPI Failure**:
    - Check if ETL completed successfully.
    - Verify schema of cleaned tables.
3. **Report Generation Failure**:
    - Check LLM API connectivity and quota.
    - Check template syntax.
4. **Email Failure**:
    - Check SMTP credentials in `.env`.
    - Verify network connectivity.

## Configuration
All configuration is managed via environment variables (see `.env.example`).
- `DB_URL`: Database connection string.
- `LLM_API_KEY`: API key for the LLM provider.
- `SMTP_*`: Email server settings.
