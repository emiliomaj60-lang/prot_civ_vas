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

        # Username digitato dall’utente
        username_input = f"{nome}_{cognome}"

        # Normalizzazioni accettate
        possibili_username = {
            username_input,
            username_input.replace("_", "."),
            username_input.replace("_", " "),
            username_input.replace("_", "-"),
            username_input.replace("_", ""),
        }

        # Carica TUTTI gli iscritti dal CSV
        try:
            with open("static/iscritti.csv", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:

                    username_csv = r["username"].strip().lower()

                    # Se il CSV contiene una variante accettata → match
                    if username_csv in possibili_username:

                        # Password corretta?
                        if r["password"] == password:

                            # Conversione campi booleani
                            r["motosega"] = r["motosega"] == "1"
                            r["corso_base"] = r["corso_base"] == "1"
                            r["altro_fatto"] = r["altro_fatto"] == "1"

                            # Colori badge
                            r["col_motosega"] = colore_scadenza(r["scadenza_motosega"])
                            r["col_base"] = colore_scadenza(r["scadenza_base"])
                            r["col_altro"] = colore_scadenza(r["scadenza_altro"])

                            return render_template("scheda_iscritto.html", dati=r)

                        else:
                            return render_template("iscritti.html", errore="Password errata")

        except Exception as e:
            print("Errore lettura CSV:", e)

        return render_template("iscritti.html", errore="Credenziali errate")

    return render_template("iscritti.html")

# ============================
# ATTIVITÀ PROGRAMMATE (CSV)
# ============================

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

                # --- Converti data da GG-MM-AAAA a AAAA-MM-GG ---
                giorno, mese, anno = r["data"].split("-")
                r["data_iso"] = f"{anno}-{mese}-{giorno}"   # per calcoli
                r["data"] = f"{giorno}-{mese}-{anno}"       # per visualizzazione

                # --- Calcolo colore usando la data ISO ---
                r["colore"] = colore_data(r["data_iso"])

                lista.append(r)

    except FileNotFoundError:
        lista = []

    return render_template("attivita.html", attivita=lista)



# ============================
# DETTAGLIO ATTIVITÀ (FILE TXT)
# ============================

@app.route("/attivita/<nome>")
def attivita_dettaglio(nome):
    path = f"templates/attivita/{nome}.txt"

    if not os.path.exists(path):
        return "Attività non trovata", 404

    dati = {}

    # --- Lettura file TXT ---
    with open(path, "r", encoding="utf-8") as f:
        for riga in f:
            if ":" in riga:
                chiave, valore = riga.split(":", 1)
                dati[chiave.strip()] = valore.strip()

    # --- Conversione data se presente (GG/MM/AAAA → AAAA-MM-GG) ---
    if "data" in dati:
        try:
            giorno, mese, anno = dati["data"].replace("-", "/").split("/")
            dati["data_iso"] = f"{anno}-{mese}-{giorno}"
        except:
            dati["data_iso"] = ""

    return render_template("attivita_dettaglio.html", dati=dati)


# ============================
# CONTATTI
# ============================

@app.route("/contatti")
def contatti():
    try:
        with open("static/contatti.txt", "r", encoding="utf-8") as f:
            testo = f.read()
    except:
        testo = "Nessun contatto disponibile."

    return render_template("contatti.html", testo=testo)


# ============================
# VERBALI
# ============================

import os

@app.route("/verbali")
def verbali():
    path = "templates/verbali"
    files = []

    for f in os.listdir(path):
        if f.endswith(".html"):
            files.append(f.replace(".html", ""))

    files.sort()

    return render_template("verbali.html", verbali=files)


@app.route("/verbali/<nome>")
def verbale_dettaglio(nome):
    try:
        return render_template(f"verbali/{nome}.html")
    except:
        return "Verbale non trovato", 404


# ============================
# AVVIO SERVER
# ============================

if __name__ == "__main__":
    app.run(debug=True)