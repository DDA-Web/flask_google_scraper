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
import json
import urllib.parse

def analyze_page(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        # 1. Détection du type de page (non affiché dans le top 10)
        if soup.find('article'):
            page_type = 'Article'
        elif soup.find('section') and 'service' in response.text.lower():
            page_type = 'Page de service'
        elif 'comparateur' in response.text.lower():
            page_type = 'Comparateur'
        else:
            page_type = 'Autre'

        # 2. Structure HN
        h1 = soup.find('h1').text.strip() if soup.find('h1') else "Aucun H1"
        h2s = [tag.get_text(strip=True) for tag in soup.find_all('h2')]
        headers = {'H1': h1, 'H2': h2s}

        # 3. Nombre de mots
        words = len(soup.get_text().split())

        # 4. Liens internes / externes
        links = soup.find_all('a', href=True)
        internal_links = [link['href'] for link in links if url in link['href']]
        external_links = [link['href'] for link in links if url not in link['href']]

        # 5. Médias
        images = len(soup.find_all('img'))
        videos = len(soup.find_all('video'))
        audios = len(soup.find_all('audio'))
        embedded_videos = len(soup.find_all('iframe', src=lambda x: x and ('youtube' in x or 'vimeo' in x)))

        # 6. Données structurées JSON-LD
        structured_data_types = []
        for script_tag in soup.find_all("script", type="application/ld+json"):
            try:
                json_data = json.loads(script_tag.string)
                if isinstance(json_data, list):
                    for item in json_data:
                        if isinstance(item, dict) and "@type" in item:
                            structured_data_types.append(item["@type"])
                elif isinstance(json_data, dict):
                    if "@type" in json_data:
                        structured_data_types.append(json_data["@type"])
            except Exception:
                continue

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
            },
            'structured_data_types': structured_data_types
        }
    except Exception as e:
        return {'error': str(e)}

def extract_videos_tbm(driver, query):
    """
    Ouvre la SERP avec le paramètre tbm=vid et extrait les vidéos.
    Renvoie une liste de dictionnaires {title, platform}.
    """
    encoded_query = urllib.parse.quote_plus(query)
    video_url = f"https://www.google.fr/search?q={encoded_query}&tbm=vid"
    driver.get(video_url)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.g")))
    time.sleep(1)
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    videos_list = []
    
    # Dans la page tbm=vid, les vidéos se trouvent souvent dans des blocs "div.g"
    video_blocks = soup.select("div.g")
    for block in video_blocks:
        title_elem = block.select_one("h3")
        if not title_elem:
            continue
        title = title_elem.get_text(strip=True)
        link_elem = block.select_one("a")
        if not link_elem or "href" not in link_elem.attrs:
            continue
        href = link_elem["href"]
        href_lower = href.lower()
        if "youtube.com" in href_lower:
            platform = "YouTube"
        elif "vimeo.com" in href_lower:
            platform = "Vimeo"
        elif "dailymotion.com" in href_lower:
            platform = "Dailymotion"
        elif "facebook.com" in href_lower:
            platform = "Facebook"
        elif "tiktok.com" in href_lower:
            platform = "TikTok"
        else:
            platform = "Autre"
        videos_list.append({"title": title, "platform": platform})
    
    return videos_list

def google_scraper():
    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--start-maximized")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    try:
        query = input("\n🔎 Entrez votre recherche Google : ")
        driver.get("https://www.google.fr")
        
        # Accepter les cookies
        try:
            accept_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button#L2AGLb"))
            )
            accept_button.click()
        except:
            pass

        # Requête principale (SERP "Tous")
        search_box = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.NAME, "q"))
        )
        search_box.send_keys(query + Keys.RETURN)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.tF2Cxc"))
        )
        time.sleep(1)
        organic_html = driver.page_source
        soup = BeautifulSoup(organic_html, 'html.parser')

        # --- Extraction PAA ---
        paa_questions = []
        question_spans = soup.select('span.CSkcDe')
        for span in question_spans:
            text = span.get_text(strip=True)
            if text:
                paa_questions.append(text)

        # --- Extraction Recherches associées ---
        assoc_elems = soup.select("div.y6Uyqe div.B2VR9.CJHX3e")
        associated_searches = [elem.get_text(strip=True) for elem in assoc_elems if elem.get_text(strip=True)]

        # --- Extraction du Top 10 organique ---
        results = soup.select("div.tF2Cxc")
        top_10_data = []
        for i, result in enumerate(results[:10], start=1):
            try:
                title_elem = result.select_one("h3")
                title = title_elem.get_text(strip=True) if title_elem else "Sans titre"
                link_elem = result.select_one("a")
                link = link_elem["href"] if link_elem else "#"
                domain = link.split("/")[2] if link.startswith("http") else "N/A"
                analysis = analyze_page(link)
                top_10_data.append({
                    "rank": i,
                    "domain": domain,
                    "link": link,
                    "title": title,
                    "analysis": analysis
                })
            except Exception as e:
                print(f"⚠️ Erreur sur un résultat organique : {e}")

        # --- Extraction des vidéos via tbm=vid ---
        videos_list = extract_videos_tbm(driver, query)
        videos_flag = "Oui" if videos_list else "Non"

        # --- Affichage ---
        print("\n##########################################")
        print("🔎 PAA (People Also Ask) :")
        if paa_questions:
            for idx, question in enumerate(paa_questions, start=1):
                print(f"{idx}. {question}")
        else:
            print("Aucune question PAA trouvée.")

        print("\n##########################################")
        print("🔎 Recherches associées :")
        if associated_searches:
            for search in associated_searches:
                print(f" - {search}")
        else:
            print("Aucune recherche associée trouvée.")

        print("\n##########################################")
        print(f"🔎 Vidéos : {videos_flag}")
        if videos_list:
            for i, vid in enumerate(videos_list, start=1):
                print(f"{i}. {vid['title']} - {vid['platform']}")

        print("\n##########################################")
        print(f"🔎 Top 10 Google France pour : {query}\n")
        for data in top_10_data:
            analysis = data["analysis"]
            print(f"{data['rank']}. \U0001F3E0 {data['domain']}\n   🔗 {data['link']}")
            print(f"   📝 Titre : {data['title']}")
            print(f"   📰 Structure HN : {analysis.get('headers', {})}")
            print(f"   🔢 Nombre de mots : {analysis.get('word_count', 'N/A')}")
            print(f"   🔗 Liens internes : {analysis.get('internal_links', 'N/A')}, "
                  f"Liens externes : {analysis.get('external_links', 'N/A')}")
            print(f"   🎥 Médias : Images: {analysis.get('media', {}).get('images', 0)}, "
                  f"Vidéos: {analysis.get('media', {}).get('videos', 0)}, "
                  f"Audios: {analysis.get('media', {}).get('audios', 0)}, "
                  f"Vidéos embed: {analysis.get('media', {}).get('embedded_videos', 0)}")
            structured_data = analysis.get('structured_data_types', [])
            print(f"   🗂️ Données structurées : {structured_data if structured_data else 'Aucune donnée structurée'}\n")

    except Exception as e:
        print(f"❌ Erreur : {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    google_scraper()
