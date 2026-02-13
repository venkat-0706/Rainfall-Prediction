import os
import numpy as np
import pickle
import pandas as pd
from flask import Flask, request, render_template, jsonify

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_pickle(filename):
    path = os.path.join(BASE_DIR, "models", filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"{filename} not found in models folder.")
    with open(path, "rb") as f:
        return pickle.load(f)

model = load_pickle("rainfall.pkl")
scaler = load_pickle("scale.pkl")
imputer = load_pickle("impter.pkl")

trained_columns = list(scaler.feature_names_in_)

@app.route("/")
def home():
    return render_template("index.html")

def preprocess_input(data):
    df = pd.DataFrame([data])

    categorical_cols = ['RainToday', 'WindGustDir', 'WindDir9am', 'WindDir3pm']

    for col in categorical_cols:
        if col not in df.columns:
            df[col] = None

    cat_df = df[categorical_cols]
    imputed_cat = imputer.transform(cat_df)
    imputed_cat_df = pd.DataFrame(imputed_cat, columns=categorical_cols)

    df = df.drop(columns=categorical_cols)
    df = pd.concat([df, imputed_cat_df], axis=1)

    df = pd.get_dummies(df, drop_first=True)

    for col in trained_columns:
        if col not in df.columns:
            df[col] = 0

    df = df[trained_columns]
    df = df.apply(pd.to_numeric, errors="coerce").fillna(0).astype(np.float64)

    return scaler.transform(df)

def build_response(prediction, probability):
    if probability >= 75:
        risk = "High Risk"
    elif probability >= 40:
        risk = "Moderate Risk"
    else:
        risk = "Low Risk"

    return {
        "prediction": prediction,
        "probability": round(probability, 2),
        "risk_level": risk,
        "message": "Rain Expected 🌧" if prediction == 1 else "No Rain Today ☀️"
    }

@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json(force=True)

        if not isinstance(data, dict):
            return jsonify({"error": "Invalid input format"}), 400

        processed = preprocess_input(data)

        prediction = int(model.predict(processed)[0])

        if hasattr(model, "predict_proba"):
            probability = float(model.predict_proba(processed)[0][1] * 100)
        else:
            probability = float(prediction * 100)

        return jsonify(build_response(prediction, probability))

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/health")
def health():
    return jsonify({"status": "running", "model_loaded": True})

if __name__ == "__main__":
    app.run(debug=True)
