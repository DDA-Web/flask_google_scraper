FROM python:3.10-slim

# Mettre à jour et installer Chromium et Chromium-driver
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    curl \
    gnupg \
    unzip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copier tous les fichiers du projet dans le conteneur
COPY . /app

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Exposer le port 8000
EXPOSE 8000

# Lancer l'application via Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:8000", "app:app"]
