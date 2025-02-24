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
    """Configuration du navigateur headless"""
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.binary_location = "/usr/bin/chromium"
    
    service = Service(executable_path="/usr/bin/chromedriver")
    return webdriver.Chrome(service=service, options=chrome_options)

@app.route('/scrape', methods=['GET'])
def scrape_google():
    """Scrape les premiers résultats Google"""
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "Paramètre 'query' requis"}), 400
    
    driver = None
    try:
        driver = get_driver()
        driver.get("https://www.google.com")
        
        # Accepter les cookies (sélecteur européen)
        try:
            WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, '//button/div[contains(text(), "Tout accepter")]'))
            ).click()
        except Exception:
            logging.info("Pas de pop-up cookies")
        
        # Recherche
        search_box = driver.find_element(By.NAME, 'q')
        search_box.send_keys(query + webdriver.Keys.RETURN)
        
        # Collecte des résultats
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.g'))
        )
        
        results = []
        for element in driver.find_elements(By.CSS_SELECTOR, 'div.g')[:10]:
            try:
                title = element.find_element(By.CSS_SELECTOR, 'h3').text
                link = element.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
                results.append({"title": title, "link": link})
            except Exception as e:
                logging.warning(f"Erreur élément: {str(e)}")
        
        return jsonify({"query": query, "results": results})
    
    except Exception as e:
        logging.error(f"ERREUR: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
    finally:
        if driver:
            driver.quit()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)