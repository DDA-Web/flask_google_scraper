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
    """Configuration spécifique pour la France"""
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_argument("--lang=fr-FR")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36 Edg/117.0.2045.60")
    chrome_options.binary_location = "/usr/bin/chromium"

    service = Service(executable_path="/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(25)
    return driver

@app.route('/scrape', methods=['GET'])
def scrape_google_fr():
    """Scraping Google France"""
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "Paramètre 'query' requis"}), 400

    driver = None
    try:
        driver = get_driver()
        driver.get(f"https://www.google.fr/search?q={query}&gl=fr&hl=fr")  # Forçage région FR
        
        # Gestion des cookies version française
        try:
            WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, '//button/div[contains(text(), "Tout accepter")]'))
            driver.find_element(By.XPATH, '//button/div[contains(text(), "Tout accepter")]').click()
            time.sleep(1)
        except Exception:
            logging.info("Pas de pop-up cookies")

        # Vérification de la localisation
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[aria-label="Résultats de recherche"]'))
        
        # Extraction des résultats
        results = []
        for element in driver.find_elements(By.CSS_SELECTOR, 'div.g, div.MjjYud')[:10]:
            try:
                title = element.find_element(By.CSS_SELECTOR, 'h3, span.VuuXrf').text
                link = element.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
                results.append({"title": title, "link": link})
            except Exception as e:
                logging.warning(f"Erreur élément: {str(e)}")
                continue

        return jsonify({"query": query, "results": results})

    except Exception as e:
        logging.error(f"ERREUR: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            "error": "Échec du scraping FR",
            "details": str(e),
            "stacktrace": traceback.format_exc()
        }), 500

    finally:
        if driver:
            driver.quit()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)