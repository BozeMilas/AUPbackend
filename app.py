import os

from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy import func, or_

from extensions import db, migrate
from models import Kolegij, Profesor, TerminNastave, Ucionica

app = Flask(__name__)
CORS(app)

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///aup1.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
migrate.init_app(app, db)

with app.app_context():
    db.create_all()


def as_int(value):
    if value in (None, ""):
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def get_or_404(model, item_id, message):
    item = db.session.get(model, item_id)
    if not item:
        return None, (jsonify({"message": message}), 404)

    return item, None


@app.route("/")
def index():
    return jsonify({"message": "API je pokrenut."})


@app.route("/dashboard")
def dashboard():
    broj_profesora = db.session.query(func.count(Profesor.id)).scalar() or 0
    broj_kolegija = db.session.query(func.count(Kolegij.id)).scalar() or 0
    broj_ucionica = db.session.query(func.count(Ucionica.id)).scalar() or 0
    broj_termina = db.session.query(func.count(TerminNastave.id)).scalar() or 0
    prosjek_ects = db.session.query(func.avg(Kolegij.ects)).scalar() or 0

    return jsonify(
        {
            "broj_profesora": broj_profesora,
            "broj_kolegija": broj_kolegija,
            "broj_ucionica": broj_ucionica,
            "broj_termina": broj_termina,
            "prosjek_ects": round(float(prosjek_ects), 2),
        }
    )


@app.route("/profesori", methods=["GET"])
def profesori():
    q = request.args.get("q", "", type=str).strip()
    upit = Profesor.query

    if q:
        pojam = f"%{q}%"
        upit = upit.filter(
            or_(
                Profesor.ime.ilike(pojam),
                Profesor.prezime.ilike(pojam),
                Profesor.email.ilike(pojam),
                Profesor.titula.ilike(pojam),
            )
        )

    return jsonify([profesor.to_dict() for profesor in upit.order_by(Profesor.id).all()])


@app.route("/profesori-dropdown", methods=["GET"])
def profesori_dropdown():
    return jsonify(
        [
            {"title": f"{profesor.ime} {profesor.prezime}", "value": profesor.id}
            for profesor in Profesor.query.order_by(Profesor.ime, Profesor.prezime).all()
        ]
    )


@app.route("/profesori/<int:item_id>", methods=["GET"])
def profesor(item_id):
    profesor, error = get_or_404(Profesor, item_id, "Profesor nije pronađen.")
    if error:
        return error

    return jsonify(profesor.to_dict())


@app.route("/profesori", methods=["POST"])
def novi_profesor():
    data = request.get_json(silent=True) or {}

    if not data.get("ime") or not data.get("prezime") or not data.get("email"):
        return jsonify({"message": "Ime, prezime i e-pošta su obavezni."}), 400

    profesor = Profesor(
        ime=data.get("ime"),
        prezime=data.get("prezime"),
        email=data.get("email"),
        titula=data.get("titula"),
    )

    db.session.add(profesor)
    db.session.commit()

    return jsonify(profesor.to_dict()), 201


@app.route("/profesori/<int:item_id>", methods=["PUT"])
def uredi_profesora(item_id):
    profesor, error = get_or_404(Profesor, item_id, "Profesor nije pronađen.")
    if error:
        return error

    data = request.get_json(silent=True) or {}
    profesor.ime = data.get("ime", profesor.ime)
    profesor.prezime = data.get("prezime", profesor.prezime)
    profesor.email = data.get("email", profesor.email)
    profesor.titula = data.get("titula")

    db.session.commit()

    return jsonify(profesor.to_dict())


@app.route("/profesori/<int:item_id>", methods=["DELETE"])
def izbrisi_profesora(item_id):
    profesor, error = get_or_404(Profesor, item_id, "Profesor nije pronađen.")
    if error:
        return error

    Kolegij.query.filter_by(nositelj_id=profesor.id).update({"nositelj_id": None})
    TerminNastave.query.filter_by(profesor_id=profesor.id).update({"profesor_id": None})
    db.session.delete(profesor)
    db.session.commit()

    return jsonify({"message": "Profesor je obrisan."})


