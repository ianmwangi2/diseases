# import os
# from flask import Flask, request, jsonify, send_from_directory
# from flask_cors import CORS
# from models import db, Disease, Symptom
# from flask import send_from_directory

# @app.route("/", defaults={"path": ""})
# @app.route("/<path:path>")
# def serve(path):
#     if path != "" and os.path.exists("build/" + path):
#         return send_from_directory("build", path)
#     else:
#         return send_from_directory("build", "index.html")

# def create_app():
#     app = Flask(__name__, instance_path=os.path.join(os.getcwd(), "instance"))
#     instance_path = os.path.join(app.root_path, 'instance')
#     if not os.path.exists(instance_path):
#         os.makedirs(instance_path)
#     app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(instance_path,'app.db')}"
#     app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#     db.init_app(app)
#     return app

# app = create_app()
# CORS(app)

# # severity weights
# SEVERITY_WEIGHTS = {"mild": 0.5, "moderate": 1.0, "severe": 1.5}

# @app.route("/health")
# def health():
#     return jsonify({"status": "ok"})

# @app.route("/symptoms", methods=["GET"])
# def get_symptoms():
#     syms = Symptom.query.order_by(Symptom.name).all()
#     return jsonify([s.to_dict() for s in syms])

# @app.route("/diseases", methods=["GET"])
# def get_diseases():
#     diseases = Disease.query.order_by(Disease.name).all()
#     return jsonify([d.to_dict() for d in diseases])

# @app.route("/diagnose", methods=["POST"])
# def diagnose():
#     """
#     Expect JSON body: { "symptoms": [ {"name": "fever", "severity": "severe"}, ... ] }
#     """
#     data = request.json or {}
#     user_symptoms = data.get("symptoms", [])
#     # normalize
#     user_symptoms_norm = []
#     for s in user_symptoms:
#         if not isinstance(s, dict):
#             continue
#         name = s.get("name", "").strip().lower()
#         severity = s.get("severity", "moderate").strip().lower()
#         if name:
#             if severity not in SEVERITY_WEIGHTS:
#                 severity = "moderate"
#             user_symptoms_norm.append({"name": name, "severity": severity})

#     if not user_symptoms_norm:
#         return jsonify({"error": "No symptoms provided"}), 400

#     results = []
#     diseases = Disease.query.all()

#     # prepare a map of symptom name -> weight for the user's input
#     user_weight_map = {s["name"]: SEVERITY_WEIGHTS.get(s["severity"], 1.0) for s in user_symptoms_norm}

#     for disease in diseases:
#         disease_symptoms = [s.name for s in disease.symptoms]
#         # compute matching
#         matched = []
#         match_score = 0.0
#         for ds in disease_symptoms:
#             ds_name = ds.lower()
#             w = user_weight_map.get(ds_name)
#             if w:
#                 matched.append({"name": ds_name, "weight": w})
#                 match_score += w

#         if not matched:
#             continue

#         # normalization: sum of ideal weights for disease symptoms (use 1.0 per symptom)
#         total_possible = float(len(disease_symptoms))  # each disease symptom counts as 1
#         match_percent = (match_score / total_possible) * 100.0

#         results.append({
#             "name": disease.name,
#             "matched_symptoms": [m["name"] for m in matched],
#             "match_percent": round(match_percent, 2),
#             "treatments": eval(disease.treatments) if disease.treatments else [],
#             "explanation": disease.explanation or ""
#         })

#     # sort by match percent desc
#     results = sorted(results, key=lambda x: x["match_percent"], reverse=True)[:10]
#     return jsonify(results)

# # if __name__ == "__main__":
# #     # create DB if not exists
# #     with app.app_context():
# #         db.create_all()
# #     app.run(debug=True)

# if __name__ == "__main__":
#     # Use 0.0.0.0 to allow external connections
#     # Use PORT from environment (needed by hosting platforms)
#     port = int(os.environ.get("PORT", 5000))
#     app.run(host="0.0.0.0", port=port)

import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from models import db, Disease, Symptom

# Severity weights for symptom scoring
SEVERITY_WEIGHTS = {"mild": 0.5, "moderate": 1.0, "severe": 1.5}


def create_app():
    """
    Factory function to create and configure the Flask app.
    """
    app = Flask(
        __name__,
        static_folder="build",  # Serve React build
        static_url_path="/"
    )

    # Ensure instance folder exists
    instance_path = os.path.join(app.root_path, 'instance')
    if not os.path.exists(instance_path):
        os.makedirs(instance_path)

    # SQLite database
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL',
        f"sqlite:///{os.path.join(instance_path, 'app.db')}"
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions
    db.init_app(app)
    CORS(app)

    # ----------------- ROUTES -----------------

    @app.route("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.route("/symptoms", methods=["GET"])
    def get_symptoms():
        syms = Symptom.query.order_by(Symptom.name).all()
        return jsonify([s.to_dict() for s in syms])

    @app.route("/diseases", methods=["GET"])
    def get_diseases():
        diseases = Disease.query.order_by(Disease.name).all()
        return jsonify([d.to_dict() for d in diseases])

    @app.route("/diagnose", methods=["POST"])
    def diagnose():
        data = request.json or {}
        user_symptoms = data.get("symptoms", [])

        # Normalize input
        user_symptoms_norm = []
        for s in user_symptoms:
            if not isinstance(s, dict):
                continue
            name = s.get("name", "").strip().lower()
            severity = s.get("severity", "moderate").strip().lower()
            if name:
                if severity not in SEVERITY_WEIGHTS:
                    severity = "moderate"
                user_symptoms_norm.append({"name": name, "severity": severity})

        if not user_symptoms_norm:
            return jsonify({"error": "No symptoms provided"}), 400

        user_weight_map = {s["name"]: SEVERITY_WEIGHTS[s["severity"]] for s in user_symptoms_norm}
        results = []

        # Compute disease matching
        diseases = Disease.query.all()
        for disease in diseases:
            disease_symptoms = [s.name.lower() for s in disease.symptoms]
            matched = []
            match_score = 0.0
            for ds_name in disease_symptoms:
                w = user_weight_map.get(ds_name)
                if w:
                    matched.append({"name": ds_name, "weight": w})
                    match_score += w

            if not matched:
                continue

            total_possible = float(len(disease_symptoms))
            match_percent = (match_score / total_possible) * 100.0

            results.append({
                "name": disease.name,
                "matched_symptoms": [m["name"] for m in matched],
                "match_percent": round(match_percent, 2),
                "treatments": eval(disease.treatments) if disease.treatments else [],
                "explanation": disease.explanation or ""
            })

        # Return top 10 matches
        results = sorted(results, key=lambda x: x["match_percent"], reverse=True)[:10]
        return jsonify(results)

    # Serve React frontend
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve(path):
        if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)
        else:
            return send_from_directory(app.static_folder, "index.html")

    return app


# ----------------- MAIN -----------------
if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()  # Ensure DB exists
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)  # debug=False in production
