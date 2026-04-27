import sys
import os
import json
import time
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv
from amadeus import Client, ResponseError

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
env_path = os.path.join(parent_dir, ".env")
load_dotenv(env_path)


OUTPUT_DIR = "XYZData"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "amadeus.json")

AIRLINE_HUBS = {
    "FR": "STN", "W6": "LTN", "U2": "LGW", 
    "LO": "WAW", "LH": "FRA", "BA": "LHR", "AF": "CDG", "KL": "AMS",
    "LX": "ZRH", "OS": "VIE", "SK": "CPH", "AY": "HEL", "IB": "MAD",
    "TP": "LIS", "AZ": "FCO", "QR": "DOH", "EK": "DXB",
    "AA": "JFK", "DL": "JFK", "UA": "EWR", "DY": "OSL"
}


AIRLINE_NAMES = {
    "FR": "Ryanair", "W6": "Wizz Air", "LO": "LOT Polish Airlines",
    "LH": "Lufthansa", "BA": "British Airways", "AF": "Air France",
    "KL": "KLM", "U2": "EasyJet", "QR": "Qatar Airways",
    "EK": "Emirates", "LX": "Swiss", "OS": "Austrian",
    "SK": "SAS", "AY": "Finnair", "IB": "Iberia",
    "TP": "TAP Air Portugal", "AZ": "ITA Airways",
    "AA": "American Airlines", "DL": "Delta",
    "UA": "United", "DY": "Norwegian"
}

def _parse_baggage_data(segment):
    """
    Parsuje segment Amadeusa i wyciąga wagę.
    Zwraca (cabin_kg, checked_kg, source_desc)
    """
    cabin_weight = 0
    checked_weight = 0
    debug_info = []


    chk_data = segment.get('includedCheckedBags', {})
    checked_weight = None

    if 'weight' in chk_data:
        checked_weight = chk_data['weight']
        debug_info.append(f"Checked:Weight({checked_weight})")
    
    elif chk_data.get('quantity') == 0:
        checked_weight = 0
        debug_info.append("Checked:Qty(0)->0kg")
        
    else:
        debug_info.append("Checked:NoExplicitWeight->TriggerFallback")

    cab_data = segment.get('includedCabinBags', {})
    if 'weight' in cab_data:
        cabin_weight = cab_data['weight']
        debug_info.append("Cabin:Weight")

    amenities = segment.get('amenities', [])
    for item in amenities:
        if item.get('amenityType') == 'BAGGAGE':
            desc = item.get('description', '').upper()
            
            match = re.search(r'(\d+)\s*KG', desc)
            if match:
                w = int(match.group(1))
                if "CHECKED" in desc and (checked_weight is None or checked_weight == 0):             
                    checked_weight = w
                    debug_info.append(f"Text:Checked({w})")
                elif ("CABIN" in desc or "HAND" in desc) and cabin_weight == 0:
                    cabin_weight = w
                    debug_info.append(f"Text:Cabin({w})")

    return cabin_weight, checked_weight, ", ".join(debug_info)

def generate_amadeus_json():
    try:
        amadeus = Client(
            client_id=os.getenv('AMADEUS_API_KEY'),
            client_secret=os.getenv('AMADEUS_API_SECRET')
        )
    except Exception as e:
        print("Błąd: Nie udało się połączyć z Amadeusem. Sprawdź .env!")
        print(f"Szczegóły: {e}")
        return

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    future_date = (datetime.now() + timedelta(days=60)).strftime('%Y-%m-%d')
    
    final_json = {}

    print(f"Rozpoczynam pobieranie danych do pliku {OUTPUT_FILE}...")
    print(f"Data wylotu: {future_date}\n")

    for iata, hub in AIRLINE_HUBS.items():
        dest = "LHR" if hub == "WAW" else "WAW"
        print(f"{iata} ({hub}->{dest}):", end=" ")

        if iata in ["U2", "FR"]: time.sleep(2)
        
        try:
            response = amadeus.shopping.flight_offers_search.get(
                originLocationCode=hub,
                destinationLocationCode=dest,
                departureDate=future_date,
                includedAirlineCodes=iata,
                adults=1,
                max=1
            )

            if not response.data:
                print("BRAK LOTU")
                continue

            offer = response.data[0]
            segment = offer['travelerPricings'][0]['fareDetailsBySegment'][0]
            cabin_kg, checked_kg, method = _parse_baggage_data(segment)

            cabin_class = segment.get('cabin', 'ECONOMY')
            
            tariff_name = f"Amadeus {cabin_class.capitalize()}"
            if checked_kg == 0:
                tariff_name += " Light/Basic"
            else:
                tariff_name += " Standard"

            print(f"{tariff_name} | C:{cabin_kg}kg / B:{checked_kg}kg [{method}]")

   
            
            tariffs = []
            
            if cabin_kg and cabin_kg > 0:
                tariffs.append({
                     "name": tariff_name + " (Cabin)",
                     "is_cabin": True,
                     "cabin_kg": cabin_kg,
                     "dims": "0x0x0"
                })
            
            if checked_kg and checked_kg > 0:
                tariffs.append({
                     "name": tariff_name + " (Checked)",
                     "is_cabin": False,
                     "checked_kg": checked_kg,
                     "dims": "158x0x0"
                })

            final_json[iata] = {
                "name": AIRLINE_NAMES.get(iata, iata),
                "source": "AMADEUS_API_EXPORT",
                "tariffs": tariffs
            }

        except ResponseError as error:
             print(f"API ERROR: {error}")
        except Exception as e:
            error_msg = str(e).split('\n')[0]
            print(f"BŁĄD: {error_msg}")

        time.sleep(0.5) 

    print("\nZapisywanie do pliku...")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_json, f, indent=4)
    
    print(f"Gotowe! Sprawdź: {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_amadeus_json()