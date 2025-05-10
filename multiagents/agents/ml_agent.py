import joblib
import os

MODEL_PATH = os.path.join(os.path.dirname(__file__), '../../ml/model.pkl')
model = joblib.load(MODEL_PATH)

def detect(text):
    # Zakładamy, że to pipeline zwracający etykiety
    if isinstance(text, str):
        text = [text]
    return model.predict(text).tolist()
