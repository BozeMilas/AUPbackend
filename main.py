from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return "Dobar dan, početna stranica...."

@app.route("/kontakt")
def contact():
    return "Moj kontakt broj je 063 123 456."

@app.route("/email")
def email():
    return "Moj email je hrvoje.ljubic@sum.ba"

@app.route("/pozdrav/<ime>")
def pozdrav(ime):
    return "Dobrodošli: " + ime + " ...."

@app.route("/pozdrav/<ime>/<prezime>")
def pozdrav2(ime, prezime):
    return f"Dobrodošli {ime} {prezime} na web stranicu"

@app.route("/zbroji/<int:broj1>/<int:broj2>")
def zbroji(broj1, broj2):
    return f"Rezultat je: {broj1 + broj2}"

@app.route("/prijava")
def prijava():
    kor_ime = request.args.get("kor_ime")
    lozinka = request.args.get("lozinka")

    if kor_ime == "marko" and lozinka == "123456":
        return 'Uspješna prijava'
    else:
        return 'Netočni pristupni podaci'

@app.route("/app_info")
def app_info():
    return jsonify({
        "kolegij": "Algoritmi u primjeni",
        "ak_god": "2025/2026",
        "tehnologije": ["Flask", "VueJS"]
    })

@app.route("/html")
def html():
    return ('Dobar dan. <p style="color: red;">Ovo je paragraf.</p>'
            + 'Ovo je <a href="https://google.com">link</a>.')

# postman.com/downloads

@app.route("/pomnozi", methods=["POST"])
def pomnozi():
    data = request.get_json()

    broj1 = data.get('broj1', 0)
    broj2 = data.get('broj2', 0)
    umnozak = broj1 * broj2

    return jsonify({
        "umnozak": umnozak
    })

@app.route('/zadnja/<jmbg>', methods=['POST'])
def zadnja(jmbg):
    data = request.get_json()

    ime = data.get('ime')
    prezime = data.get('prezime')
    godiste = request.args.get('godiste')

    return jsonify({
        "ime": ime,
        "prezime": prezime,
        "jmbg": jmbg,
        "godiste": godiste
    })

# Zadatak 3
# Napraviti POST rutu koja ujedno ima jedan argument koji se šalje kroz URL
# Kroz body se šalju dva argumenta.
# Npr. kroz url šaljemo JMBG, a kroz body šaljemo ime i prezim
# Sa JSON-om vraćamo natrag sva 3 podatka

'''
curl --location 'http://127.0.0.1:5000/zadnja/0502996150012?godiste=1996' \
--header 'Content-Type: application/json' \
--data '{
    "ime": "Marko",
    "prezime": "Markić"
}'
'''

if __name__ == "__main__":
    app.run(debug=True)