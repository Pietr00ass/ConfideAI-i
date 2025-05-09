
import joblib
import os

MODEL_PATH = os.path.join(os.path.dirname(__file__), '../../ml/model.pkl')
model = joblib.load(MODEL_PATH)

def detect_sensitive_ml(text):
    # assumes model is a sklearn/transformers pipeline
    if isinstance(text, str):
        text = [text]
    return model.predict(text).tolist()
