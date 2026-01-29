from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/attivita")
def attivita():
    return render_template("attivita.html")

@app.route("/verbali")
def verbali():
    return render_template("verbali.html")

@app.route("/iscritti")
def iscritti():
    return render_template("iscritti.html")

@app.route("/emergenze")
def emergenze():
    return render_template("emergenze.html")

@app.route("/pagina4")
def pagina4():
    return render_template("pagina4.html")

if __name__ == "__main__":
    app.run(debug=True)