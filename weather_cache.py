from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List, Type

CACHE_TTL_MINUTES = 30 
HISTORY_TTL_MINUTES = 60 * 24 * 365
MAX_CACHE_SIZE = 2048


TRIP_KEY_MAP: Dict[int, List[str]] = {}


WEATHER_CACHE: Dict[str, Dict[str, Any]] = {}


def invalidate_trip_cache(trip_id: int):
    if trip_id in TRIP_KEY_MAP:
        keys_to_delete = TRIP_KEY_MAP.pop(trip_id)
        
        deleted_count = 0
        for key in keys_to_delete:
            if key in WEATHER_CACHE:
                del WEATHER_CACHE[key]
                deleted_count += 1
        
        print(f"INFO: Cache inwalidowany dla Trip ID {trip_id}. Usunięto {deleted_count} wpisów.")
        return deleted_count
    
    print(f"INFO: Brak kluczy cache'u do usunięcia dla Trip ID {trip_id}.")
    return 0

def get_cache_key(latitude: float, longitude: float, start_date_iso: str, end_date_iso: str, is_forecast: bool) -> str:
    location_key = f"{round(latitude, 3)}_{round(longitude, 3)}"
    type_key = "FORECAST" if is_forecast else "HISTORY"
    
    return f"{location_key}_{start_date_iso}_{end_date_iso}_{type_key}"


def get_cached_weather(
    latitude: float, 
    longitude: float, 
    start_date: datetime, 
    end_date: datetime, 
    is_forecast: bool, 
    schema_type: Type[Any]
) -> Optional[List[Any]]:
    start_iso = start_date.strftime('%Y-%m-%d')
    end_iso = end_date.strftime('%Y-%m-%d')
    key = get_cache_key(latitude, longitude, start_iso, end_iso, is_forecast)
    
    cached_item = WEATHER_CACHE.get(key)
    
    if cached_item:
        ttl = cached_item.get("ttl_minutes", CACHE_TTL_MINUTES)
        expiry_time = cached_item["timestamp"] + timedelta(minutes=ttl)
        
        if expiry_time > datetime.now(timezone.utc):
            cached_data = WEATHER_CACHE.pop(key)
            WEATHER_CACHE[key] = cached_data
            time_left = expiry_time - datetime.now(timezone.utc)
            print(f"INFO: Cache hit. Zostało sekund: {time_left.total_seconds():.0f}")
            
            return [schema_type.model_validate(d) for d in cached_item["data"]]
        else:
            print(f"INFO: Cache wygasł dla klucza {key}. Usuwam.")
            del WEATHER_CACHE[key]
            
    return None

def set_cached_weather(
    latitude: float, 
    longitude: float, 
    start_date: datetime, 
    end_date: datetime, 
    is_forecast: bool, 
    data: List[Any],
    trip_id: Optional[int] = None 
):
    start_iso = start_date.strftime('%Y-%m-%d')
    end_iso = end_date.strftime('%Y-%m-%d')
    key = get_cache_key(latitude, longitude, start_iso, end_iso, is_forecast)
    
    
    new_ttl_minutes = HISTORY_TTL_MINUTES if not is_forecast else CACHE_TTL_MINUTES
    
    serialized_data = [item.model_dump() for item in data]


    if len(WEATHER_CACHE) >= MAX_CACHE_SIZE:
        oldest_key = next(iter(WEATHER_CACHE)) 
        del WEATHER_CACHE[oldest_key]
        print(f"INFO: LRU: Osiągnięto limit, usunięto najstarszy wpis: {oldest_key}")
    WEATHER_CACHE[key] = {
        "timestamp": datetime.now(timezone.utc),
        "data": serialized_data,
        "ttl_minutes": new_ttl_minutes 
        }
    

    if trip_id is not None and key not in TRIP_KEY_MAP.get(trip_id, []):
            TRIP_KEY_MAP.setdefault(trip_id, []).append(key)
            print(f"INFO: Zarejestrowano klucz {key} dla Trip ID: {trip_id}")

    print(f"INFO: Cache miss. Zapisano dane z TTL: {new_ttl_minutes} minut.")