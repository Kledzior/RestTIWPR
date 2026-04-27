import os
from dotenv import load_dotenv

load_dotenv() 

SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = os.environ.get("ALGORITHM", "HS256") 
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

if SECRET_KEY is None:
    print("!!! BŁĄD KRYTYCZNY: Nie znaleziono SECRET_KEY w zmiennych środowiskowych.")
