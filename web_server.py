from flask import Flask, render_template  # Import base per server web e rendering template

# Create a Flask app instance for the web server
app = Flask(__name__)  # Istanza separata per il web server (serve l'HTML)

# ---------- Web Endpoints ----------
@app.route('/')
def homepage():
    """Serves the main homepage."""
    # Rende index.html situato in templates/
    return render_template("index.html")

if __name__ == '__main__':
    # Avvia il web server sulla porta 5000 in debug
    app.run(host='0.0.0.0', port=5000, debug=True)
