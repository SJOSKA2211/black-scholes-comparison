from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase = create_client(url, key)
# Use admin API to list users
try:
    users = supabase.auth.admin.list_users()
    print(f"Users: {len(users)} users found.")
    for u in users:
        print(f"User: {u.email} (ID: {u.id})")
except Exception as e:
    print(f"Error: {e}")
