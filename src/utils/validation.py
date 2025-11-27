from pyspark.sql import DataFrame
from pyspark.sql.functions import col, count, when

def check_nulls(df: DataFrame, columns: list[str]) -> dict[str, int]:
    """
    Checks for null values in specified columns.
    Returns a dictionary with column names and null counts.
    """
    null_counts = {}
    for column in columns:
        count_null = df.filter(col(column).isNull()).count()
        if count_null > 0:
            null_counts[column] = count_null
    return null_counts

def check_duplicates(df: DataFrame, key_columns: list[str]) -> int:
    """
    Checks for duplicate records based on key columns.
    Returns the count of duplicate rows.
    """
    total_count = df.count()
    distinct_count = df.select(key_columns).distinct().count()
    return total_count - distinct_count

def validate_data_quality(df: DataFrame, key_columns: list[str], required_columns: list[str]) -> bool:
    """
    Runs basic data quality checks:
    1. No duplicates on primary keys.
    2. No nulls in required columns.
    Returns True if checks pass, raises ValueError otherwise.
    """
    # Check duplicates
    dupes = check_duplicates(df, key_columns)
    if dupes > 0:
        raise ValueError(f"Data Quality Failed: Found {dupes} duplicate records based on keys {key_columns}")

    # Check nulls
    nulls = check_nulls(df, required_columns)
    if nulls:
        raise ValueError(f"Data Quality Failed: Found nulls in required columns: {nulls}")

    return True
