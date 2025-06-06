# 1. Bazowy obraz Pythona
FROM python:3.12-slim

# 2. Zainstaluj narzędzia budowania i biblioteki systemowe dla OpenCV/spaCy
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      build-essential \
      python3-dev \
      libsm6 \
      libxext6 \
      libxrender1 \
      wget \
      git && \
    rm -rf /var/lib/apt/lists/*

# 3. Ustaw katalog roboczy
WORKDIR /app

# 4. Skopiuj requirements i zainstaluj je
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --only-binary=:all: -r requirements.txt

# 5. (Opcjonalnie) Jeśli chcesz, możesz pobrać model spaCy tak:
RUN python -m spacy download pl_core_news_sm

# 6. Skopiuj resztę kodu aplikacji
COPY . .

# 7. Utwórz katalog na uploady
RUN mkdir -p uploads

# 8. Zmienna środowiskowa portu (Railway używa $PORT)
ENV PORT=8000

# 9. Domyślna komenda uruchamiająca serwer
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
