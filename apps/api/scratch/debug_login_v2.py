import os
from dotenv import load_dotenv
import httpx

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY") # Service role

email = "test_smoke@example.com"
password = "Password123!"

try:
    r = httpx.post(
        f"{url}/auth/v1/token?grant_type=password",
        json={"email": email, "password": password},
        headers={"apikey": key}
    )
    print(f"Manual Result (Service Key): {r.status_code}")
    if r.status_code == 200:
        print(f"Token: {r.json()['access_token']}")
    else:
        print(r.text)
except Exception as e:
    print(f"Error: {e}")
