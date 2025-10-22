import requests  # Libreria HTTP sincrona per testare gli endpoint
import json  # Non strettamente necessario qui, ma utile per debug/print
import random  # Per scegliere endpoint casuali nello stress test
import time  # Per misurazioni temporali se servisse
import threading  # Per eseguire richieste concorrenti su più thread

BASE_URL = "http://127.0.0.1:5001"  # Base URL dell'API (api_server.py su porta 5001)

# ---------------------------
# Test singoli endpoint
# ---------------------------
def test_get_elenco():
    print(">>> GET elenco distributori")
    r = requests.get(f"{BASE_URL}/api/distributori")  # Chiama l'endpoint elenco
    print(r.status_code, r.json())  # Stampa status + payload JSON

def test_get_provincia():
    print(">>> GET distributori provincia=MI")
    r = requests.get(f"{BASE_URL}/api/distributori/provincia/MI/livelli")  # Filtra per MI
    print(r.status_code, r.json())

def test_get_distributore():
    print(">>> GET livelli distributore id=1")
    r = requests.get(f"{BASE_URL}/api/distributori/1/livelli")  # Livelli per id=1
    print(r.status_code, r.json())

def test_get_distributore_notfound():
    print(">>> GET distributore inesistente id=999")
    r = requests.get(f"{BASE_URL}/api/distributori/999/livelli")  # Caso 404 atteso
    print(r.status_code, r.text)

def test_put_prezzi_ok():
    print(">>> PUT cambio prezzi provincia=MI")
    payload = {"benzina": 1.77, "diesel": 1.66}  # Nuovi prezzi validi
    r = requests.put(f"{BASE_URL}/api/distributori/provincia/MI/prezzi", json=payload)  # PUT con JSON
    print(r.status_code, r.json())

def test_put_prezzi_err_json():
    print(">>> PUT senza JSON")
    r = requests.put(f"{BASE_URL}/api/distributori/provincia/MI/prezzi")  # Nessun body => 400
    print(r.status_code, r.json())

def test_put_prezzi_err_valore():
    print(">>> PUT con valore non valido")
    payload = {"benzina": "abc"}  # Non convertibile a float => errore
    r = requests.put(f"{BASE_URL}/api/distributori/provincia/MI/prezzi", json=payload)
    print(r.status_code, r.json())

def test_put_prezzi_negativi():
    print(">>> PUT con prezzo negativo")
    payload = {"diesel": -1.5}  # Valore negativo => l'API dovrebbe rifiutarlo internamente
    r = requests.put(f"{BASE_URL}/api/distributori/provincia/MI/prezzi", json=payload)
    print(r.status_code, r.text)

# ---------------------------
# Stress test multi-thread
# ---------------------------
def stress_worker(n):
    """Worker che fa N richieste casuali"""
    for _ in range(n):
        endpoint = random.choice([
            f"{BASE_URL}/api/distributori",  # Elenco completo
            f"{BASE_URL}/api/distributori/map",  # Dati per mappa
            f"{BASE_URL}/api/distributori/1/livelli",  # Livelli singolo
            f"{BASE_URL}/api/distributori/provincia/MI/livelli",  # Livelli per provincia
        ])
        try:
            r = requests.get(endpoint, timeout=2)  # Timeout breve per non bloccare
            print(f"[{threading.current_thread().name}] {endpoint} -> {r.status_code}")
        except Exception as e:
            print(f"[{threading.current_thread().name}] Errore: {e}")  # Logga eventuali errori di rete

def run_stress(num_threads=5, req_per_thread=10):
    print(f">>> Stress test con {num_threads} thread x {req_per_thread} richieste")
    threads = []
    for i in range(num_threads):
        t = threading.Thread(target=stress_worker, args=(req_per_thread,), name=f"T{i}")  # Crea thread worker
        threads.append(t)
        t.start()  # Avvia thread
    for t in threads:
        t.join()  # Attende il completamento di tutti i thread

# ---------------------------
# Main
# ---------------------------
if __name__ == "__main__":
    # Esegue i test singoli
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
