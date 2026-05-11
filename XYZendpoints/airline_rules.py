from fastapi import APIRouter
from services import baggage_rules 

router = APIRouter(
    prefix="/airline-rules",
    tags=["Airline Rules"] 
)

@router.get("/")
def get_all_airline_rules():
    return baggage_rules.get_rules()

