from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import List

import models
import schemas
from database import get_db
from auth import get_current_user
from XYZendpoints.trips import get_trip_data

router = APIRouter(
    tags=["Packing Lists & Items"]
)

def get_item_data(
    item_id: int, 
    current_user: models.User, 
    db: Session
) -> models.PackingItem:
    item = db.query(models.PackingItem).filter(models.PackingItem.id == item_id).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
        
    if item.packing_list.trip.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this item")
        
    return item

@router.post("/trips/{trip_id}/packing-lists", response_model=schemas.PackingList, status_code=status.HTTP_201_CREATED)
def create_packing_list(
    trip_id: int,
    list_data: schemas.PackingListCreate,
    response: Response,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    get_trip_data(trip_id, current_user, db)
    
    new_list = models.PackingList(
        name=list_data.name,
        trip_id=trip_id
    )
    db.add(new_list)
    db.commit()
    db.refresh(new_list)
    response.headers["Location"] = f"/packing-lists/{new_list.id}"

    return new_list

@router.get("/trips/{trip_id}/packing-lists", response_model=List[schemas.PackingList])
def get_packing_lists_for_trip(
    trip_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    get_trip_data(trip_id, current_user, db)
    lists = db.query(models.PackingList).filter(models.PackingList.trip_id == trip_id).all()
    return lists

@router.get("/packing-lists/{list_id}", response_model=schemas.PackingList)
def get_single_packing_list(
    list_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    packing_list = db.query(models.PackingList).filter(models.PackingList.id == list_id).first()
    
    if not packing_list:
        raise HTTPException(status_code=404, detail="Packing List not found")
        
    if packing_list.trip.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    return packing_list

@router.delete("/packing-lists/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_packing_list(
    list_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    packing_list = db.query(models.PackingList).filter(models.PackingList.id == list_id).first()
    
    if not packing_list:
        raise HTTPException(status_code=404, detail="List not found")
        
    if packing_list.trip.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    db.delete(packing_list)
    db.commit()
    return

@router.post("/packing-lists/{list_id}/items", response_model=schemas.PackingItem, status_code=status.HTTP_201_CREATED)
def add_item_to_list(
    list_id: int,
    item: schemas.PackingItemCreate,
    response: Response,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    packing_list = db.query(models.PackingList).filter(models.PackingList.id == list_id).first()
    if not packing_list or packing_list.trip.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="List not found or unauthorized")

    new_item = models.PackingItem(
        **item.model_dump(exclude={'id', 'trip_id', 'packing_list_id'}), 
        packing_list_id=list_id
    )

    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    response.headers["Location"] = f"/items/{new_item.id}"
    return new_item

@router.get("/packing-lists/{list_id}/items", response_model=List[schemas.PackingItem])
def get_items_for_list(
    list_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    packing_list = db.query(models.PackingList).filter(models.PackingList.id == list_id).first()
    
    if not packing_list:
        raise HTTPException(status_code=404, detail="Packing List not found")
        
    if packing_list.trip.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    items = db.query(models.PackingItem).filter(models.PackingItem.packing_list_id == list_id).all()
    return items

@router.patch("/items/{item_id}", response_model=schemas.PackingItem)
def update_item(
    item_id: int,
    item_update: schemas.PackingItemUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_item = get_item_data(item_id, current_user, db) 
    update_data = item_update.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(db_item, key, value)
        
    db.commit()
    db.refresh(db_item)
    return db_item

@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_item = get_item_data(item_id, current_user, db)
    db.delete(db_item)
    db.commit()
    return