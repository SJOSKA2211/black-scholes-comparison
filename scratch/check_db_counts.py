
import asyncio
import os
from supabase import create_client, Client

async def check_db():
    url = "https://smawxojcohoqeqyksuvp.supabase.co"
    key = os.environ.get("SUPABASE_KEY") or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNtYXd4b2pjb2hvcWVxeWtzdXZwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MDMwMDIwMSwiZXhwIjoyMDg1ODc2MjAxfQ.tBr2ZgGQfVcHTlWfi7puOXwjVoVZC281Wycu8cYMa6k"
    supabase: Client = create_client(url, key)
    
    tables = ["option_parameters", "method_results", "market_data", "validation_metrics", "scrape_runs"]
    for table in tables:
        try:
            res = supabase.table(table).select("count", count="exact").limit(1).execute()
            print(f"Table {table}: {res.count} rows")
        except Exception as e:
            print(f"Table {table}: Error {e}")

if __name__ == "__main__":
    asyncio.run(check_db())
