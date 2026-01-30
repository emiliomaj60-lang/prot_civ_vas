from flask import Flask, render_template, request
from datetime import datetime
import csv

app = Flask(__name__)

# ============================
# LETTURA ISCRITTI DA CSV
# ============================

def carica_iscritto(username):
    """Carica un iscritto dal file CSV in base allo username."""
    try:
        with open("static/iscritti.csv", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                if r["username"].strip().lower() == username.strip().lower():

                    # Conversione campi booleani
                    r["motosega"] = r["motosega"] == "1"
                    r["corso_base"] = r["corso_base"] == "1"
                    r["altro_fatto"] = r["altro_fatto"] == "1"

                    # Colori badge
                    r["col_motosega"] = colore_scadenza(r["scadenza_motosega"])
                    r["col_base"] = colore_scadenza(r["scadenza_base"])
                    r["col_altro"] = colore_scadenza(r["scadenza_altro"])

                    return r
    except Exception as e:
        print("Errore lettura CSV iscritti:", e)

    return None


# ============================
# FUNZIONI DI UTILITÀ
# ============================

def colore_scadenza(data):
    """Restituisce un colore Bootstrap in base alla scadenza."""
    if data == "-" or data.strip() == "":
        return "secondary"

    try:
        scadenza = datetime.strptime(data, "%Y-%m-%d")
    except:
        return "secondary"

    oggi = datetime.now()
    diff = (scadenza - oggi).days

    if diff < 0:
        return "danger"   # scaduto
    elif diff <= 30:
        return "danger"   # urgente
    elif diff <= 180:
        return "warning"  # entro 6 mesi
    else:
        return "success"  # ok


def colore_data(data):
    """Colora le attività programmate in base alla data."""
    try:
        d = datetime.strptime(data, "%Y-%m-%d")
    except:
        return "secondary"

    oggi = datetime.now()
    diff = (d - oggi).days

    if diff < 0:
        return "danger"   # già passata
    elif diff <= 7:
        return "danger"   # entro una settimana
    elif diff <= 30:
        return "warning"  # entro un mese
    else:
        return "success"  # lontana


# ============================
# ROUTES PRINCIPALI
# ============================

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/emergenze")
def emergenze():
    return render_template("emergenze.html")


@app.route("/pagina4")
def pagina4():
    return render_template("pagina4.html")


# ============================
# AREA ISCRITTI (LOGIN)
# ============================

@app.route("/iscritti", methods=["GET", "POST"])
def iscritti():
    if request.method == "POST":
        nome = request.form["nome"].strip().lower()
        cognome = request.form["cognome"].strip().lower()
        password = request.form["password"].strip()

        username = f"{nome}_{cognome}"

        dati = carica_iscritto(username)

        if dati and dati["password"] == password:
            return render_template("scheda_iscritto.html", dati=dati)
        else:
            return render_template("iscritti.html", errore="Credenziali errate")

    return render_template("iscritti.html")


# ============================
# ATTIVITÀ PROGRAMMATE (CSV)
# ============================

@app.route("/attivita")
def attivita():
    lista = []

    try:
        with open("static/attivita.csv", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                r["colore"] = colore_data(r["data"])
                lista.append(r)
    except FileNotFoundError:
        lista = []

    return render_template("attivita.html", attivita=lista)


@app.route("/attivita/<nome>")
def attivita_dettaglio(nome):
    try:
        return render_template(f"attivita/{nome}.html")
    except:
        return "Attività non trovata", 404


# ============================
# VERBALI
# ============================

@app.route("/verbali")
def verbali():
    return render_template("verbali.html")


# ============================
# AVVIO SERVER
# ============================

if __name__ == "__main__":
    app.run(debug=True)