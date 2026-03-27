from flask import (
    Flask,
    render_template,
    request,
    send_from_directory,
    current_app,
    flash,
    redirect
)

import csv
import time
import os
from datetime import datetime
from pywebpush import webpush, WebPushException
import json

# 👉 CHIAVI VAPID
VAPID_PUBLIC_KEY = "BFIUzXfa4CrKCYonvgUng451FbUZyrDpY2nX0E6c-FWmpHwU09Q4J5ZxPqmv_vKNzsNuv2exGkdWczSCVqMOWlo"
VAPID_PRIVATE_KEY = "RRXpnXlIg8TYuvBttWTZ8ILeQ6usrFlbUXunQIhtDwI"

app = Flask(__name__)
app.secret_key = "supersegreto123"   # Necessaria per flash()

# ============================
# SERVICE WORKER
# ============================
@app.route('/service-worker.js')
def service_worker():
    return send_from_directory('.', 'service-worker.js', mimetype='application/javascript')


# ============================
# LETTURA ISCRITTI DA CSV
# ============================
def carica_iscritto(username):
    try:
        with open("static/iscritti.csv", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                if r["username"].strip().lower() == username.strip().lower():
                    return r
    except Exception as e:
        print("Errore lettura CSV iscritti:", e)

    return None


# ============================
# FUNZIONI DI UTILITÀ
# ============================
def colore_scadenza(data):
    if data == "-" or data.strip() == "":
        return "secondary"

    try:
        scadenza = datetime.strptime(data, "%Y-%m-%d")
    except:
        return "secondary"

    oggi = datetime.now()
    diff = (scadenza - oggi).days

    if diff < 0:
        return "danger"
    elif diff <= 30:
        return "danger"
    elif diff <= 180:
        return "warning"
    else:
        return "success"


def colore_data(data):
    try:
        d = datetime.strptime(data, "%Y-%m-%d")
    except:
        return "secondary"

    oggi = datetime.now()
    diff = (d - oggi).days

    if diff < 0:
        return "danger"
    elif diff <= 7:
        return "danger"
    elif diff <= 30:
        return "warning"
    else:
        return "success"


# ============================
# LETTURA ALLERTA
# ============================
def leggi_allerta():
    try:
        with open("/tmp/allerta.txt", "r", encoding="utf-8") as f:
            dati = {}
            for riga in f:
                if ":" in riga:
                    k, v = riga.split(":", 1)
                    dati[k.strip()] = v.strip().lower()
            return dati
    except:
        return {"colore": "verde", "messaggio": ""}


# ============================
# ROUTES PRINCIPALI
# ============================
@app.route("/")
def home():
    allerta = leggi_allerta()
    return render_template("index.html", allerta=allerta, nocache=time.time())


@app.route("/debug/lista_file")
def debug_lista_file():
    base_path = os.path.join(current_app.root_path, "templates", "attivita")
    try:
        files = os.listdir(base_path)
    except Exception as e:
        return f"Errore: {e}<br>Path cercato: {base_path}"

    return "<br>".join(files) + f"<br><br>Path: {base_path}"
# ============================
# ATTIVITÀ
# ============================
@app.route("/attivita")
def attivita():
    folder = os.path.abspath("templates/attivita")
    files = [f for f in os.listdir(folder) if f.endswith(".txt")]

    lista_attivita = []

    for f in files:
        path = os.path.join(folder, f)
        data_attivita = "N/D"

        with open(path, "r", encoding="utf-8") as file:
            for riga in file:
                if riga.lower().startswith("data:"):
                    data_attivita = riga.split(":", 1)[1].strip()
                    break

        lista_attivita.append({
            "nome": f.replace(".txt", ""),
            "data": data_attivita
        })

    try:
        lista_attivita.sort(key=lambda x: datetime.strptime(x["data"], "%d/%m/%Y"))
    except:
        pass

    return render_template("attivita.html", files=lista_attivita)

@app.route("/attivita/<nome>")
def attivita_dettaglio(nome):
    base_path = os.path.join(current_app.root_path, "templates", "attivita")

    # Cerca il file ignorando maiuscole/minuscole
    file_trovato = None
    for f in os.listdir(base_path):
        if f.lower() == f"{nome.lower()}.txt":
            file_trovato = f
            break

    if not file_trovato:
        return f"File non trovato: {nome}", 404

    txt_path = os.path.join(base_path, file_trovato)

    # Parsing del file
    dati = {}
    chiave_corrente = None

    with open(txt_path, "r", encoding="utf-8") as f:
        for riga in f:
            riga = riga.rstrip("\n")

            if ":" in riga:
                chiave, valore = riga.split(":", 1)
                chiave = chiave.strip()
                valore = valore.strip()
                dati[chiave] = valore
                chiave_corrente = chiave
            else:
                if chiave_corrente == "descrizione":
                    dati["descrizione"] += "\n" + riga

    return render_template("attivita_dettaglio.html", dati=dati)

# ============================
# VISUALIZZAZIONE RAW (opzionale)
# ============================
@app.route("/attivita/raw/<nomefile>")
def mostra_attivita_raw(nomefile):
    base_path = os.path.join(current_app.root_path, "templates", "attivita")
    txt_path = os.path.join(base_path, f"{nomefile}.txt")

    # MOSTRA IL PERCORSO DIRETTAMENTE NELLA PAGINA
    debug_info = f"""
    <div style='padding:20px; background:#ffeeee; border:2px solid red; margin-bottom:20px;'>
        <b>DEBUG:</b><br>
        root_path: {current_app.root_path}<br>
        base_path: {base_path}<br>
        txt_path: {txt_path}<br>
    </div>
    """

    if os.path.exists(txt_path):
        with open(txt_path, "r", encoding="utf-8") as f:
            contenuto = f.read()

        return f"""
        <div style='max-width:900px; margin:auto; padding:40px; font-size:1.6rem; white-space:pre-wrap;'>
            <h2 style='margin-bottom:30px;'>📄 {nomefile}</h2>
            <pre style='font-size:1.6rem; white-space:pre-wrap;'>{contenuto}</pre>
        </div>
        """

    return f"File non trovato: {txt_path}", 404

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
# SCHEDA PERSONALE (SOLO CSV)
# ============================
@app.route("/scheda_personale")
def scheda_personale():
    username = request.args.get("username")
    if not username:
        return "Errore: manca username", 400

    dati = carica_iscritto(username)
    if not dati:
        return "Utente non trovato", 404

    return render_template("scheda_personale.html", **dati)


# ============================
# LOGIN CSV (ex /iscritti)
# ============================
@app.route("/iscritti", methods=["GET", "POST"])
def iscritti():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip().lower()
        cognome = request.form.get("cognome", "").strip().lower()
        password_input = request.form.get("password", "").strip()

        username_input = f"{nome}_{cognome}"

        try:
            with open("static/iscritti.csv", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)

                for r in reader:
                    if r["username"].strip().lower() == username_input:
                        if r["password"].strip() == password_input:
                            return render_template(
                                "scheda_iscritto.html",
                                dati=r,
                                vapid_public_key=VAPID_PUBLIC_KEY
                            )
                        else:
                            return render_template("iscritti.html", errore="Password errata")

        except Exception as e:
            print(">>> ERRORE:", e)

        return render_template("iscritti.html", errore="Credenziali errate")

    return render_template("iscritti.html")


# ============================
# AGGIORNA DATI (CSV)
# ============================
@app.route("/aggiorna_dati", methods=["POST"])
def aggiorna_dati():
    username = request.form.get("username")
    nuovo_indirizzo = request.form.get("indirizzo")
    nuova_data = request.form.get("data_nascita")
    nuovo_tel = request.form.get("telefono")
    nuova_email = request.form.get("email")

    CSV_PATH = "static/iscritti.csv"
    df = pd.read_csv(CSV_PATH, dtype=str)

    idx = df.index[df["username"] == username].tolist()
    if not idx:
        flash("Errore: utente non trovato", "danger")
        return redirect("/")

    i = idx[0]

    df.at[i, "indirizzo"] = nuovo_indirizzo
    df.at[i, "data_nascita"] = nuova_data
    df.at[i, "telefono"] = nuovo_tel
    df.at[i, "email"] = nuova_email

    df.to_csv(CSV_PATH, index=False)

    flash("Dati aggiornati con successo!", "success")
    return redirect(f"/scheda_personale?username={username}")


# ============================
# AGGIORNA PASSWORD (CSV)
# ============================
@app.route("/aggiorna_password", methods=["POST"])
def aggiorna_password():
    username = request.form.get("username")
    nuova_password = request.form.get("nuova_password")

    if not username or not nuova_password:
        return "Dati mancanti", 400

    righe = []
    trovato = False

    with open("static/iscritti.csv", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            if r["username"] == username:
                r["password"] = nuova_password
                trovato = True
            righe.append(r)

    if not trovato:
        return "Utente non trovato", 404

    with open("static/iscritti.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=righe[0].keys())
        writer.writeheader()
        writer.writerows(righe)

    flash("Password aggiornata con successo!", "success")
    return redirect(f"/scheda_personale?username={username}")


# ============================
# AVVIO SERVER
# ============================
if __name__ == "__main__":
    app.run(debug=True)