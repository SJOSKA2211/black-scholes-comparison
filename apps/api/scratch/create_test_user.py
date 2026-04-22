from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase = create_client(url, key)

email = "test_smoke@example.com"
password = "Password123!"

try:
    # Try to delete if exists
    users = supabase.auth.admin.list_users()
    for u in users:
        if u.email == email:
            supabase.auth.admin.delete_user(u.id)
            print(f"Deleted existing user {email}")
            
    # Create user
    res = supabase.auth.admin.create_user({
        "email": email,
        "password": password,
        "email_confirm": True
    })
    print(f"Created user: {res.user.id}")
except Exception as e:
    print(f"Error: {e}")
