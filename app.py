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
    """Configuration ultra-robuste pour Railway"""
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1280x720")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.binary_location = "/usr/bin/chromium"

    service = Service(
        executable_path="/usr/bin/chromedriver",
        service_args=["--verbose", "--log-path=/tmp/chromedriver.log"]
    )
    
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(45)
    return driver

@app.route('/scrape', methods=['GET'])
def scrape_google_fr():
    """Version finale testée"""
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "Paramètre 'query' requis"}), 400

    driver = None
    try:
        driver = get_driver()
        driver.get(f"https://www.google.fr/search?q={query}&gl=fr")
        logging.info("Page chargée avec succès")

        # Vérification basique du contenu
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Sélecteur simplifié pour les résultats
        search_results = WebDriverWait(driver, 30).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.g"))
        )

        results = []
        for element in search_results[:10]:
            try:
                link = element.find_element(By.TAG_NAME, "a").get_attribute("href")
                title = element.find_element(By.TAG_NAME, "h3").text
                results.append({"title": title, "link": link})
            except Exception as e:
                logging.warning(f"Erreur élément: {str(e)}")

        return jsonify({"query": query, "results": results})

    except Exception as e:
        logging.error(f"ERREUR: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            "error": "Service temporairement indisponible",
            "code": 503
        }), 503

    finally:
        if driver:
            driver.quit()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)