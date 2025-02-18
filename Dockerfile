# Utiliser une image Python légère
FROM python:3.10-slim

# Installer Chromium et son driver
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Créer un dossier de travail
WORKDIR /app

# Copier ton code dans /app
COPY . /app

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Exposer le port 8000 (Railway mappe ce port automatiquement)
EXPOSE 8000

# Commande de démarrage : lancer Flask via Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:8000", "app:app"]
