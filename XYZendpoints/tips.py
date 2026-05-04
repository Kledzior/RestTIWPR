import json
import re
import requests
import pprint  
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter(
    prefix="/tips",
    tags=["Tips"]
)

VACCINE_CACHE: Dict[str, Any] = {}
JSON_DB_FILENAME = "XYZData/cdc_data_EN.json" 

def load_vaccine_cache():
    print("[TIPS MODULE] Ładowanie cache szczepień...")
    try:
        with open(JSON_DB_FILENAME, "r", encoding="utf-8") as f:
            data = json.load(f)
            VACCINE_CACHE.update(data)
            print(f"[CACHE] Załadowano dane dla {len(VACCINE_CACHE)} krajów.")
            print(f"Przykładowe klucze w bazie: {list(VACCINE_CACHE.keys())[:5]}")
    except FileNotFoundError:
        print(f"[WARNING] Nie znaleziono pliku '{JSON_DB_FILENAME}'. Sprawdź ścieżkę!")

class VaccineInfo(BaseModel):
    disease: str
    recommendation: str

class HealthSource(BaseModel):
    source_name: str
    url: str
    vaccines: List[VaccineInfo]
    notes: Optional[str] = None
    last_updated: Optional[str] = None

class TravelHealthResponse(BaseModel):
    country: str
    advice: List[HealthSource]

def clean_slug(country_name: str) -> str:
    return country_name.strip().lower().replace(" ", "-")

def get_cached_cdc_advice(country_slug: str) -> Optional[HealthSource]:
    print(f"[CDC CACHE] Szukam klucza: '{country_slug}'")
    raw_data = VACCINE_CACHE.get(country_slug)
    
    if not raw_data: 
        print(f"[CDC CACHE] Brak danych dla klucza '{country_slug}'")
        return None

    print(f"[CDC CACHE] Znaleziono dane dla '{country_slug}'")
    
    vaccines_list = []
    for item in raw_data.get("data", []):
        vaccines_list.append(VaccineInfo(
            disease=item.get("disease", "Unknown"),
            recommendation=item.get("recommendation", "")
        ))

    return HealthSource(
        source_name="CDC (USA)",
        url=f"https://wwwnc.cdc.gov/travel/destinations/traveler/none/{country_slug}",
        vaccines=vaccines_list,
        notes=raw_data.get("note", "Dane zarchiwizowane (cache)."),
        last_updated=raw_data.get("last_updated", "N/A")
    )

@router.get("", response_model=TravelHealthResponse)
async def search_health_advice(
    q: str = Query(..., min_length=2, description="Nazwa kraju")
):
    print(f"\n---NOWE ZAPYTANIE: {q} ---")
    slug = clean_slug(q)
    combined_advice = []

    cdc_result = get_cached_cdc_advice(slug)
    if cdc_result: 
        combined_advice.append(cdc_result)
        print("\n--- DANE CDC (Raw Output) ---")
        pprint.pprint(cdc_result.dict())

    
    if not combined_advice:
        raise HTTPException(status_code=404, detail=f"Nie znaleziono porad dla kraju: {q}.")

    return TravelHealthResponse(country=q, advice=combined_advice)