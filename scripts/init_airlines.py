import sys
import os
import json
from sqlalchemy.orm import Session


current_script_path = os.path.abspath(__file__)

scripts_dir = os.path.dirname(current_script_path)

project_root = os.path.dirname(scripts_dir)


if project_root not in sys.path:
    sys.path.append(project_root)

from models import Airline

def init_airlines(db: Session):
    json_path = os.path.join(project_root, "XYZData", "fallback_rules.json") 
    
    if not os.path.exists(json_path):
        print(f"Błąd: Nie znaleziono pliku: {json_path}")
        
        print(f"   Szukana ścieżka absolutna: {json_path}")
        return

    print(f"Wczytuję reguły bagażowe z: {json_path}")

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Błąd odczytu JSON: {e}")
        return

    print(f"Weryfikacja {len(data)} linii w bazie SQL...")

    new_airlines_count = 0
    for iata_code, airline_data in data.items():
        
        airline = db.query(Airline).filter(Airline.iata_code == iata_code).first()
        
        if not airline:
            airline = Airline(
                name=airline_data["name"],
                iata_code=iata_code,
                source="fallback"
            )
            db.add(airline)
            new_airlines_count += 1
        
    db.commit()
    
    if new_airlines_count > 0:
        print(f"Dodano {new_airlines_count} nowych linii do bazy SQL.")
    else:
        print("Wszystkie linie już istnieją w SQL. Brak zmian.")