from flask import Flask, jsonify, request, send_file, abort, render_template  # Import necessari per API e template
from flask_cors import CORS  # Per abilitare CORS
from dataclasses import dataclass, field, asdict  # Dataclass per modelli dati
from typing import List  # Tipi
import threading  # Lock per thread-safety

app = Flask(__name__)  # Crea app Flask
CORS(app)  # Abilita CORS

# ---------- Domain classes ----------
@dataclass
class Serbatoio:
    capacita: float  # Capacità massima (L)
    livello: float = 0.0  # Livello attuale (L), default 0

    def aggiungi(self, quantita: float):
        # Aumenta livello senza superare capacità; blocca quantità negative
        if quantita < 0:
            raise ValueError("quantita negativa")
        self.livello = min(self.capacita, self.livello + quantita)

    def preleva(self, quantita: float):
        # Diminuisce livello se sufficiente; blocca quantità negative
        if quantita < 0:
            raise ValueError("quantita negativa")
        if quantita > self.livello:
            raise ValueError("livello insufficiente")
        self.livello -= quantita

    def percentuale(self) -> float:
        # Percentuale riempimento (0..100)
        if self.capacita == 0:
            return 0.0
        return (self.livello / self.capacita) * 100.0

@dataclass
class Distributore:
    id: int  # ID univoco
    nome: str  # Nome stazione
    provincia: str  # Sigla provincia (es. MI)
    indirizzo: str  # Indirizzo completo
    lat: float  # Latitudine mappa
    lon: float  # Longitudine mappa
    serbatoio_benzina: Serbatoio  # Serbatoio benzina
    serbatoio_diesel: Serbatoio  # Serbatoio diesel
    prezzo_benzina: float  # Prezzo €/L benzina
    prezzo_diesel: float  # Prezzo €/L diesel

    def to_dict(self, include_private: bool = False) -> dict:
        # Serializza il distributore per output API (campi principali)
        base = {
            "id": self.id,
            "nome": self.nome,
            "provincia": self.provincia,
            "indirizzo": self.indirizzo,
            "lat": self.lat,
            "lon": self.lon,
            "prezzo_benzina": self.prezzo_benzina,
            "prezzo_diesel": self.prezzo_diesel,
            "livello_benzina": self.serbatoio_benzina.livello,
            "capacita_benzina": self.serbatoio_benzina.capacita,
            "livello_diesel": self.serbatoio_diesel.livello,
            "capacita_diesel": self.serbatoio_diesel.capacita,
        }
        return base  # Ritorna i dati base (ignore include_private in questa implementazione)

    def set_prezzo(self, tipo: str, nuovo_prezzo: float):
        # Imposta il prezzo in base al tipo di carburante con validazione
        if nuovo_prezzo < 0:
            raise ValueError("Prezzo negativo")
        if tipo == "benzina":
            self.prezzo_benzina = nuovo_prezzo
        elif tipo == "diesel":
            self.prezzo_diesel = nuovo_prezzo
        else:
            raise ValueError("Tipo carburante sconosciuto")

lock = threading.Lock()  # Lock per gestire concorrenza su dati in-memory

# Dataset in-memory di esempio
_distributori: List[Distributore] = [
    Distributore(
        id=1,
        nome="IPERSTAR Ovest",
        provincia="MI",
        indirizzo="Via Roma 10, Milano",
        lat=45.4642,
        lon=9.1900,
        serbatoio_benzina=Serbatoio(capacita=10000, livello=7000),
        serbatoio_diesel=Serbatoio(capacita=12000, livello=9000),
        prezzo_benzina=1.90,
        prezzo_diesel=1.80,
    ),
    Distributore(
        id=2,
        nome="IPERSTAR Sud",
        provincia="MI",
        indirizzo="Piazza Duomo 1, Milano",
        lat=45.4643,
        lon=9.1910,
        serbatoio_benzina=Serbatoio(capacita=8000, livello=2000),
        serbatoio_diesel=Serbatoio(capacita=10000, livello=4000),
        prezzo_benzina=1.92,
        prezzo_diesel=1.82,
    ),
    Distributore(
        id=3,
        nome="IPERSTAR Nord",
        provincia="TO",
        indirizzo="Corso Francia 2, Torino",
        lat=45.0703,
        lon=7.6869,
        serbatoio_benzina=Serbatoio(capacita=9000, livello=9000),
        serbatoio_diesel=Serbatoio(capacita=11000, livello=5000),
        prezzo_benzina=1.95,
        prezzo_diesel=1.85,
    ),
]

# Utility
def find_by_id(did: int) -> Distributore:
    # Cerca e ritorna il distributore con id == did, altrimenti None
    for d in _distributori:
        if d.id == did:
            return d
    return None

