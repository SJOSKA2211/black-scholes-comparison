import asyncio
import httpx
import time
import os
from dotenv import load_dotenv

load_dotenv()

def get_token():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    email = "test_smoke@example.com"
    password = "Password123!"
    
    r = httpx.post(
        f"{url}/auth/v1/token?grant_type=password",
        json={"email": email, "password": password},
        headers={"apikey": key}
    )
    if r.status_code == 200:
        return r.json()['access_token']
    raise Exception(f"Failed to get token: {r.text}")

async def send_request(client, token, methods):
    payload = {
        "params": {
            "underlying_price": 100.0,
            "strike_price": 100.0,
            "maturity_years": 1.0,
            "volatility": 0.2,
            "risk_free_rate": 0.05,
            "option_type": "call",
            "is_american": False
        },
        "methods": methods
    }
    
    start = time.time()
    try:
        response = await client.post(
            "https://localhost/api/v1/price",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=30.0
        )
        duration = time.time() - start
        return response.status_code, duration
    except Exception as e:
        return str(e), time.time() - start

async def main():
    token = get_token()
    methods = [
        "analytical", "explicit_fdm", "implicit_fdm", "crank_nicolson",
        "standard_mc", "antithetic_mc", "control_variate_mc", "quasi_mc",
        "binomial_crr", "trinomial"
    ]
    
    print(f"Starting load test with {len(methods)} methods in batch.")
    
    async with httpx.AsyncClient(verify=False) as client:
        # Simulate 10 concurrent users
        tasks = [send_request(client, token, methods) for _ in range(10)]
        results = await asyncio.gather(*tasks)
        
    print("\nResults:")
    success_count = 0
    durations = []
    for i, (status, duration) in enumerate(results):
        print(f"User {i+1}: Status {status}, Duration {duration:.4f}s")
        if status == 200:
            success_count += 1
            durations.append(duration)
            
    if durations:
        print(f"\nSummary: {success_count}/10 successful. Avg duration: {sum(durations)/len(durations):.4f}s")
    else:
        print("\nSummary: 0 successful requests.")

if __name__ == "__main__":
    asyncio.run(main())
