from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import requests
import time
from bs4 import BeautifulSoup

app = Flask(__name__)

# ============
# FONCTION D'ANALYSE D'UNE PAGE
# ============
def analyze_page(url):
    """
    Récupère h1, h2, nombre de mots, etc.
    """
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Type de page
        if soup.find('article'):
            page_type = 'Article'
        elif soup.find('section') and 'service' in response.text.lower():
            page_type = 'Page de service'
        elif 'comparateur' in response.text.lower():
            page_type = 'Comparateur'
        else:
            page_type = 'Autre'

        # H1 + tous les H2
        h1 = soup.find('h1').text.strip() if soup.find('h1') else "Aucun H1"
        h2s = [tag.text.strip() for tag in soup.find_all('h2')]

        # Nombre de mots
        words = len(soup.get_text().split())

        # Liens internes/externes
        links = soup.find_all('a', href=True)
        internal_links = [link['href'] for link in links if url in link['href']]
        external_links = [link['href'] for link in links if url not in link['href']]

        # Médias
        images = len(soup.find_all('img'))
        videos = len(soup.find_all('video'))
        audios = len(soup.find_all('audio'))
        embedded_videos = len(soup.find_all('iframe', src=lambda x: x and ('youtube' in x or 'vimeo' in x))

        return {
            'type': page_type,
            'headers': {
                'H1': h1,
                'H2': h2s
            },
            'word_count': words,
            'internal_links': len(internal_links),
            'external_links': len(external_links),
            'media': {
                'images': images,
                'videos': videos,
                'audios': audios,
                'embedded_videos': embedded_videos
            }
        }

    except Exception as e:
        return {'error': str(e)}

# ============
# ROUTE FLASK : /scrape?query=...
# ============
@app.route('/scrape', methods=['GET'])
def scrape_google():
    """
    Ex: /scrape?query=seo+freelance
    """
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "Veuillez fournir un mot-clé."}), 400

    # ============
    # CONFIG SELENIUM
    # ============
    chrome_options = Options()
    chrome_options.add_argument("--headless")        # Mode sans interface
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Lance le navigateur Chrome
    driver = webdriver.Chrome(options=chrome_options)

    try:
        # Aller sur Google FR
        driver.get("https://www.google.fr")

        # Accepter cookies si pop-up
        try:
            accept_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button#L2AGLb"))
            )
            accept_btn.click()
        except:
            pass

        # Rechercher
        search_box = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.NAME, "q"))
        )
        search_box.send_keys(query + Keys.RETURN)

        # Attendre l'apparition des résultats
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.tF2Cxc"))
        )
        time.sleep(2)

        # Récupérer les 10 premiers résultats
        results = driver.find_elements(By.CSS_SELECTOR, "div.tF2Cxc")[:10]
        scraped_data = []

        for result in results:
            try:
                title = result.find_element(By.CSS_SELECTOR, "h3").text
                link = result.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                domain = link.split("/")[2]

                # Analyser le contenu de la page
                analysis = analyze_page(link)

                scraped_data.append({
                    "domain": domain,
                    "url": link,
                    "title": title,
                    "analysis": analysis
                })

            except Exception as e:
                print(f"⚠️ Erreur sur un résultat : {e}")

        return jsonify(scraped_data)

    except Exception as e:
        return jsonify({"error": str(e)})

    finally:
        driver.quit()

# ============
# MAIN
# ============
if __name__ == "__main__":
    # Pour test local seulement :
    # app.run(port=8000, debug=True)
    #
    # (Dans Docker ou Gunicorn, on n'utilise pas app.run)
    pass
