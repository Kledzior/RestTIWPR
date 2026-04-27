import os
import time
from datetime import datetime, timedelta
from amadeus import Client, ResponseError
from dotenv import load_dotenv

load_dotenv()

amadeus = Client(
    client_id=os.getenv('AMADEUS_API_KEY'),
    client_secret=os.getenv('AMADEUS_API_SECRET')
)

airlines_to_test = [
    ("LO", "WAW"),
    ("LH", "FRA"), 
    ("BA", "LHR"), 
    ("AF", "CDG"), 
    ("KL", "AMS"), 
    ("LX", "ZRH"), 
    ("OS", "VIE"), 
    ("SK", "CPH"), 
    ("AY", "HEL"), 
    ("IB", "MAD"), 
    ("TP", "LIS"), 
    ("AZ", "FCO"), 
    ("AA", "JFK"), 
    ("DL", "JFK"), 
    ("UA", "EWR"), 
    ("QR", "DOH"), 
    ("EK", "DXB"), 

    ("W6", "LTN"), 
    ("FR", "STN"), 
    ("U2", "LGW"), 
    ("DY", "OSL"), 
]

def check_airline(code, origin):
    print(f"Sprawdzam linię: {code} (Baza: {origin})...", end=" ")
    
    try:
        future_date = (datetime.now() + timedelta(days=60)).strftime('%Y-%m-%d')
        
        dest = "LHR" if origin == "WAW" else "WAW"

        response = amadeus.shopping.flight_offers_search.get(
            originLocationCode=origin,
            destinationLocationCode=dest,
            departureDate=future_date,
            includedAirlineCodes=code,
            adults=1,
            max=1
        )

        if response.data:
            segment = response.data[0]['travelerPricings'][0]['fareDetailsBySegment'][0]
            cabin = segment.get('includedCabinBags', {})
            amenities = segment.get('amenities', [])
            
            has_weight = 'weight' in cabin
            has_checked_info = any(i['amenityType'] == 'BAGGAGE' for i in amenities)
            
            print(f"SUKCES!")
            return {
                "status": "OK",
                "cabin_weight_in_api": has_weight,
                "checked_info_found": has_checked_info
            }
        else:
            print(f"PUSTO (Brak lotów)")
            return {"status": "NO_FLIGHTS"}

    except ResponseError as error:
        print(f"BŁĄD API: {error.code}")
        if error.response:
            print(f"   [DETALE]: {error.response.body}")
        return {"status": "ERROR"}

print(f"--- ROZPOCZYNAM SKANOWANIE {len(airlines_to_test)} LINII ---\n")

results = []

for code, hub in airlines_to_test:
    res = check_airline(code, hub)
    results.append((code, res))
    time.sleep(0.5)

print("\n" + "="*40)
print("RAPORT DOSTĘPNOŚCI W SANDBOXIE")
print("="*40)
print(f"{'LINIA':<6} | {'STATUS':<12} | {'WAGA CABIN?':<12} | {'CHECKED INFO?'}")
print("-" * 45)

available_count = 0
for code, data in results:
    if data['status'] == "OK":
        available_count += 1
        waga = "TAK" if data['cabin_weight_in_api'] else "NIE"
        checked = "TAK" if data['checked_info_found'] else "NIE"
        print(f"{code:<6} | {data['status']:<12} | {waga:<12} | {checked}")
    else:
        print(f"{code:<6} | {data['status']:<12} | -            | -")

print("-" * 45)
print(f"Znaleziono dane dla {available_count} z {len(airlines_to_test)} linii.")