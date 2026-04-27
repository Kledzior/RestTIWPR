from amadeus import Client, ResponseError
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import re

load_dotenv()

def extract_baggage_options(segment):
    options = []
    
    cabin = segment.get('includedCabinBags', {})
    cabin_qty = cabin.get('quantity', 0)
    
    if cabin_qty > 0:
        weight = cabin.get('weight', None) 
            
        options.append({
            "type": "cabin",
            "name": "Bagaż podręczny (z API)",
            "limit_kg": weight, 
            "quantity": cabin_qty,
            "source": "API_STRUCTURAL"
        })

    amenities = segment.get('amenities', [])
    for item in amenities:
        if item.get('amenityType') == 'BAGGAGE':
            desc = item.get('description', '')
            is_chargeable = item.get('isChargeable', False)
            
            waga_match = re.search(r'(\d+)\s*KG', desc)
            waga = int(waga_match.group(1)) if waga_match else None
            
            options.append({
                "type": "checked",
                "name": desc,
                "limit_kg": waga,
                "is_included": not is_chargeable,
                "source": "API_TEXT_PARSER"
            })

    return options


amadeus = Client(
    client_id=os.getenv('AMADEUS_API_KEY'),
    client_secret=os.getenv('AMADEUS_API_SECRET')
)

try:
    future_date = (datetime.now() + timedelta(days=45)).strftime('%Y-%m-%d')
    
    print(f"Szukam surowych danych dla Wizz Air (W6) na trasie LTN->WAW ({future_date})...")

    response = amadeus.shopping.flight_offers_search.get(
        originLocationCode='LHR',
        destinationLocationCode='WAW',
        departureDate=future_date,
        includedAirlineCodes='W6',
        adults=1,
        max=1
    )

    if not response.data:
        print("Sandbox zwrócił pustą listę dla Wizz Air (norma w wersji darmowej).")
        print("Spróbuj zmienić includedAirlineCodes na 'LO' (LOT), żeby przetestować parser na jakichkolwiek danych.")
    else:
        offer = response.data[0]
        segment = offer['travelerPricings'][0]['fareDetailsBySegment'][0]

        print("\n--- WYNIKI ANALIZY (BEZ HARDCODINGU) ---\n")
        
        baggage_options = extract_baggage_options(segment)

        if not baggage_options:
            print("Parser nie znalazł żadnych informacji o bagażu w JSON-ie.")
        
        for opt in baggage_options:
            waga_str = f"{opt['limit_kg']} kg" if opt['limit_kg'] else "BRAK DANYCH W API"
            platnosc = "W CENIE" if opt.get('is_included', True) else "PŁATNE"
            
            print(f"Typ: {opt['type'].upper()}")
            print(f"Opis: {opt['name']}")
            print(f"Limit wagi: {waga_str}")
            print(f"Płatność: {platnosc}")
            print("-" * 30)
            
        print("\n[DOWÓD] Surowy JSON sekcji 'includedCabinBags':")
        print(json.dumps(segment.get('includedCabinBags'), indent=4))

except ResponseError as error:
    print(f"Błąd API: {error}")