from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import requests
import time

# Fonction pour analyser une page web
def analyze_page(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        # 1. Détecter le type de page
        if soup.find('article'):
            page_type = 'Article'
        elif soup.find('section') and 'service' in response.text.lower():
            page_type = 'Page de service'
        elif 'comparateur' in response.text.lower():
            page_type = 'Comparateur'
        else:
            page_type = 'Autre'

        # 2. Récupérer la structure HN (H1 et tous les H2)
        h1 = soup.find('h1').text.strip() if soup.find('h1') else "Aucun H1"
        h2s = [tag.text.strip() for tag in soup.find_all('h2')]

        headers = {
            'H1': h1,
            'H2': h2s
        }

        # 3. Compter le nombre de mots
        words = len(soup.get_text().split())

        # 4. Compter les liens internes et externes
        links = soup.find_all('a', href=True)
        internal_links = [link['href'] for link in links if url in link['href']]
        external_links = [link['href'] for link in links if url not in link['href']]

        # 5. Identifier les types de médias présents (images, vidéos, audio, vidéos embed)
        images = len(soup.find_all('img'))
        videos = len(soup.find_all('video'))
        audios = len(soup.find_all('audio'))
        embedded_videos = len(soup.find_all('iframe', src=lambda x: 'youtube' in x or 'vimeo' in x))

        return {
            'type': page_type,
            'headers': headers,
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


# Fonction pour scraper Google

def google_scraper():
    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--start-maximized")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    try:
        query = input("\n🔎 Entrez votre recherche Google : ")
        driver.get("https://www.google.fr")

        try:
            accept_button = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button#L2AGLb")))
            accept_button.click()
        except:
            pass

        search_box = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.NAME, "q")))
        search_box.send_keys(query + Keys.RETURN)

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.tF2Cxc")))
        time.sleep(2)

        results = driver.find_elements(By.CSS_SELECTOR, "div.tF2Cxc")[:10]

        print(f"\n🔎 Top 10 Google France pour : {query}\n")

        for i, result in enumerate(results, 1):
            try:
                title = result.find_element(By.CSS_SELECTOR, "h3").text
                link = result.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                domain = link.split("/")[2]  # Extraire le domaine

                analysis = analyze_page(link)

                print(f"{i}. \U0001F3E0 {domain}\n   🔗 {link}")
                print(f"   📝 Type : {analysis['type']}")
                print(f"   📰 Structure HN : {analysis['headers']}")
                print(f"   🔢 Nombre de mots : {analysis['word_count']}")
                print(f"   🔗 Liens internes : {analysis['internal_links']}, Liens externes : {analysis['external_links']}")
                print(f"   🎥 Médias : Images: {analysis['media']['images']}, Vidéos: {analysis['media']['videos']}, Audios: {analysis['media']['audios']}, Vidéos embed: {analysis['media']['embedded_videos']}\n")

            except Exception as e:
                print(f"⚠️ Erreur sur un résultat : {e}")

    except Exception as e:
        print(f"❌ Erreur : {e}")

    finally:
        driver.quit()


if __name__ == "__main__":
    google_scraper()
