import requests
import time
import threading
import logging
import os
from dotenv import load_dotenv

load_dotenv()


GIST_URL = os.getenv("GIST_URL")
REFRESH_INTERVAL = 3600

logger = logging.getLogger("RulesService")

_rules_cache = {}

def _fetch_from_gist():
    try:
        url = f"{GIST_URL}?t={int(time.time())}"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Błąd pobierania zasad bagażu: {e}")
        return None

def _background_worker():
    global _rules_cache
    logger.info("Uruchomiono wątek aktualizacji zasad bagażu.")
    
    while True:
        data = _fetch_from_gist()
        if data:
            _rules_cache = data
            logger.info("Cache zasad zaktualizowany.")
        
        time.sleep(REFRESH_INTERVAL)

def start_updater():
    thread = threading.Thread(target=_background_worker, daemon=True)
    thread.start()

def get_rules():
    if not _rules_cache:
        logger.warning("Cache pusty - wymuszam pobranie przy pierwszym zapytaniu.")
        data = _fetch_from_gist()
        if data:
            return data
        return {}
    return _rules_cache