from supabase import create_client
import os
from dotenv import load_dotenv
import httpx

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_ANON_KEY")

print(f"Connecting to {url}")
supabase = create_client(url, key)

email = "test_smoke@example.com"
password = "Password123!"

try:
    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
    print(f"Success! Token: {res.session.access_token[:20]}...")
except Exception as e:
    print(f"Detailed Error: {e}")
    # Try manual request
    try:
        r = httpx.post(
            f"{url}/auth/v1/token?grant_type=password",
            json={"email": email, "password": password},
            headers={"apikey": key}
        )
        print(f"Manual Result: {r.status_code} {r.text}")
    except Exception as e2:
        print(f"Manual Error: {e2}")
