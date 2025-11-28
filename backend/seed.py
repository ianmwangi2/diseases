"""
Seed script: load diseases.json into SQLite (app.db).
Run from the backend folder:
python seed.py
"""
import json
import os
from app import create_app
from models import db, Disease, Symptom

APP = create_app()
APP.app_context().push()

DB_PATH = os.path.join(os.path.dirname(__file__), 'instance')
if not os.path.exists(DB_PATH):
    os.makedirs(DB_PATH)

# recreate database
db.drop_all()
db.create_all()

with open("diseases.json", "r", encoding="utf-8") as f:
    data = json.load(f)

symptom_cache = {}

def get_or_create_symptom(name):
    key = name.strip().lower()
    if key in symptom_cache:
        return symptom_cache[key]
    s = Symptom.query.filter_by(name=key).first()
    if not s:
        s = Symptom(name=key)
        db.session.add(s)
        db.session.flush()
    symptom_cache[key] = s
    return s

for entry in data.get("diseases", []):
    name = entry.get("name")
    if not name:
        continue
    disease = Disease(name=name.strip())
    treatments = entry.get("treatments", [])
    # store treatments as python-list string for simple retrieval in to_dict
    disease.treatments = repr(treatments)
    disease.explanation = entry.get("explanation", "")
    db.session.add(disease)
    db.session.flush()

    for s in entry.get("symptoms", []):
        sym = get_or_create_symptom(s)
        disease.symptoms.append(sym)

db.session.commit()
print("Database seeded with diseases and symptoms.")
