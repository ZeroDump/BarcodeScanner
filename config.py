import psycopg2
from dotenv import load_dotenv
import os
import pandas as pd

load_dotenv()

def db_run_query(query, params=None):
    connection = None
    cur = None
    try:
        connection = psycopg2.connect(
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT", 6543),
            dbname=os.getenv("DB_NAME", "postgres")
        )
        cur = connection.cursor()

        # 🧾 DEBUG: show the query and params before executing
        print("🧾 Running query:")
        print(query)
        print("📦 Params:", params)
        if query.strip().lower().startswith("select"):
            cur.execute(query, params)
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description]
            df = pd.DataFrame(rows, columns=columns)
            return df
        else:
            cur.execute(query, params)
            connection.commit()
            return None

    except Exception as e:
        print(f"❌ Query failed: {e}")
        if query.strip().lower().startswith("select"):
            return pd.DataFrame()
        return None

    finally:
        if cur:
            cur.close()
        if connection:
            connection.close()
