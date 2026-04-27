from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import models
import schemas
import auth
from database import get_db
from auth import get_current_user

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


@router.post("/create_user/", response_model=schemas.User)
def create_user(
    uzytkownik: schemas.UserCreate, 
    db: Session = Depends(get_db)
):
    
    db_user = db.query(models.User).filter(
        models.User.email == uzytkownik.email
    ).first()
    
    if db_user:
        raise HTTPException(
            status_code=400, 
            detail="Email już zarejestrowany"
        )

    hashed_password = auth.get_password_hash(uzytkownik.password)
    
    new_user = models.User(
        email=uzytkownik.email, 
        password_hash=hashed_password
    )
    
    db.add(new_user)
    db.commit()
    
    db.refresh(new_user)
 
    return new_user

@router.get("/me", response_model=schemas.User)
def read_users_me(
    current_user: models.User = Depends(get_current_user)
):
    return current_user