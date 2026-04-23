import os
import requests
from supabase import create_client, Client

url = "https://smawxojcohoqeqyksuvp.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNtYXd4b2pjb2hvcWVxeWtzdXZwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MDMwMDIwMSwiZXhwIjoyMDg1ODc2MjAxfQ.tBr2ZgGQfVcHTlWfi7puOXwjVoVZC281Wycu8cYMa6k"

supabase: Client = create_client(url, key)

try:
    # Try to select one row and see the columns
    res = supabase.table("method_results").select("*").limit(1).execute()
    if res.data:
        print("Columns in method_results:", res.data[0].keys())
    else:
        print("No data in method_results. Trying to fetch schema info...")
        # Since we can't easily fetch schema via REST, we'll try to insert a dummy and see error
        try:
            supabase.table("method_results").insert({"delta": 0}).execute()
        except Exception as e:
            print("Error inserting delta:", str(e))
except Exception as e:
    print("Error:", str(e))
