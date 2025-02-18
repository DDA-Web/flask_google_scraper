# Partir d'une image Python légère
FROM python:3.10-slim

# Installer quelques outils de base
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    unzip \
 && rm -rf /var/lib/apt/lists/*

# Installer Google Chrome
RUN curl -fsSL https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
 && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
 && apt-get update \
 && apt-get install -y google-chrome-stable

# Installer ChromeDriver (version correspondant à Chrome)
RUN CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d'.' -f1) \
 && LATEST_CHROMEDRIVER=$(curl -sS https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION}) \
 && curl -sS -o /tmp/chromedriver_linux64.zip https://chromedriver.storage.googleapis.com/${LATEST_CHROMEDRIVER}/chromedriver_linux64.zip \
 && unzip /tmp/chromedriver_linux64.zip -d /usr/local/bin/ \
 && chmod +x /usr/local/bin/chromedriver

# Définir le dossier de travail
WORKDIR /app

# Copier le code dans l'image
COPY . /app

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Exposer le port 8000 (Railway mappera ce port en externe)
EXPOSE 8000

# Lancer Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:8000", "app:app"]
