FROM python:3.10-slim

# Installer Chromium 117 + Chromedriver 117.0.5938.0 (versions verrouillées)
RUN apt-get update && apt-get install -y \
    chromium=117.0.5938.92-1~deb12u1 \
    chromium-driver=117.0.5938.92-1~deb12u1 \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000
CMD ["gunicorn", "-b", "0.0.0.0:8000", "--timeout", "120", "app:app"]