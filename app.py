from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import logging
import traceback

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

def get_driver():
    """Configuration optimisée pour Railway"""
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1280x720")
    chrome_options.add_argument("--lang=fr-FR")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36")
    chrome_options.binary_location = "/usr/bin/chromium"

    service = Service(executable_path="/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(30)
    return driver

@app.route('/scrape', methods=['GET'])
def scrape_google_fr():
    """Version finale fonctionnelle"""
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "Paramètre 'query' requis"}), 400

    driver = None
    try:
        driver = get_driver()
        driver.get(f"https://www.google.fr/search?q={query}&gl=fr&hl=fr")

        # Gestion des cookies améliorée
        try:
            WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button#L2AGLb"))
            ).click()
            time.sleep(1)
        except Exception:
            logging.info("Pas de pop-up cookies")

        # Nouveau sélecteur principal
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div#search"))
        )

        # Attente supplémentaire pour les résultats
        time.sleep(2)

        # Extraction simplifiée
        results = []
        for element in driver.find_elements(By.CSS_SELECTOR, "div.g")[:10]:
            try:
                title = element.find_element(By.CSS_SELECTOR, "h3").text
                link = element.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                results.append({"title": title, "link": link})
            except Exception as e:
                logging.warning(f"Élément ignoré: {str(e)}")
                continue

        return jsonify({"query": query, "results": results})

    except Exception as e:
        logging.error(f"ERREUR: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            "error": "Impossible de récupérer les résultats",
            "details": "Essayez une requête plus spécifique"
        }), 500

    finally:
        if driver:
            driver.quit()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)