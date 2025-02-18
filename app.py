from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import os

app = Flask(__name__)

# 🔹 Configuration de Selenium avec la bonne version de ChromeDriver
def get_chrome_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")  # Mode headless
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # 🔹 Récupérer la version de Chromium installée
    chrome_version = os.popen("chromium --version").read().strip().split()[-1].split('.')[0]

    # 🔹 Télécharger la version correcte de ChromeDriver
    chromedriver_path = ChromeDriverManager(version=f"{chrome_version}").install()

    service = Service(chromedriver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    return driver


@app.route('/scrape', methods=['GET'])
def scrape_google():
    query = request.args.get("query")
    if not query:
        return jsonify({"error": "Missing 'query' parameter"}), 400

    driver = None
    try:
        print(f"✅ [DEBUG] Lancement du scraping pour la requête : {query}")
        driver = get_chrome_driver()
        driver.get("https://www.google.fr")

        # 🔹 Vérification du pop-up cookies
        try:
            accept_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button#L2AGLb"))
            )
            accept_button.click()
        except Exception:
            print("⚠️ [DEBUG] Pas de pop-up cookies ou erreur")

        # 🔹 Effectuer la recherche Google
        search_box = driver.find_element(By.NAME, "q")
        search_box.send_keys(query + Keys.RETURN)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.tF2Cxc"))
        )

        # 🔹 Extraire les résultats de recherche
        results = driver.find_elements(By.CSS_SELECTOR, "div.tF2Cxc")[:10]
        data = []
        for result in results:
            try:
                title = result.find_element(By.CSS_SELECTOR, "h3").text
                link = result.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                data.append({"title": title, "link": link})
            except Exception:
                continue

        return jsonify({"query": query, "results": data})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if driver:
            driver.quit()


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000)
