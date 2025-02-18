FROM python:3.10-slim

# Installer Chromium et son driver
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Créer un dossier de travail
WORKDIR /app

# Copier ton code
COPY . /app

# Installer dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Exposer le port 8000 (Railway)
EXPOSE 8000

# Lancer l'app via Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:8000", "app:app"]
