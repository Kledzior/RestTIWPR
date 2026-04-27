# from fastapi import APIRouter, Depends, HTTPException, status
# from sqlalchemy.orm import Session
# from typing import Optional, List

# import models
# import schemas
# from database import get_db
# from auth import get_current_user 

# router = APIRouter(
#     prefix="/library",
#     tags=["Item Library"] 
# )


# @router.get("/", response_model=List[schemas.LibraryItem])
# def get_library_items(
#     search: Optional[str] = None, 
#     category: Optional[str] = None,
#     db: Session = Depends(get_db),
#     current_user: models.User = Depends(get_current_user)
# ):
#     query = db.query(models.LibraryItem)
    
#     if search:
#         query = query.filter(models.LibraryItem.name.ilike(f"%{search}%"))
        
#     if category:
#         query = query.filter(models.LibraryItem.category == category)
    
#     query = query.order_by(models.LibraryItem.name.asc())
    
#     return query.all()


# @router.post("/", response_model=schemas.LibraryItem, status_code=status.HTTP_201_CREATED)
# def add_item_to_library(
#     item: schemas.LibraryItemCreate,
#     db: Session = Depends(get_db),
#     current_user: models.User = Depends(get_current_user)
# ):
#     exists = db.query(models.LibraryItem).filter(
#         models.LibraryItem.name.ilike(item.name)
#     ).first()
    
#     if exists:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Przedmiot o tej nazwie już istnieje w bibliotece."
#         )
        
#     new_library_item = models.LibraryItem(**item.model_dump())
    
#     db.add(new_library_item)
#     db.commit()
#     db.refresh(new_library_item)
    
#     return new_library_item