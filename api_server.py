from flask import Flask, jsonify, request, abort, render_template
from flask_cors import CORS
from dataclasses import dataclass
from typing import List
import threading

# --- App Flask unica ---
app = Flask(__name__)
CORS(app)

# ---------- Domain classes ----------
@dataclass
class Serbatoio:
    capacita: float
    livello: float = 0.0

    def aggiungi(self, quantita: float):
        if quantita < 0:
            raise ValueError("quantita negativa")
        self.livello = min(self.capacita, self.livello + quantita)

    def preleva(self, quantita: float):
        if quantita < 0:
            raise ValueError("quantita negativa")
        if quantita > self.livello:
            raise ValueError("livello insufficiente")
        self.livello -= quantita

    def percentuale(self) -> float:
        if self.capacita == 0:
            return 0.0
        return (self.livello / self.capacita) * 100.0

@dataclass
class Distributore:
    id: int
    nome: str
    provincia: str
    indirizzo: str
    lat: float
    lon: float
    serbatoio_benzina: Serbatoio
    serbatoio_diesel: Serbatoio
    prezzo_benzina: float
    prezzo_diesel: float

    def to_dict(self) -> dict:
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
        if nuovo_prezzo < 0:
            raise ValueError("Prezzo negativo")
        if tipo == "benzina":
            self.prezzo_benzina = nuovo_prezzo
        elif tipo == "diesel":
            self.prezzo_diesel = nuovo_prezzo
        else:
            raise ValueError("Tipo carburante sconosciuto")

# --- Dati e lock per threading ---
lock = threading.Lock()
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
    for d in _distributori:
        if d.id == did:
            return d
    return None

# ---------- Web endpoint ----------
@app.route('/')
def homepage():
    return render_template("index.html")

# ---------- API Endpoints ----------
@app.route('/api/distributori', methods=['GET'])
def api_elenco_distributori():
    with lock:
        ordinati = sorted(_distributori, key=lambda x: x.id)
        return jsonify([d.to_dict() for d in ordinati])

@app.route('/api/distributori/provincia/<string:provincia>/livelli', methods=['GET'])
def api_livelli_provincia(provincia):
    with lock:
        selezionati = [d for d in _distributori if d.provincia.lower() == provincia.lower()]
        return jsonify([d.to_dict() for d in selezionati])

@app.route('/api/distributori/<int:did>/livelli', methods=['GET'])
def api_livelli_distributore(did):
    with lock:
        d = find_by_id(did)
        if d is None:
            abort(404, "Distributore non trovato")
        return jsonify(d.to_dict())

@app.route('/api/distributori/map', methods=['GET'])
def api_mappa_distributori():
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
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Richiesta JSON mancante"}), 400

    nuovi_prezzi = {}
    if 'benzina' in data:
        try:
            nuovi_prezzi['benzina'] = float(data['benzina'])
        except:
            return jsonify({"error": "Prezzo benzina non valido"}), 400
    if 'diesel' in data:
        try:
            nuovi_prezzi['diesel'] = float(data['diesel'])
        except:
            return jsonify({"error": "Prezzo diesel non valido"}), 400
    if not nuovi_prezzi:
        return jsonify({"error": "Nessun prezzo fornito"}), 400

    aggiornati = []
    with lock:
        for d in _distributori:
            if d.provincia.lower() == provincia.lower():
                if 'benzina' in nuovi_prezzi:
                    d.set_prezzo('benzina', nuovi_prezzi['benzina'])
                if 'diesel' in nuovi_prezzi:
                    d.set_prezzo('diesel', nuovi_prezzi['diesel'])
                aggiornati.append(d.id)
    return jsonify({"aggiornati": aggiornati})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)