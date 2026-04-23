import os

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase = create_client(url, key)
try:
    user = supabase.auth.get_user(key)
    print(f"User: {user}")
except Exception as e:
    print(f"Error: {e}")
