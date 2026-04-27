from fastapi import FastAPI, Depends, HTTPException, status
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import JWTError, jwt
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from scripts.init_airlines import init_airlines

import config
import models
import  schemas
import auth
from database import create_db_and_tables, get_db
from XYZendpoints import tips,trips, users, login, catalog, locations, packing_lists, airline_rules, airlines
from database import create_db_and_tables, get_db, SessionLocal
from services import baggage_rules

@asynccontextmanager
async def lifespan_fun(app: FastAPI):
    print("Aplikacja startuje...")
    try:
        
        create_db_and_tables()
        print("Tabele (jeśli nie istniały) zostały utworzone.")

        db = SessionLocal()
        try:
            print("Sprawdzanie i inicjalizacja linii lotniczych...")
            init_airlines(db)
        except Exception as e:
            print(f"Błąd podczas inicjalizacji linii lotniczych: {e}")
        finally:
            db.close()

        tips.load_vaccine_cache() 

        print("Uruchamianie serwisu zasad bagażowych (Gist)...")
        baggage_rules.start_updater()
        
    except Exception as e:
        print(f"Baza nie odpowiada przy starcie, ale uruchamianmy serwer mimo to: {e}")
    
    
    yield
    print("Aplikacja się zamyka...")

app = FastAPI(
    title="Aplikacja Podróżnicza API",
    description="Backend dla inżynierskiej aplikacji mobilnej wspierającej pakowanie.",
    version="1.0.0",
    lifespan=lifespan_fun
)

origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://10.0.2.2:8000", 
    "*",                    
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)


app.include_router(trips.router)
app.include_router(users.router)
app.include_router(login.router)
app.include_router(locations.router)
app.include_router(packing_lists.router)
app.include_router(tips.router)
app.include_router(airline_rules.router)
app.include_router(airlines.router)
# app.include_router(catalog.router)

@app.get("/")
def read_root(db: Session = Depends(get_db)):
    """
    NIE USUWAĆ! Ten endpoint pełni dwie funkcje:
    
    * **Szybki start:** Jest niezbędny do odpalania Rendera, bo jest lekki i szybko się ładuje.
    * **Keep-Alive:** Broni to przed zresetowaniem się Rendera jak i bazy Supabase.
    """

    try:
        db.execute(text("SELECT 1"))
        return {"Status": "Serwer i Baza działają!"}
    except Exception as e:
        return {"Status": "Serwer działa, ale Baza ma problem", "Error": str(e)}
