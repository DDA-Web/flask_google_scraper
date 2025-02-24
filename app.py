from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

def get_driver():
    """Configuration optimisée du navigateur Chromium"""
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.binary_location = "/usr/bin/chromium"  # Chemin officiel Debian

    service = Service(executable_path="/usr/bin/chromedriver")  # Chemin driver système
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(15)
    return driver

@app.route('/scrape', methods=['GET'])
def scrape_google():
    """Endpoint principal de scraping"""
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "Le paramètre 'query' est obligatoire"}), 400

    driver = None
    try:
        driver = get_driver()
        driver.get(f"https://www.google.com/search?q={query}")

        # Gestion des cookies (sélecteur international)
        try:
            cookie_btn = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, '//button[contains(., "Tout accepter") or contains(., "Accept all")]'))
            )
            cookie_btn.click()
            time.sleep(1)
        except Exception:
            logging.info("Aucun pop-up cookies détecté")

        # Attente des résultats
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.g"))  # Sélecteur historique Google
        )

        # Extraction des données
        results = []
        for item in driver.find_elements(By.CSS_SELECTOR, "div.g")[:10]:
            try:
                title = item.find_element(By.CSS_SELECTOR, "h3").text
                link = item.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                results.append({"title": title, "link": link})
            except Exception as e:
                logging.warning(f"Élément ignoré : {str(e)}")
                continue

        return jsonify({"query": query, "results": results})

    except Exception as e:
        logging.error(f"ÉCHEC CRITIQUE : {str(e)}")
        return jsonify({"error": "Erreur lors du scraping"}), 500

    finally:
        if driver:
            driver.quit()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)