import requests
import json
import time
import re
from bs4 import BeautifulSoup
from datetime import datetime

OUTPUT_FILENAME = "XYZData/cdc_data_EN.json"
BASE_URL = "https://wwwnc.cdc.gov"
LIST_URL = "https://wwwnc.cdc.gov/travel/destinations/list"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
}

def get_all_countries_slugs():
    print(f"Pobieram listę wszystkich krajów z: {LIST_URL}...")
    try:
        response = requests.get(LIST_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        slugs = []
        
        links = soup.find_all('a', href=True)
        
        for link in links:
            href = link['href']
            if "/travel/destinations/traveler/none/" in href:
                parts = href.strip("/").split("/")
                slug = parts[-1]
                
                if slug and slug not in slugs:
                    slugs.append(slug)
        
        print(f"Znaleziono {len(slugs)} krajów/terytoriów.")
        return slugs

    except Exception as e:
        print(f"Błąd podczas pobierania listy krajów: {e}")
        return []

def get_cdc_data_for_country(country_slug):
    url = f"https://wwwnc.cdc.gov/travel/destinations/traveler/none/{country_slug}"
    print(f"[{country_slug.upper()}] Pobieram dane...", end=" ")
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        
        if response.status_code != 200:
            print(f"Błąd HTTP {response.status_code}")
            return []

        soup = BeautifulSoup(response.content, 'html.parser')
        vaccines = []
        
        section_header = soup.find(string=re.compile("Vaccines and Medicines"))
        
        if section_header:
            table = section_header.find_next('table')
            if table:
                rows = table.find_all('tr')
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 2:
                        disease_name = cols[0].get_text(strip=True)
                        recommendation = cols[1].get_text(separator=" ", strip=True)
                        
                        disease_name = re.sub(r'\[.*?\]', '', disease_name)
                        recommendation = re.sub(r'\[.*?\]', '', recommendation)
                        
                        if len(recommendation) > 300:
                            recommendation = recommendation[:300] + "..."

                        if disease_name and recommendation:
                            vaccines.append({
                                "disease": disease_name,
                                "recommendation": recommendation
                            })
        
        if vaccines:
            print(f"OK ({len(vaccines)} wpisów)")
        else:
            print("Pusto/Bezpiecznie")
            
        return vaccines

    except Exception as e:
        print(f"Wyjątek: {e}")
        return []

def main():
    print("------------------------------------------------")
    print("   GENERATOR DANYCH ZDROWOTNYCH (CDC GLOBAL)    ")
    print("------------------------------------------------")
    
    countries_to_scrape = get_all_countries_slugs()
    
    if not countries_to_scrape:
        print("Nie udało się pobrać listy krajów. Przerywam.")
        return

    print(countries_to_scrape)
    
    database = {}
    timestamp = datetime.now().strftime("%Y-%m-%d")
    
    total = len(countries_to_scrape)
    
    for index, country in enumerate(countries_to_scrape):
        print(f"({index + 1}/{total}) ", end="")
        
        data = get_cdc_data_for_country(country)
        
        database[country] = {
            "source": "CDC (USA)",
            "last_updated": timestamp,
            "data": data if data else [],
            "note": "Dane pobrane automatycznie." if data else "Brak specyficznych zagrożeń lub błąd."
        }

        time.sleep(1.5) 

    print("\nZapisuję dane do pliku...")
    try:
        with open(OUTPUT_FILENAME, "w", encoding="utf-8") as f:
            json.dump(database, f, ensure_ascii=False, indent=2)
        print(f"GOTOWE Baza '{OUTPUT_FILENAME}' zawiera dane dla {len(database)} krajów.")
    except Exception as e:
        print(f"Błąd zapisu pliku: {e}")

if __name__ == "__main__":
    main()