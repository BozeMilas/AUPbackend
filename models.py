from extensions import db

class Profesor(db.Model):
    __tablename__ = "profesori"

    id = db.Column(db.Integer, primary_key=True)
    ime = db.Column(db.String(30), nullable=False) # Ctrl + D za duplicate retka
    prezime = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    titula = db.Column(db.String(20), nullable=True) # ovo polje ne moramo unositi

    # ovo je opcionalno sada, ali poželjno, da dodamo relaciju i s druge strane
    # u model Profesor dodajemo iduće:
    kolegiji = db.relationship("Kolegij", backref="nositelj", lazy=True)
    # za DZ istražite što je "lazy loading"

    def to_dict(self):
        return {
            "id": self.id,
            "ime": self.ime,
            "prezime": self.prezime,
            "email": self.email,
            "titula": self.titula
        }

class Kolegij(db.Model):
    __tablename__ = "kolegiji"

    id = db.Column(db.Integer, primary_key=True)
    naziv = db.Column(db.String(60), nullable=False)
    ects = db.Column(db.Integer, nullable=False)
    semestar = db.Column(db.Integer, nullable=True)

    nositelj_id = db.Column(db.Integer, db.ForeignKey("profesori.id"), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "naziv": self.naziv,
            "ects": self.ects,
            "semestar": self.semestar,
            "nositelj_id": self.nositelj_id,
            "nositelj_ime_prezime": f"{self.nositelj.ime} {self.nositelj.prezime}" if self.nositelj else ""
        }

class Ucionica(db.Model):
    __tablename__ = "ucionice"

    id = db.Column(db.Integer, primary_key=True)
    oznaka = db.Column(db.String(80), nullable=False)
    kat = db.Column(db.Integer, nullable=True)
    kapacitet = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "oznaka": self.oznaka,
            "kat": self.kat,
            "kapacitet": self.kapacitet
        }

class TerminNastave(db.Model):
    __tablename__ = "termini_nastave"

    id = db.Column(db.Integer, primary_key=True)
    dan_u_tjednu = db.Column(db.String(10), nullable=False)
    vrijeme_pocetka = db.Column(db.String(10), nullable=False)
    trajanje = db.Column(db.Integer, nullable=False)

    profesor_id = db.Column(db.Integer, db.ForeignKey("profesori.id"), nullable=True)
    kolegij_id = db.Column(db.Integer, db.ForeignKey("kolegiji.id"), nullable=True)

    profesor = db.relationship("Profesor", backref="termini_nastave", lazy=True)
    kolegij = db.relationship("Kolegij", backref="termini_nastave", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "dan_u_tjednu": self.dan_u_tjednu,
            "vrijeme_pocetka": self.vrijeme_pocetka,
            "trajanje": self.trajanje,
            "profesor_id": self.profesor_id,
            "kolegij_id": self.kolegij_id,
            "profesor_ime_prezime": f"{self.profesor.ime} {self.profesor.prezime}" if self.profesor else "",
            "kolegij_naziv": self.kolegij.naziv if self.kolegij else "",
        }


# U terminalu pokrenemo dvije naredbe:

# flask db migrate -m "napravljena tablica ucionice"
# flask db upgrade

# 3. zadatak
# napraviti klasu TerminNastave (tablice termini_nastave)
# dodati stupce id, dan_u_tjednu (string), vrijeme_pocetka (string), trajanje (integer)
# dodati strane ključeve na profesor_id i kolegij_id

