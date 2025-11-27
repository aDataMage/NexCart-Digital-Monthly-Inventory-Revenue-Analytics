import pandas as pd
from sqlalchemy import create_engine, text
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

class DBClient:
    def __init__(self):
        self.engine = create_engine(settings.DB_URL)

    def read_table(self, table_name: str) -> pd.DataFrame:
        """Reads a table from SQLite into a pandas DataFrame."""
        try:
            query = f"SELECT * FROM {table_name}"
            df = pd.read_sql(query, self.engine)
            logger.info(f"Successfully read {len(df)} rows from {table_name}")
            return df
        except Exception as e:
            logger.error(f"Error reading table {table_name}: {e}")
            raise

    def write_table(self, df: pd.DataFrame, table_name: str, if_exists: str = "append"):
        """Writes a pandas DataFrame to a SQLite table."""
        try:
            df.to_sql(table_name, self.engine, if_exists=if_exists, index=False)
            logger.info(f"Successfully wrote {len(df)} rows to {table_name}")
        except Exception as e:
            logger.error(f"Error writing to table {table_name}: {e}")
            raise

    def execute_query(self, query: str) -> pd.DataFrame:
        """Executes a raw SQL query and returns results as DataFrame."""
        try:
            df = pd.read_sql(query, self.engine)
            logger.info(f"Successfully executed query, returned {len(df)} rows")
            return df
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            raise

