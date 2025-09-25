import os
from flask import Flask, render_template, request, jsonify
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev')

# Connessione al DB MySQL
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv('MYSQL_HOST'),
        user=os.getenv('MYSQL_USER'),
        password=os.getenv('MYSQL_PASSWORD'),
        database=os.getenv('MYSQL_DB')
    )

# ==================== API ====================
@app.route('/api/distributors', methods=['GET'])
def list_distributors():
    province = request.args.get('province')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if province:
        cursor.execute("SELECT * FROM distributori WHERE provincia=%s ORDER BY id", (province,))
    else:
        cursor.execute("SELECT * FROM distributori ORDER BY id")
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(results)


@app.route('/api/distributors/<int:id>', methods=['GET'])
def get_distributor(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM distributori WHERE id=%s", (id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    if result:
        return jsonify(result)
    return jsonify({'error':'Distributore non trovato'}), 404


@app.route('/api/distributors/province/<province>/levels', methods=['GET'])
def province_levels(province):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, nome, benzina, diesel FROM distributori WHERE provincia=%s ORDER BY id", (province,))
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    for r in results:
        r['livello_totale'] = (r['benzina'] or 0) + (r['diesel'] or 0)
    return jsonify(results)


@app.route('/api/distributors/province/<province>/prices', methods=['POST'])
def set_prices_province(province):
    data = request.get_json() or {}
    benzina = data.get('benzina')
    diesel = data.get('diesel')

    if benzina is None and diesel is None:
        return jsonify({'error':'Nessun prezzo fornito'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    query_parts = []
    params = []
    if benzina is not None:
        query_parts.append("prezzo_benzina=%s")
        params.append(benzina)
    if diesel is not None:
        query_parts.append("prezzo_diesel=%s")
        params.append(diesel)
    params.append(province)
    query = f"UPDATE distributori SET {', '.join(query_parts)} WHERE provincia=%s"
    cursor.execute(query, tuple(params))
    conn.commit()
    count = cursor.rowcount
    cursor.close()
    conn.close()
    return jsonify({'updated': count})

# ==================== Web Routes ====================
@app.route('/')
def index():
    province = request.args.get('province')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if province:
        cursor.execute("SELECT * FROM distributori WHERE provincia=%s ORDER BY id", (province,))
    else:
        cursor.execute("SELECT * FROM distributori ORDER BY id")
    distributori = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('index.html', distributori=distributori)


@app.route('/distributor/<int:id>')
def distributor(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM distributori WHERE id=%s", (id,))
    d = cursor.fetchone()
    cursor.close()
    conn.close()
    if not d:
        return "Distributore non trovato", 404
    return render_template('distributor.html', distributore=d)

if __name__ == '__main__':
    app.run(debug=True)