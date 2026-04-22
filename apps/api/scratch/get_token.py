from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_ANON_KEY")

supabase = create_client(url, key)

email = "test_smoke@example.com"
password = "Password123!"

try:
    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
    print(res.session.access_token)
except Exception as e:
    print(f"Error: {e}")
