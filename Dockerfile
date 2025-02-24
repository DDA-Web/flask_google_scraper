FROM python:3.10-slim

# 1. Installer les dépendances système
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    --no-install-recommends

# 2. Installer Chrome et ChromeDriver (versions fixes)
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update -y \
    && apt-get install -y \
    google-chrome-stable=114.0.5735.198-1 \
    --no-install-recommends \
    && wget https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_linux64.zip \
    && unzip chromedriver_linux64.zip \
    && mv chromedriver /usr/bin/chromedriver \
    && chmod +x /usr/bin/chromedriver \
    && rm chromedriver_linux64.zip \
    && rm -rf /var/lib/apt/lists/*

# 3. Configuration de l'environnement
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000
CMD ["gunicorn", "-b", "0.0.0.0:8000", "--timeout", "120", "app:app"]