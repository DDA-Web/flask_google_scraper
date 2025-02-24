from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import requests
import time
import logging

app = Flask(__name__)

# Configuration du logging
logging.basicConfig(level=logging.INFO)

# Chemins fixes (DO NOT MODIFY)
CHROME_PATH = '/usr/bin/google-chrome'
CHROME_DRIVER_PATH = '/usr/bin/chromedriver'

def analyze_page(url):
    [...]  # (Identique à la version précédente)

@app.route('/scrape', methods=['GET'])
def scrape_google():
    """Endpoint pour scraper les résultats Google"""
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "Paramètre 'query' manquant"}), 400

    driver = None
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.binary_location = CHROME_PATH

        # Configuration explicite sans webdriver-manager
        service = Service(executable_path=CHROME_DRIVER_PATH)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(30)

        [...]  # (Le reste identique à la version précédente)

    except Exception as e:
        logging.error(f"Erreur générale: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)