from flask import Flask, render_template, request
from datetime import datetime

app = Flask(__name__)

# DATABASE SEMPLICE (poi lo sposteremo in SQLite)
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

# FUNZIONE PER COLORI SCADENZE
def colore_scadenza(data):
    if data == "-" or data.strip() == "":
        return "secondary"  # grigio

    try:
        scadenza = datetime.strptime(data, "%Y-%m-%d")
    except:
        return "secondary"

    oggi = datetime.now()
    diff = (scadenza - oggi).days

    if diff < 0:
        return "danger"   # rosso
    elif diff <= 30:
        return "danger"   # rosso
    elif diff <= 180:
        return "warning"  # giallo
    else:
        return "success"  # verde


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/attivita")
def attivita():
    return render_template("attivita.html")


@app.route("/verbali")
def verbali():
    return render_template("verbali.html")


# 🔵 AREA ISCRITTI (LOGIN)
@app.route("/iscritti", methods=["GET", "POST"])
def iscritti():
    if request.method == "POST":
        nome = request.form["nome"].strip().lower()
        cognome = request.form["cognome"].strip().lower()
        password = request.form["password"].strip()

        key = f"{nome}_{cognome}"

        if key in iscritti_db and iscritti_db[key]["password"] == password:
            dati = iscritti_db[key]

            # COLORI SCADENZE
            dati["col_motosega"] = colore_scadenza(dati["scadenza_motosega"])
            dati["col_base"] = colore_scadenza(dati["scadenza_base"])
            dati["col_altro"] = colore_scadenza(dati["scadenza_altro"])

            return render_template("scheda_iscritto.html", dati=dati)
        else:
            return render_template("iscritti.html", errore="Credenziali errate")

    return render_template("iscritti.html")


@app.route("/emergenze")
def emergenze():
    return render_template("emergenze.html")


@app.route("/pagina4")
def pagina4():
    return render_template("pagina4.html")


if __name__ == "__main__":
    app.run(debug=True)