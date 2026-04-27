import sys
import os

sys.path.append(os.getcwd())

from database import engine, Base
import models  

def init_db():
    try:
        print("Łączenie z bazą danych (Supabase)...")
        print(f"   Używany Engine: {engine.url}")

        Base.metadata.create_all(bind=engine)
        
        print("SUKCES! Tabele zostały utworzone (lub już istniały).")
        print("Sprawdź teraz panel Supabase (Table Editor).")
        
    except Exception as e:
        print("BŁĄD! Nie udało się połączyć z bazą.")
        print(f"   Szczegóły błędu: {e}")

if __name__ == "__main__":
    init_db()