@app.route("/kolegiji", methods=["GET"])
def kolegiji():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 5, type=int)
    q = request.args.get("q", "", type=str).strip()

    upit = Kolegij.query.outerjoin(Profesor, Kolegij.nositelj_id == Profesor.id)

    if q:
        pojam = f"%{q}%"
        upit = upit.filter(
            or_(
                Kolegij.naziv.ilike(pojam),
                Profesor.ime.ilike(pojam),
                Profesor.prezime.ilike(pojam),
            )
        )

    upit = upit.order_by(Kolegij.id)
    paginacija = upit.paginate(page=page, per_page=per_page, error_out=False)

    if page > paginacija.pages and paginacija.pages > 0:
        paginacija = upit.paginate(page=paginacija.pages, per_page=per_page, error_out=False)

    return jsonify(
        {
            "items": [kolegij.to_dict() for kolegij in paginacija.items],
            "page": paginacija.page,
            "per_page": paginacija.per_page,
            "total": paginacija.total,
            "pages": paginacija.pages,
        }
    )


@app.route("/kolegiji-dropdown", methods=["GET"])
def kolegiji_dropdown():
    return jsonify(
        [
            {"title": kolegij.naziv, "value": kolegij.id}
            for kolegij in Kolegij.query.order_by(Kolegij.naziv).all()
        ]
    )


@app.route("/kolegiji/<int:item_id>", methods=["GET"])
def kolegij(item_id):
    kolegij, error = get_or_404(Kolegij, item_id, "Kolegij nije pronađen.")
    if error:
        return error

    return jsonify(kolegij.to_dict())


@app.route("/kolegiji", methods=["POST"])
def novi_kolegij_crud():
    data = request.get_json(silent=True) or {}

    if not data.get("naziv") or data.get("ects") is None:
        return jsonify({"message": "Naziv i ECTS su obavezni."}), 400

    kolegij = Kolegij(
        naziv=data.get("naziv"),
        ects=as_int(data.get("ects")),
        semestar=as_int(data.get("semestar")),
        nositelj_id=as_int(data.get("nositelj_id")),
    )

    db.session.add(kolegij)
    db.session.commit()

    return jsonify(kolegij.to_dict()), 201


@app.route("/kolegiji/<int:item_id>", methods=["PUT"])
def uredi_kolegij(item_id):
    kolegij, error = get_or_404(Kolegij, item_id, "Kolegij nije pronađen.")
    if error:
        return error

    data = request.get_json(silent=True) or {}
    if data.get("naziv") is not None:
        kolegij.naziv = data.get("naziv")
    if data.get("ects") is not None:
        kolegij.ects = as_int(data.get("ects"))
    kolegij.semestar = as_int(data.get("semestar"))
    kolegij.nositelj_id = as_int(data.get("nositelj_id"))

    db.session.commit()

    return jsonify(kolegij.to_dict())


@app.route("/kolegiji/<int:item_id>", methods=["DELETE"])
def izbrisi_kolegij(item_id):
    kolegij, error = get_or_404(Kolegij, item_id, "Kolegij nije pronađen.")
    if error:
        return error

    TerminNastave.query.filter_by(kolegij_id=kolegij.id).update({"kolegij_id": None})
    db.session.delete(kolegij)
    db.session.commit()

    return jsonify({"message": "Kolegij je obrisan."})


@app.route("/ucionice", methods=["GET"])
def ucionice():
    return jsonify([ucionica.to_dict() for ucionica in Ucionica.query.order_by(Ucionica.id).all()])


@app.route("/ucionice/<int:item_id>", methods=["GET"])
def ucionica(item_id):
    ucionica, error = get_or_404(Ucionica, item_id, "Učionica nije pronađena.")
    if error:
        return error

    return jsonify(ucionica.to_dict())


@app.route("/ucionice", methods=["POST"])
def nova_ucionica():
    data = request.get_json(silent=True) or {}

    if not data.get("oznaka") or data.get("kapacitet") is None:
        return jsonify({"message": "Oznaka i kapacitet su obavezni."}), 400

    ucionica = Ucionica(
        oznaka=data.get("oznaka"),
        kat=as_int(data.get("kat")),
        kapacitet=as_int(data.get("kapacitet")),
    )

    db.session.add(ucionica)
    db.session.commit()

    return jsonify(ucionica.to_dict()), 201


