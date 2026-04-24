
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv("apps/api/.env")

DB_HOST = "db.smawxojcohoqeqyksuvp.supabase.co"
DB_NAME = "postgres"
DB_USER = "postgres.smawxojcohoqeqyksuvp"
DB_PASS = os.getenv("RABBITMQ_PASSWORD") # Trying common password

try:
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        port=5432
    )
    cur = conn.cursor()
    
    # Enable Realtime
    sql = """
    ALTER PUBLICATION supabase_realtime ADD TABLE 
        user_profiles, option_parameters, method_results, market_data, 
        validation_metrics, scrape_runs, audit_log, scrape_errors, notifications;
    """
    try:
        cur.execute(sql)
        print("Realtime enabled successfully.")
    except Exception as e:
        print(f"Failed to enable realtime: {e}")
        conn.rollback()

    # Disable RLS for testing if requested
    tables = ["notifications", "method_results", "option_parameters", "user_profiles"]
    for table in tables:
        try:
            cur.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")
            print(f"RLS disabled for {table}")
        except Exception as e:
            print(f"Failed to disable RLS for {table}: {e}")
            conn.rollback()

    conn.commit()
    cur.close()
    conn.close()
except Exception as e:
    print(f"Connection failed: {e}")
