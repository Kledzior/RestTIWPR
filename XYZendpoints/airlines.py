from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional

from database import get_db
import models
import schemas 

router = APIRouter(
    prefix="/airlines",
    tags=["Airlines"]
)

@router.get("/", response_model=List[schemas.AirlineResponse])
def get_airlines(search: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(models.Airline)

    if search:
        search_fmt = f"%{search}%"
        query = query.filter(
            or_(
                models.Airline.name.ilike(search_fmt),
                models.Airline.iata_code.ilike(search_fmt)
            )
        )
    
    airlines = query.order_by(models.Airline.name).all()
    
    return airlines