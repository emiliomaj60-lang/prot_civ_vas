from flask import Flask, render_template, request
from datetime import datetime
import csv

app = Flask(__name__)

# ============================
# DATABASE SEMPLICE ISCRITTI
# ============================

iscritti_db = {
    "mario_rossi": {
        "password": "abc123",
        "nome": "Mario",
        "cognome": "Rossi",
        "indirizzo": "Via Roma 10",
        "telefono": "3331234567",

        # CORSI
        "motosega": True,
        "scadenza_motosega": "2027-05-12",

        "corso_base": False,
        "scadenza_base": "-",

        "altro_fatto": True,
        "scadenza_altro": "2026-11-01"
    }
}

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

        key = f"{nome}_{cognome}"

        if key in iscritti_db and iscritti_db[key]["password"] == password:
            dati = iscritti_db[key]

            # Calcolo colori scadenze
            dati["col_motosega"] = colore_scadenza(dati["scadenza_motosega"])
            dati["col_base"] = colore_scadenza(dati["scadenza_base"])
            dati["col_altro"] = colore_scadenza(dati["scadenza_altro"])

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