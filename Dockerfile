FROM python:3.10-slim

# 1. Installer Chromium + Driver (versions synchronisées)
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# 2. Configuration de l'app
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Exposer le port
EXPOSE 8000

# 4. Lancer l'API
CMD ["gunicorn", "-b", "0.0.0.0:8000", "--timeout", "120", "app:app"]