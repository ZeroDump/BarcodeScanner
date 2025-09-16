import psycopg2
from dotenv import load_dotenv
import os
import pandas as pd

load_dotenv()

def db_run_query(query, params=None):
    try:
        connection = psycopg2.connect(
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT", 6543),
            dbname=os.getenv("DB_NAME", "postgres")
        )
        cur = connection.cursor()
        
        # Determine query type
        if query.strip().lower().startswith("select"):
            # For SELECT, return DataFrame
            df = pd.read_sql(query, connection, params=params)
            return df
        else:
            # For INSERT/UPDATE/DELETE
            cur.execute(query, params)
            connection.commit()  # Important! Save changes
            return None

    except Exception as e:
        print(f"Query failed: {e}")
        return pd.DataFrame() if query.strip().lower().startswith("select") else None

    finally:
        if 'cur' in locals() and cur:
            cur.close()
        if 'connection' in locals() and connection:
            connection.close()
