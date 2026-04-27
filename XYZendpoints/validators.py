from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from auth import get_current_user 
from datetime import datetime, timezone


def validate_trip_dates(start_date: datetime, end_date: datetime) -> tuple[datetime, datetime]:
    now_utc = datetime.now(timezone.utc)

    if start_date.tzinfo is None:
        start_utc = start_date.replace(tzinfo=timezone.utc)
    else:
        start_utc = start_date.astimezone(timezone.utc)
    
    if end_date.tzinfo is None:
        end_utc = end_date.replace(tzinfo=timezone.utc)
    else:
        end_utc = end_date.astimezone(timezone.utc)

    if start_utc < now_utc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nie można planować podróży w przeszłości!"
        )

    if end_utc < start_utc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Data powrotu nie może być wcześniejsza niż data wyjazdu!"
        )
    
    return start_utc, end_utc
