FROM python:3.10-slim

# Installer les dépendances système nécessaires pour Chromium
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    xvfb \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

# Définir la variable d'environnement pour Chrome
ENV DISPLAY=:99
ENV CHROME_BIN=/usr/bin/chromium

EXPOSE 8000

CMD ["gunicorn", "-b", "0.0.0.0:8000", "--timeout", "120", "app:app"]