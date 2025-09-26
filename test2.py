import asyncio
import aiohttp
import random
import time

BASE_URL = "http://127.0.0.1:5001"

ENDPOINTS = [
    "/api/distributori",
    "/api/distributori/map",
    "/api/distributori/1/livelli",
    "/api/distributori/provincia/MI/livelli",
]

async def fetch(session, url):
    try:
        async with session.get(url, timeout=3) as resp:
            return resp.status
    except Exception as e:
        return f"ERR:{e}"

async def worker(session, num_requests, results):
    for _ in range(num_requests):
        endpoint = random.choice(ENDPOINTS)
        url = BASE_URL + endpoint
        status = await fetch(session, url)
        results.append(status)

async def run_stress(total_requests=10000, concurrency=100):
    tasks = []
    results = []
    async with aiohttp.ClientSession() as session:
        # Quante richieste per ogni worker
        req_per_worker = total_requests // concurrency
        for _ in range(concurrency):
            tasks.append(worker(session, req_per_worker, results))
        start = time.time()
        await asyncio.gather(*tasks)
        elapsed = time.time() - start
        print(f"\n--- Stress test completato ---")
        print(f"Totale richieste: {len(results)}")
        print(f"Tempo totale: {elapsed:.2f} s")
        print(f"RPS (Requests/sec): {len(results)/elapsed:.2f}")

        # Riassunto codici risposta
        summary = {}
        for r in results:
            summary[r] = summary.get(r, 0) + 1
        print("\nRisultati per codice HTTP:")
        for k, v in summary.items():
            print(f"{k}: {v}")

if __name__ == "__main__":
    asyncio.run(run_stress(total_requests=10000, concurrency=50))