import json
import requests
import os
from dotenv import load_dotenv

load_dotenv()
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

GIST_ID = os.getenv("GIST_ID")
GIST_PAT = os.getenv("GIST_PAT")
GIST_FILENAME = "airline_rules.json"

AMADEUS_FILE = os.path.join(PROJECT_ROOT, "XYZDATA", "amadeus.json")
FALLBACK_FILE = os.path.join(PROJECT_ROOT, "XYZDATA", "fallback_rules.json")

def deploy():
    print("Rozpoczynam łączenie danych w trybie APPEND...")

    combined_data = {}
    try:
        with open(FALLBACK_FILE, 'r', encoding='utf-8') as f:
            combined_data = json.load(f)
        print(f"Wczytano Fallback: {len(combined_data)} linii.")
    except FileNotFoundError:
        print(f"Nie znaleziono {FALLBACK_FILE}!")
        return
    
    if os.path.exists(AMADEUS_FILE):
        with open(AMADEUS_FILE, 'r', encoding='utf-8') as f:
            amadeus_data = json.load(f)
            
        print("Analizuję dane z Amadeusa i łączę z Fallbackiem...")
        
        updated_airlines = 0
        new_tariffs_count = 0
        
        for code, amadeus_entry in amadeus_data.items():
            if not amadeus_entry:
                continue
            
            new_tariffs = amadeus_entry.get("tariffs")
            if not isinstance(new_tariffs, list) or len(new_tariffs) == 0:
                continue

            if code not in combined_data:
                combined_data[code] = amadeus_entry
                updated_airlines += 1
            
            else:
                existing_entry = combined_data[code]
                existing_tariffs = existing_entry.get("tariffs", [])
                
                existing_names = {t["name"] for t in existing_tariffs}
                
                added_for_this_airline = False
                
                for tariff in new_tariffs:
                    if tariff["name"] not in existing_names:
                        existing_tariffs.append(tariff)
                        new_tariffs_count += 1
                        added_for_this_airline = True
                
                combined_data[code]["tariffs"] = existing_tariffs
                
                if added_for_this_airline:
                    updated_airlines += 1

        print(f"Zaktualizowano linii: {updated_airlines}")
        print(f"Łącznie dopisano nowych taryf: {new_tariffs_count}")
        
    else:
        print("Brak pliku Amadeus, wysyłam sam Fallback.")

    json_content = json.dumps(combined_data, indent=4, ensure_ascii=False)
    
    headers = {
        "Authorization": f"token {GIST_PAT}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    data = {
        "files": {
            GIST_FILENAME: {
                "content": json_content
            }
        }
    }

    print(f"Wysyłam dane na Gist ID: {GIST_ID}...")
    try:
        response = requests.patch(f"https://api.github.com/gists/{GIST_ID}", json=data, headers=headers)

        if response.status_code == 200:
            print("SUKCES! Dane zaktualizowane.")
            print(f"RAW URL: {response.json()['files'][GIST_FILENAME]['raw_url']}")
        else:
            print(f"Błąd wysyłania: {response.status_code}")
            print(response.text)
            print("Być może wygasł GIST_PAT")
    except Exception as e:
        print(f"Błąd połączenia: {e}")

if __name__ == "__main__":
    deploy()