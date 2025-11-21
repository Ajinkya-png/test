"""
Minimal load test using asyncio and aiohttp.
Replace with Locust or k6 for production-grade load testing.
"""
import asyncio
import aiohttp

async def hit_health(session):
    async with session.get("http://localhost:8000/api/v1/monitoring/health") as resp:
        return resp.status

async def run(n=50):
    async with aiohttp.ClientSession() as session:
        tasks = [hit_health(session) for _ in range(n)]
        results = await asyncio.gather(*tasks)
        print("Statuses:", results.count(200), "success /", len(results), "total")

if __name__ == "__main__":
    asyncio.run(run(100))
