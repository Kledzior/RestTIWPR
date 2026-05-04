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


@router.post("", response_model=schemas.User)
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

@router.get("/{user_id}", response_model=schemas.User)
def read_user(
    user_id: int, # <--- Dodajemy user_id z URL
    current_user: models.User = Depends(get_current_user)
):
    # Zabezpieczenie: czy ID z URL zgadza się z ID z tokena?
    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Brak uprawnień. Możesz pobrać tylko własny profil."
        )
        
    return current_user