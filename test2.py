import asyncio  # Per gestire concorrenza asincrona
import aiohttp  # Client HTTP asincrono ad alte prestazioni
import random  # Per scegliere endpoint casuali
import time  # Per misurare tempi e calcolare RPS

BASE_URL = "http://127.0.0.1:5001"  # API server (api_server.py) porta 5001

# Lista degli endpoint da bombardare nello stress test
ENDPOINTS = [
    "/api/distributori",
    "/api/distributori/map",
    "/api/distributori/1/livelli",
    "/api/distributori/provincia/MI/livelli",
]

async def fetch(session, url):
    # Effettua una GET asincrona con timeout; ritorna solo lo status code
    try:
        async with session.get(url, timeout=3) as resp:
            return resp.status
    except Exception as e:
        return f"ERR:{e}"  # In caso di errore di rete/timeout

async def worker(session, num_requests, results):
    # Esegue num_requests richieste casuali e accumula gli status in results
    for _ in range(num_requests):
        endpoint = random.choice(ENDPOINTS)
        url = BASE_URL + endpoint
        status = await fetch(session, url)
        results.append(status)

async def run_stress(total_requests=10000, concurrency=100):
    # Lancia molti worker in parallelo per generare carico
    tasks = []
    results = []
    async with aiohttp.ClientSession() as session:
        # Quante richieste per ogni worker in base alla concorrenza
        req_per_worker = total_requests // concurrency
        for _ in range(concurrency):
            tasks.append(worker(session, req_per_worker, results))
        start = time.time()  # Inizio misura tempo
        await asyncio.gather(*tasks)  # Esegue tutti i task
        elapsed = time.time() - start  # Tempo totale trascorso
        print(f"\n--- Stress test completato ---")
        print(f"Totale richieste: {len(results)}")
        print(f"Tempo totale: {elapsed:.2f} s")
        print(f"RPS (Requests/sec): {len(results)/elapsed:.2f}")

        # Riassume i codici di risposta per un quadro d'insieme
        summary = {}
        for r in results:
            summary[r] = summary.get(r, 0) + 1
        print("\nRisultati per codice HTTP:")
        for k, v in summary.items():
            print(f"{k}: {v}")

if __name__ == "__main__":
    # Avvia lo stress test con 10k richieste e concorrenza 50
    asyncio.run(run_stress(total_requests=10000, concurrency=50))
