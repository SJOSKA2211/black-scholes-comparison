import asyncio
from dotenv import load_dotenv
load_dotenv()
from src.database import repository

async def run():
    print("Testing market data")
    try:
        res = await repository.insert_market_data([{"option_id": "a5592c9d-995d-46df-909e-72b19d224dc2", "trade_date": "2026-04-25", "data_source": "spy"}])
        print("Inserted:", res)
        data = await repository.get_market_data("spy", trade_date="2026-04-25")
        print("Got:", data)
    except Exception as e:
        print("Error:", e)

asyncio.run(run())
