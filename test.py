import requests
import json
import random
import time
import threading

BASE_URL = "http://127.0.0.1:5001"

# ---------------------------
# Test singoli endpoint
# ---------------------------
def test_get_elenco():
    print(">>> GET elenco distributori")
    r = requests.get(f"{BASE_URL}/api/distributori")
    print(r.status_code, r.json())

def test_get_provincia():
    print(">>> GET distributori provincia=MI")
    r = requests.get(f"{BASE_URL}/api/distributori/provincia/MI/livelli")
    print(r.status_code, r.json())

def test_get_distributore():
    print(">>> GET livelli distributore id=1")
    r = requests.get(f"{BASE_URL}/api/distributori/1/livelli")
    print(r.status_code, r.json())

def test_get_distributore_notfound():
    print(">>> GET distributore inesistente id=999")
    r = requests.get(f"{BASE_URL}/api/distributori/999/livelli")
    print(r.status_code, r.text)

def test_put_prezzi_ok():
    print(">>> PUT cambio prezzi provincia=MI")
    payload = {"benzina": 1.77, "diesel": 1.66}
    r = requests.put(f"{BASE_URL}/api/distributori/provincia/MI/prezzi", json=payload)
    print(r.status_code, r.json())

def test_put_prezzi_err_json():
    print(">>> PUT senza JSON")
    r = requests.put(f"{BASE_URL}/api/distributori/provincia/MI/prezzi")
    print(r.status_code, r.json())

def test_put_prezzi_err_valore():
    print(">>> PUT con valore non valido")
    payload = {"benzina": "abc"}
    r = requests.put(f"{BASE_URL}/api/distributori/provincia/MI/prezzi", json=payload)
    print(r.status_code, r.json())

def test_put_prezzi_negativi():
    print(">>> PUT con prezzo negativo")
    payload = {"diesel": -1.5}
    r = requests.put(f"{BASE_URL}/api/distributori/provincia/MI/prezzi", json=payload)
    print(r.status_code, r.text)

# ---------------------------
# Stress test multi-thread
# ---------------------------
def stress_worker(n):
    """Worker che fa N richieste casuali"""
    for _ in range(n):
        endpoint = random.choice([
            f"{BASE_URL}/api/distributori",
            f"{BASE_URL}/api/distributori/map",
            f"{BASE_URL}/api/distributori/1/livelli",
            f"{BASE_URL}/api/distributori/provincia/MI/livelli",
        ])
        try:
            r = requests.get(endpoint, timeout=2)
            print(f"[{threading.current_thread().name}] {endpoint} -> {r.status_code}")
        except Exception as e:
            print(f"[{threading.current_thread().name}] Errore: {e}")

def run_stress(num_threads=5, req_per_thread=10):
    print(f">>> Stress test con {num_threads} thread x {req_per_thread} richieste")
    threads = []
    for i in range(num_threads):
        t = threading.Thread(target=stress_worker, args=(req_per_thread,), name=f"T{i}")
        threads.append(t)
        t.start()
    for t in threads:
        t.join()

# ---------------------------
# Main
# ---------------------------
if __name__ == "__main__":
    test_get_elenco()
    test_get_provincia()
    test_get_distributore()
    test_get_distributore_notfound()
    test_put_prezzi_ok()
    test_put_prezzi_err_json()
    test_put_prezzi_err_valore()
    test_put_prezzi_negativi()

    # Stress test (aumenta req_per_thread per più carico)
    run_stress(num_threads=10, req_per_thread=20)