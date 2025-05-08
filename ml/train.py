
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import joblib

texts = [
    "jan.kowalski@gmail.com", "48050112345", "1234 5678 9012 3456", "To nie jest wrażliwe"
]
labels = ["email", "pesel", "credit_card", "none"]

pipeline = make_pipeline(TfidfVectorizer(), LogisticRegression())
pipeline.fit(texts, labels)

joblib.dump(pipeline, "ml/model.pkl")
print("Model saved to ml/model.pkl")
