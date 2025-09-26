from flask import Flask, render_template

# Create a Flask app instance for the web server
app = Flask(__name__)

# ---------- Web Endpoints ----------
@app.route('/')
def homepage():
    """Serves the main homepage."""
    return render_template("index.html")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)