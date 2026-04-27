from fastapi import APIRouter, HTTPException
from services import baggage_rules 

router = APIRouter(
    prefix="/airline-rules",
    tags=["Airline Rules"] 
)

@router.get("/")
def get_all_airline_rules():
    return baggage_rules.get_rules()

@router.get("/check-baggage/{airline_code}")
def check_baggage_limits(airline_code: str):
    
    all_rules = baggage_rules.get_rules()
    
    code = airline_code.upper()
    
    if code in all_rules:
        return all_rules[code]
    
    raise HTTPException(status_code=404, detail=f"Airline {code} not found in fallback rules.")