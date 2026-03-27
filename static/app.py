from flask import Flask, render_template, request, send_from_directory
import sqlite3
from datetime import datetime
import csv
import time
import os
from pywebpush import webpush, WebPushException
import json

from flask import Flask, render_template, request, send_from_directory, current_app

# 👉 CHIAVI VAPID
VAPID_PUBLIC_KEY = "BFIUzXfa4CrKCYonvgUng451FbUZyrDpY2nX0E6c-FWmpHwU09Q4J5ZxPqmv_vKNzsNuv2exGkdWczSCVqMOWlo"
VAPID_PRIVATE_KEY = "RRXpnXlIg8TYuvBttWTZ8ILeQ6usrFlbUXunQIhtDwI"

app = Flask(__name__)

# ============================
app.secret_key = "supersegreto123"   # CHIAVE SEGRETA
# ============================

# ============================
# SERVICE WORKER
# ============================
@app.route('/service-worker.js')
def service_worker():
    return send_from_directory('.', 'service-worker.js', mimetype='application/javascript')


# ============================
# FUNZIONI NOTIFICHE
# ============================
def notifiche_attive(telefono):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT 1 FROM subscriptions WHERE telefono = ?", (telefono,))
    row = c.fetchone()
    conn.close()
    return row is not None


@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


