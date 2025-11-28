from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Association table disease <-> symptom
disease_symptom = db.Table(
    "disease_symptom",
    db.Column("disease_id", db.Integer, db.ForeignKey("diseases.id"), primary_key=True),
    db.Column("symptom_id", db.Integer, db.ForeignKey("symptoms.id"), primary_key=True)
)

class Disease(db.Model):
    __tablename__ = "diseases"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)
    treatments = db.Column(db.Text)       # JSON-encoded list string or comma-separated
    explanation = db.Column(db.Text)
    symptoms = db.relationship("Symptom", secondary=disease_symptom, back_populates="diseases")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "symptoms": [s.name for s in self.symptoms],
            "treatments": eval(self.treatments) if self.treatments else [],
            "explanation": self.explanation or ""
        }

class Symptom(db.Model):
    __tablename__ = "symptoms"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)
    diseases = db.relationship("Disease", secondary=disease_symptom, back_populates="symptoms")

    def to_dict(self):
        return {"id": self.id, "name": self.name}