# ---------- API Endpoints ----------
@app.route('/api/distributori', methods=['GET'])
def api_elenco_distributori():
    """0. elenco ordinato su ID dei distributori (tutte le informazioni)"""
    # Ritorna la lista di distributori come JSON, ordinata per ID (asc)
    with lock:
        ordinati = sorted(_distributori, key=lambda x: x.id)
        return jsonify([d.to_dict() for d in ordinati])

@app.route('/api/distributori/provincia/<string:provincia>/livelli', methods=['GET'])
def api_livelli_provincia(provincia):
    """1. livello di carburante nei distributori di una provincia"""
    # Filtra per provincia (case-insensitive) e ritorna livelli/percentuali
    with lock:
        selezionati = [d for d in _distributori if d.provincia.lower() == provincia.lower()]
        if not selezionati:
            return jsonify([])  # Nessun distributore trovato per la provincia
        return jsonify([
            {
                "id": d.id,
                "nome": d.nome,
                "livello_benzina": d.serbatoio_benzina.livello,
                "capacita_benzina": d.serbatoio_benzina.capacita,
                "percent_benzina": d.serbatoio_benzina.percentuale(),
                "livello_diesel": d.serbatoio_diesel.livello,
                "capacita_diesel": d.serbatoio_diesel.capacita,
                "percent_diesel": d.serbatoio_diesel.percentuale(),
            }
            for d in selezionati
        ])

@app.route('/api/distributori/<int:did>/livelli', methods=['GET'])
def api_livelli_distributore(did):
    """2. livello di carburante in un distributore specifico"""
    # Recupera un singolo distributore per ID e ritorna i livelli
    with lock:
        d = find_by_id(did)
        if d is None:
            abort(404, "Distributore non trovato")  # 404 se non esiste
        return jsonify({
            "id": d.id,
            "nome": d.nome,
            "livello_benzina": d.serbatoio_benzina.livello,
            "capacita_benzina": d.serbatoio_benzina.capacita,
            "percent_benzina": d.serbatoio_benzina.percentuale(),
            "livello_diesel": d.serbatoio_diesel.livello,
            "capacita_diesel": d.serbatoio_diesel.capacita,
            "percent_diesel": d.serbatoio_diesel.percentuale(),
        })

@app.route('/api/distributori/map', methods=['GET'])
def api_mappa_distributori():
    """3. visualizzazione su mappa di tutti i distributori - ritorna i dati necessari"""
    # Endpoint ridotto per la mappa: coordinate, nomi e prezzi
    with lock:
        return jsonify([
            {
                "id": d.id,
                "nome": d.nome,
                "provincia": d.provincia,
                "lat": d.lat,
                "lon": d.lon,
                "prezzo_benzina": d.prezzo_benzina,
                "prezzo_diesel": d.prezzo_diesel,
            }
            for d in _distributori
        ])

@app.route('/api/distributori/provincia/<string:provincia>/prezzi', methods=['PUT'])
def api_cambia_prezzi_provincia(provincia):
    """Modifica il prezzo della benzina o del diesel in tutti i distributori di una provincia.
    JSON body: {"benzina": 1.95, "diesel": 1.85} (uno o entrambi)
    """
    # Legge JSON dal body; silent=True evita eccezione se non JSON
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Richiesta JSON mancante"}), 400  # Validazione base

    nuovi_prezzi = {}
    if 'benzina' in data:
        try:
            nuovi_prezzi['benzina'] = float(data['benzina'])
        except Exception:
            return jsonify({"error": "Prezzo benzina non valido"}), 400  # Valore non convertibile
    if 'diesel' in data:
        try:
            nuovi_prezzi['diesel'] = float(data['diesel'])
        except Exception:
            return jsonify({"error": "Prezzo diesel non valido"}), 400  # Valore non convertibile

    if not nuovi_prezzi:
        return jsonify({"error": "Nessun prezzo fornito"}), 400  # Nessun campo valido passato

    aggiornati = []  # Lista ID distributori aggiornati
    with lock:
        for d in _distributori:
            if d.provincia.lower() == provincia.lower():
                if 'benzina' in nuovi_prezzi:
                    d.set_prezzo('benzina', nuovi_prezzi['benzina'])
                if 'diesel' in nuovi_prezzi:
                    d.set_prezzo('diesel', nuovi_prezzi['diesel'])
                aggiornati.append(d.id)

    return jsonify({"aggiornati": aggiornati})

@app.route('/')
def homepage():
    # Ritorna il template index.html per la home web
    return render_template("index.html")

if __name__ == '__main__':
    # Avvia il web server (porta 5000) in debug
    app.run(host='0.0.0.0', port=5000, debug=True)
