from fastapi import APIRouter, Depends, Query
from typing import List

import schemas
import weather_client 
from auth import get_current_user
import models

router = APIRouter(
    prefix="/locations",
    tags=["Locations"]
)

@router.get("", response_model=List[schemas.LocationSuggestion])
async def search_locations(
    q: str = Query(..., min_length=3, description="Fragment nazwy miejsca do wyszukania"),
    current_user: models.User = Depends(get_current_user)
):
    suggestions = await weather_client.get_coordinates(q)
    return suggestions