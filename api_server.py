from flask import Flask, jsonify, request, abort, render_template  # Import base da Flask per API e template
from flask_cors import CORS  # Abilita CORS per chiamate da frontend in locale o domini diversi
from dataclasses import dataclass  # Per definire classi dati in modo compatto
from typing import List  # Tipo per liste tipizzate
import threading  # Per usare un lock thread-safe nelle operazioni di scrittura

# --- App Flask unica ---
app = Flask(__name__)  # Istanzia l'app Flask
CORS(app)  # Abilita CORS sull'app

# ---------- Domain classes ----------
@dataclass
class Serbatoio:
    capacita: float  # Capacità massima del serbatoio in litri
    livello: float = 0.0  # Livello corrente in litri (default 0)

    def aggiungi(self, quantita: float):
        # Aumenta il livello senza superare la capacità
        if quantita < 0:
            raise ValueError("quantita negativa")  # Non si può aggiungere una quantità negativa
        self.livello = min(self.capacita, self.livello + quantita)  # Clamp a capacità max

    def preleva(self, quantita: float):
        # Diminuisce il livello se sufficiente
        if quantita < 0:
            raise ValueError("quantita negativa")  # Non si può prelevare quantità negativa
        if quantita > self.livello:
            raise ValueError("livello insufficiente")  # Non si può scendere sotto zero
        self.livello -= quantita  # Aggiorna il livello

    def percentuale(self) -> float:
        # Ritorna la percentuale di riempimento (0..100)
        if self.capacita == 0:
            return 0.0  # Evita divisione per zero
        return (self.livello / self.capacita) * 100.0

@dataclass
class Distributore:
    id: int  # Identificativo univoco
    nome: str  # Nome commerciale
    provincia: str  # Sigla provincia (es. MI)
    indirizzo: str  # Indirizzo testuale
    lat: float  # Latitudine per la mappa
    lon: float  # Longitudine per la mappa
    serbatoio_benzina: Serbatoio  # Serbatoio benzina
    serbatoio_diesel: Serbatoio  # Serbatoio diesel
    prezzo_benzina: float  # Prezzo corrente benzina €/L
    prezzo_diesel: float  # Prezzo corrente diesel €/L

    def to_dict(self) -> dict:
        # Serializza il distributore in un dict JSON-friendly
        return {
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
            "percent_benzina": self.serbatoio_benzina.percentuale(),
            "livello_diesel": self.serbatoio_diesel.livello,
            "capacita_diesel": self.serbatoio_diesel.capacita,
            "percent_diesel": self.serbatoio_diesel.percentuale(),
        }

    def set_prezzo(self, tipo: str, nuovo_prezzo: float):
        # Cambia il prezzo in base al tipo carburante, validando input
        if nuovo_prezzo < 0:
            raise ValueError("Prezzo negativo")  # Prezzi negativi non ammessi
        if tipo == "benzina":
            self.prezzo_benzina = nuovo_prezzo
        elif tipo == "diesel":
            self.prezzo_diesel = nuovo_prezzo
        else:
            raise ValueError("Tipo carburante sconosciuto")  # Tipo valido: 'benzina' o 'diesel'

# --- Dati e lock per threading ---
lock = threading.Lock()  # Lock per proteggere la struttura dati in scrittura concorrente

# Lista in-memory dei distributori (mock/dati di esempio)
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

def find_by_id(did: int) -> Distributore:
    # Cerca un distributore per ID nella lista in-memory, ritorna None se non trovato
    for d in _distributori:
        if d.id == did:
            return d
    return None

# ---------- Web endpoint ----------
@app.route('/')
def homepage():
    # Rende il template index.html (deve essere in templates/)
    return render_template("index.html")

# ---------- API Endpoints ----------
@app.route('/api/distributori', methods=['GET'])
def api_elenco_distributori():
    # Restituisce elenco completo dei distributori (ordinati per id)
    with lock:
        ordinati = sorted(_distributori, key=lambda x: x.id)
        return jsonify([d.to_dict() for d in ordinati])

@app.route('/api/distributori/provincia/<string:provincia>/livelli', methods=['GET'])
def api_livelli_provincia(provincia):
    # Filtra i distributori per provincia e restituisce le info con livelli e percentuali
    with lock:
        selezionati = [d for d in _distributori if d.provincia.lower() == provincia.lower()]
        return jsonify([d.to_dict() for d in selezionati])

@app.route('/api/distributori/<int:did>/livelli', methods=['GET'])
def api_livelli_distributore(did):
    # Restituisce i livelli/percentuali per un distributore specifico
    with lock:
        d = find_by_id(did)
        if d is None:
            abort(404, "Distributore non trovato")  # Se non esiste, 404
        return jsonify(d.to_dict())

@app.route('/api/distributori/map', methods=['GET'])
def api_mappa_distributori():
    # Endpoint ridotto per la mappa: id, nome, provincia, coordinate e prezzi
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
    # Aggiorna i prezzi (benzina/diesel) per tutti i distributori di una provincia
    data = request.get_json(silent=True)  # Legge JSON dal body; silent evita eccezioni
    if not data:
        return jsonify({"error": "Richiesta JSON mancante"}), 400  # Validazione base

    nuovi_prezzi = {}
    if 'benzina' in data:
        try:
            nuovi_prezzi['benzina'] = float(data['benzina'])  # Conversione a float
        except:
            return jsonify({"error": "Prezzo benzina non valido"}), 400  # Errore di formato
    if 'diesel' in data:
        try:
            nuovi_prezzi['diesel'] = float(data['diesel'])  # Conversione a float
        except:
            return jsonify({"error": "Prezzo diesel non valido"}), 400  # Errore di formato
    if not nuovi_prezzi:
        return jsonify({"error": "Nessun prezzo fornito"}), 400  # Nessun campo fornito

    aggiornati = []  # Terrà gli ID dei distributori aggiornati
    with lock:
        for d in _distributori:
            if d.provincia.lower() == provincia.lower():
                if 'benzina' in nuovi_prezzi:
                    d.set_prezzo('benzina', nuovi_prezzi['benzina'])
                if 'diesel' in nuovi_prezzi:
                    d.set_prezzo('diesel', nuovi_prezzi['diesel'])
                aggiornati.append(d.id)  # Registra l'ID aggiornato
    return jsonify({"aggiornati": aggiornati})

if __name__ == '__main__':
    # Avvia il server API su 0.0.0.0:5001 in debug
    app.run(host='0.0.0.0', port=5001, debug=True)
