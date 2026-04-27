# import sys
# import os
# import time
# import json
# from datetime import datetime, timedelta

# sys.path.append(os.path.dirname(os.path.abspath(__file__)))
# from database import SessionLocal

# AIRLINE_HUBS = {
#     "FR": "STN", "W6": "LTN", "U2": "LGW", # Tanie linie (Londyn)
#     "LO": "WAW", "LH": "FRA", "BA": "LHR", "AF": "CDG", "KL": "AMS",
#     "LX": "ZRH", "OS": "VIE", "SK": "CPH", "AY": "HEL", "IB": "MAD",
#     "TP": "LIS", "AZ": "FCO", "QR": "DOH", "EK": "DXB",
#     "AA": "JFK", "DL": "ATL", "UA": "SFO", "DY": "OSL"
# }

# def run_smart_audit():
#     db = SessionLocal()
#     manager = BaggageManager(db)
    
#     results = {"FOUND": [], "EMPTY": [], "DETAILS": {}}
    
#     # Szukamy lotu za 90 dni (bezpieczny termin dla Sandboxa)
#     future_date = (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d')

#     print(f"🕵️  Rozpoczynam INTELIGENTNY audyt (Data: {future_date})...\n")

#     for iata, hub in AIRLINE_HUBS.items():
#         # Jeśli Hub to WAW, lecimy do LHR, w przeciwnym razie lecimy do WAW
#         dest = "LHR" if hub == "WAW" else "WAW"
        
#         print(f"✈️  {iata}: Szukam lotu {hub} -> {dest}...", end=" ")
        
#         try:
#             # Nadpisujemy logikę managera, żeby użyć konkretnego HUB-a
#             # (Normalnie manager bierze defaulty, tu wymuszamy poprawność)
#             response = manager.amadeus.shopping.flight_offers_search.get(
#                 originLocationCode=hub,
#                 destinationLocationCode=dest,
#                 departureDate=future_date,
#                 includedAirlineCodes=iata,
#                 adults=1,
#                 max=1
#             )
            
#             if not response.data:
#                 print("❌ BRAK LOTÓW")
#                 results["EMPTY"].append(iata)
#                 continue

#             # Parsowanie ręczne pierwszego segmentu
#             offer = response.data[0]
#             segment = offer['travelerPricings'][0]['fareDetailsBySegment'][0]
            
#             cabin = segment.get('includedCabinBags', {}).get('weight')
#             checked = segment.get('includedCheckedBags', {}).get('weight')
            
#             # Parsing Amenities (szukanie checked w tekście, bo często tam jest)
#             if not checked:
#                 for item in segment.get('amenities', []):
#                      if item.get('amenityType') == 'BAGGAGE' and 'CHECKED' in item.get('description', '').upper():
#                          import re
#                          match = re.search(r'(\d+)KG', item.get('description', '').upper())
#                          if match: checked = int(match.group(1))

#             print(f"✅ DANE: Cabin={cabin}, Checked={checked}")
#             results["FOUND"].append(iata)
#             results["DETAILS"][iata] = {"cabin": cabin, "checked": checked}

#         except Exception as e:
#             print(f"⚠️ BŁĄD: {e}")
#             results["EMPTY"].append(iata)
        
#         time.sleep(0.5)

#     print("\nRAPORT:")
#     print(f"Znaleziono: {len(results['FOUND'])}")
#     print(f"Pusto: {len(results['EMPTY'])}")
    
#     db.close()

# if __name__ == "__main__":
#     run_smart_audit()