from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

app = Flask(__name__)

@app.route('/scrape', methods=['GET'])
def scrape_google():
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "Veuillez fournir paramètre 'query'"}), 400

    # Config Selenium
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")

    # Forcer le chemin vers chromedriver
    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get("https://www.google.fr")
        time.sleep(2)

        # Tenter d'accepter le pop-up cookies
        try:
            accept_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button#L2AGLb"))
            )
            accept_btn.click()
        except:
            pass

        # Rechercher
        search_box = driver.find_element(By.NAME, "q")
        search_box.send_keys(query + Keys.RETURN)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.tF2Cxc"))
        )
        time.sleep(2)

        blocks = driver.find_elements(By.CSS_SELECTOR, "div.tF2Cxc")[:10]
        data = []
        for block in blocks:
            try:
                title = block.find_element(By.CSS_SELECTOR, "h3").text
                link = block.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                data.append({"title": title, "link": link})
            except:
                pass

        return jsonify({"query": query, "results": data})

    except Exception as e:
        return jsonify({"error": str(e)})
    finally:
        driver.quit()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