# ============================
# LETTURA ISCRITTI DA CSV
# ============================
def carica_iscritto(username):
    try:
        with open("static/iscritti.csv", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                if r["username"].strip().lower() == username.strip().lower():

                    r["motosega"] = r["motosega"] == "1"
                    r["corso_base"] = r["corso_base"] == "1"
                    r["altro_fatto"] = r["altro_fatto"] == "1"

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

import os


@app.route("/debug/lista_file")
def debug_lista_file():
    base_path = os.path.join(current_app.root_path, "templates", "attivita")
    try:
        files = os.listdir(base_path)
    except Exception as e:
        return f"Errore: {e}<br>Path cercato: {base_path}"

    return "<br>".join(files) + f"<br><br>Path: {base_path}"



# ============================
# ELENCO ATTIVITÀ (con data)
# ============================
@app.route("/attivita")
def lista_attivita():
    folder = os.path.abspath("templates/attivita")
    files = [f for f in os.listdir(folder) if f.endswith(".txt")]

    lista_attivita = []

    for f in files:
        path = os.path.join(folder, f)
        data_attivita = "N/D"

        # Leggiamo solo la riga "data:"
        with open(path, "r", encoding="utf-8") as file:
            for riga in file:
                if riga.lower().startswith("data:"):
                    data_attivita = riga.split(":", 1)[1].strip()
                    break

        nome_originale = f.replace(".txt", "")
        nome_url = nome_originale.lower()  # <-- URL SEMPRE MINUSCOLO

        lista_attivita.append({
            "nome": nome_originale,
            "nome_url": nome_url,
            "data": data_attivita
        })

    # Ordiniamo per data (opzionale)
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

@app.route("/scheda_personale")
def scheda_personale():
    username = session.get("username")
    if not username:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT * FROM iscritti WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()

    if not row:
        return "Utente non trovato"

    dati = dict(row)

    # Convertiamo 0/1 in booleano per il template
    dati["notifiche_attive"] = (row["notifiche_attive"] == 1)

    return render_template("scheda_personale.html", **dati)

@app.route("/api/allerta")
def api_allerta():
    return leggi_allerta()


@app.route("/emergenze")
def emergenze():
    return render_template("emergenze.html", vapid_public_key=VAPID_PUBLIC_KEY)


@app.route("/invia_allerta")
def invia_allerta():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT id, nome FROM gruppi")
    gruppi = c.fetchall()
    conn.close()

    return render_template("invia_allerta.html", gruppi=gruppi)


@app.route("/pagina4")
def pagina4():
    return render_template("pagina4.html")

@app.route("/iscritti", methods=["GET", "POST"])
def iscritti():
    print(">>> /iscritti chiamata")

    if request.method == "POST":
        print(">>> Metodo POST ricevuto")

        nome = request.form.get("nome", "").strip().lower()
        cognome = request.form.get("cognome", "").strip().lower()
        password_input = request.form.get("password", "").strip()

        username_input = f"{nome}_{cognome}"
        possibili_username = {
            username_input,
            username_input.replace("_", "."),
            username_input.replace("_", " "),
            username_input.replace("_", "-"),
            username_input.replace("_", "")
        }

        try:
            with open("static/iscritti.csv", newline="", encoding="utf-8") as f:
                reader = csv.reader(f)

                # Leggiamo l'intestazione
                header = next(reader)
                num_colonne = len(header)

                for row in reader:
                    if not row:
                        continue

                    # Username = prima colonna
                    username_csv = row[0].strip().lower()

                    if username_csv in possibili_username:

                        # Password = ultima colonna della riga
                        password_csv = row[-1].strip()

                        if password_csv == password_input:

                            # Ricostruzione dizionario robusta
                            r = {}

                            for i, col in enumerate(header):
                                if i < len(row):
                                    r[col] = row[i].strip()
                                else:
                                    r[col] = ""  # colonna mancante → vuota

                            # Conversione corsi
                            def flag(x): return x == "1"

                            r["corso_aib"] = flag(r.get("corso_aib", ""))
                            r["corso_motosega"] = flag(r.get("corso_motosega", ""))
                            r["corso_ricerca_sco"] = flag(r.get("corso_ricerca_sco", ""))
                            r["corso_1"] = flag(r.get("corso_1", ""))
                            r["corso_2"] = flag(r.get("corso_2", ""))
                            r["corso_3"] = flag(r.get("corso_3", ""))
                            r["corso_4"] = flag(r.get("corso_4", ""))
                            r["corso_5"] = flag(r.get("corso_5", ""))

                            # Badge colori
                            r["col_aib"] = "success" if r["corso_aib"] else "secondary"
                            r["col_motosega"] = "success" if r["corso_motosega"] else "secondary"
                            r["col_ricerca"] = "success" if r["corso_ricerca_sco"] else "secondary"

                            # Scadenze vuote
                            for key in [
                                "scadenza_aib", "scadenza_motosega", "scadenza_ricerca",
                                "scadenza_corso_1", "scadenza_corso_2", "scadenza_corso_3",
                                "scadenza_corso_4", "scadenza_corso_5"
                            ]:
                                r[key] = ""

                            # Notifiche
                            try:
                                r["notifiche_attive"] = notifiche_attive(r.get("telefono", ""))
                            except:
                                r["notifiche_attive"] = False

                            # Alias campi
                            r["codice_fiscale"] = r.get("cod_fiscale", "")
                            r["cod_is"] = r.get("cod_is", "")
                            r["cod_2"] = r.get("cod_2", "")
                            r["sez_alpini"] = r.get("sez_alpini", "")

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
# ROUTE SALVATAGGIO SUBSCRIPTION
# ============================
@app.route("/subscribe", methods=["POST"])
def subscribe():
    data = request.json
    endpoint = data.get("endpoint")
    p256dh = data.get("p256dh")
    auth = data.get("auth")
    telefono = data.get("telefono")
    gruppo = data.get("gruppo")   # 👈 AGGIUNTO

    print(">>> Subscription ricevuta:", data)

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # Salva o aggiorna la subscription
    c.execute("""
        INSERT OR REPLACE INTO subscriptions (telefono, endpoint, p256dh, auth, gruppo)
        VALUES (?, ?, ?, ?, ?)
    """, (telefono, endpoint, p256dh, auth, gruppo))

    # 🔥 AGGIUNTA FONDAMENTALE:
    # Imposta lo stato notifiche come ATTIVE
    c.execute("""
        UPDATE iscritti
        SET notifiche_attive = 1
        WHERE telefono = ?
    """, (telefono,))

    conn.commit()
    conn.close()

    return "OK"

# ============================
# ROUTE ATTIVITA
# ============================

@app.route("/attivita")
def attivita():
    folder = os.path.abspath("templates/attivita")
    files = [f for f in os.listdir(folder) if f.endswith(".txt")]

    lista_attivita = []

    for f in files:
        path = os.path.join(folder, f)
        data_attivita = "N/D"

        # Leggiamo solo la riga "data:"
        with open(path, "r", encoding="utf-8") as file:
            for riga in file:
                if riga.lower().startswith("data:"):
                    data_attivita = riga.split(":", 1)[1].strip()
                    break

        lista_attivita.append({
            "nome": f.replace(".txt", ""),
            "data": data_attivita
        })

    # Ordiniamo per data (opzionale)
    try:
        lista_attivita.sort(key=lambda x: datetime.strptime(x["data"], "%d/%m/%Y"))
    except:
        pass

    return render_template("attivita.html", files=lista_attivita)

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
# INVIO NOTIFICHE AI GRUPPI
# ============================
@app.route("/api/send_alert_group", methods=["POST"])
def send_alert_group():
    try:
        data = request.json
        gruppo = data.get("gruppo_id")
        titolo = data.get("titolo")
        messaggio = data.get("messaggio")
        livello = data.get("livello")

        print("Dati ricevuti:", data)

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("""
            SELECT endpoint, p256dh, auth 
            FROM subscriptions 
            WHERE gruppo = ?
        """, (gruppo,))
        subs = c.fetchall()
        conn.close()

        print(f"Trovate {len(subs)} subscription per il gruppo {gruppo}")

        payload = {
            "title": titolo,
            "body": messaggio,
            "level": livello
        }

        for endpoint, p256dh, auth in subs:
            subscription_info = {
                "endpoint": endpoint,
                "keys": {
                    "p256dh": p256dh,
                    "auth": auth
                }
            }

            try:
                webpush(
                    subscription_info,
                    data=json.dumps(payload),
                    vapid_private_key=VAPID_PRIVATE_KEY,
                    vapid_claims={"sub": "mailto:admin@example.com"}
                )
                print("Notifica inviata a:", endpoint)

            except WebPushException as e:
                print("Errore invio notifica:", e)

        with open("/tmp/allerta.txt", "w", encoding="utf-8") as f:
            f.write(f"colore: {livello}\n")
            f.write(f"messaggio: {titolo} – {messaggio}")

        print("File allerta.txt aggiornato correttamente!")

        return "OK"

    except Exception as e:
        print("Errore generale:", e)
        return "ERRORE", 500

# ============================
# aggiorna_dati
# ============================

from flask import flash, redirect, request
import pandas as pd

@app.route("/aggiorna_dati", methods=["POST"])
def aggiorna_dati():
    username = request.form.get("username")
    nuovo_indirizzo = request.form.get("indirizzo")
    nuova_data = request.form.get("data_nascita")
    nuovo_tel = request.form.get("telefono")
    nuova_email = request.form.get("email")

    df = pd.read_csv("iscritti.csv", dtype=str)

    # Trova la riga dell’utente
    idx = df.index[df["username"] == username].tolist()
    if not idx:
        flash("Errore: utente non trovato", "danger")
        return redirect("/")

    i = idx[0]

    # Aggiorna i campi
    df.at[i, "indirizzo"] = nuovo_indirizzo
    df.at[i, "data_nascita"] = nuova_data
    df.at[i, "telefono"] = nuovo_tel
    df.at[i, "email"] = nuova_email

    # Salva
    df.to_csv("iscritti.csv", index=False)

    # ⭐ NOTIFICA VISIVA ⭐
    flash("Dati aggiornati con successo!", "success")

    return redirect(f"/scheda/{username}")

# ============================
# AGGIORNA PASSWORD
# ============================
from flask import flash, redirect, request
import pandas as pd

@app.route("/aggiorna_password", methods=["POST"])
def aggiorna_password():
    username = request.form.get("username")
    nuova_password = request.form.get("nuova_password")

    df = pd.read_csv("iscritti.csv", dtype=str)

    # Trova la riga dell’utente
    idx = df.index[df["username"] == username].tolist()
    if not idx:
        flash("Errore: utente non trovato", "danger")
        return redirect("/")

    i = idx[0]

    # Aggiorna la password
    df.at[i, "password"] = nuova_password

    # Salva il CSV
    df.to_csv("iscritti.csv", index=False)

    # ⭐ NOTIFICA VISIVA ⭐
    flash("Password aggiornata con successo!", "success")

    return redirect(f"/scheda/{username}")

# ============================
# AVVIO SERVER
# ============================
if __name__ == "__main__":
    app.run(debug=True)