@app.route("/ucionice/<int:item_id>", methods=["PUT"])
def uredi_ucionicu(item_id):
    ucionica, error = get_or_404(Ucionica, item_id, "Učionica nije pronađena.")
    if error:
        return error

    data = request.get_json(silent=True) or {}
    if data.get("oznaka") is not None:
        ucionica.oznaka = data.get("oznaka")
    ucionica.kat = as_int(data.get("kat"))
    if data.get("kapacitet") is not None:
        ucionica.kapacitet = as_int(data.get("kapacitet"))

    db.session.commit()

    return jsonify(ucionica.to_dict())


@app.route("/ucionice/<int:item_id>", methods=["DELETE"])
def izbrisi_ucionicu(item_id):
    ucionica, error = get_or_404(Ucionica, item_id, "Učionica nije pronađena.")
    if error:
        return error

    db.session.delete(ucionica)
    db.session.commit()

    return jsonify({"message": "Učionica je obrisana."})


@app.route("/termini-nastave", methods=["GET"])
def termini_nastave():
    q = request.args.get("q", "", type=str).strip()
    upit = TerminNastave.query.outerjoin(Profesor, TerminNastave.profesor_id == Profesor.id).outerjoin(
        Kolegij, TerminNastave.kolegij_id == Kolegij.id
    )

    if q:
        pojam = f"%{q}%"
        upit = upit.filter(
            or_(
                TerminNastave.dan_u_tjednu.ilike(pojam),
                TerminNastave.vrijeme_pocetka.ilike(pojam),
                Profesor.ime.ilike(pojam),
                Profesor.prezime.ilike(pojam),
                Kolegij.naziv.ilike(pojam),
            )
        )

    return jsonify([termin.to_dict() for termin in upit.order_by(TerminNastave.id).all()])


@app.route("/termini-nastave/<int:item_id>", methods=["GET"])
def termin_nastave(item_id):
    termin, error = get_or_404(TerminNastave, item_id, "Termin nastave nije pronađen.")
    if error:
        return error

    return jsonify(termin.to_dict())


@app.route("/termini-nastave", methods=["POST"])
def novi_termin_nastave():
    data = request.get_json(silent=True) or {}

    if not data.get("dan_u_tjednu") or not data.get("vrijeme_pocetka") or data.get("trajanje") is None:
        return jsonify({"message": "Dan, vrijeme početka i trajanje su obavezni."}), 400

    termin = TerminNastave(
        dan_u_tjednu=data.get("dan_u_tjednu"),
        vrijeme_pocetka=data.get("vrijeme_pocetka"),
        trajanje=as_int(data.get("trajanje")),
        profesor_id=as_int(data.get("profesor_id")),
        kolegij_id=as_int(data.get("kolegij_id")),
    )

    db.session.add(termin)
    db.session.commit()

    return jsonify(termin.to_dict()), 201


@app.route("/termini-nastave/<int:item_id>", methods=["PUT"])
def uredi_termin_nastave(item_id):
    termin, error = get_or_404(TerminNastave, item_id, "Termin nastave nije pronađen.")
    if error:
        return error

    data = request.get_json(silent=True) or {}
    if data.get("dan_u_tjednu") is not None:
        termin.dan_u_tjednu = data.get("dan_u_tjednu")
    if data.get("vrijeme_pocetka") is not None:
        termin.vrijeme_pocetka = data.get("vrijeme_pocetka")
    if data.get("trajanje") is not None:
        termin.trajanje = as_int(data.get("trajanje"))
    termin.profesor_id = as_int(data.get("profesor_id"))
    termin.kolegij_id = as_int(data.get("kolegij_id"))

    db.session.commit()

    return jsonify(termin.to_dict())


@app.route("/termini-nastave/<int:item_id>", methods=["DELETE"])
def izbrisi_termin_nastave(item_id):
    termin, error = get_or_404(TerminNastave, item_id, "Termin nastave nije pronađen.")
    if error:
        return error

    db.session.delete(termin)
    db.session.commit()

    return jsonify({"message": "Termin nastave je obrisan."})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
