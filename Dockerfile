FROM python:3.10-slim

# Installer Chromium et son driver
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copier ton code
COPY . /app

# Installer dépendances Python (sans webdriver-manager !)
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

# Lancer Flask via Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:8000", "app:app"]
