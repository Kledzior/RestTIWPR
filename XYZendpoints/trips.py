from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List

import models
import schemas
from database import get_db
from auth import get_current_user 
from datetime import datetime, timezone
from XYZendpoints.validators import validate_trip_dates
import weather_client 

IDEMPOTENCY_CACHE = {}

router = APIRouter(
    prefix="/trips",
    tags=["Trips"]
)

def check_lost_update(db_trip, if_match: str):
    if if_match:
        # ETag to po prostu ID
        if if_match != str(db_trip.id):
            raise HTTPException(
                status_code=status.HTTP_412_PRECONDITION_FAILED,
                detail="Precondition Failed: Zasób został zmodyfikowany przez kogoś innego."
            )
        
# 2. ZMIANA: Zagnieżdżenie pod trips
@router.post("/{trip_id}/packing-lists", response_model=schemas.PackingList)
def create_packing_list(
    trip_id: int,
    list_data: schemas.PackingListCreate,
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
    return new_list

def get_trip_data(
    trip_id: int,
    current_user: models.User,
    db: Session
) -> models.Trip:
    trip = db.query(models.Trip).filter(models.Trip.id == trip_id).first()

    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Podróż nie znaleziona"
        )
        
    if trip.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Brak uprawnień do tej podróży"
        )
        
    return trip



# DODATEK 1: Pobieranie wszystkich list dla konkretnej wycieczki (zgodne z tabelką: GET /trips/{trip_id}/packing-lists)
@router.get("/{trip_id}/packing-lists", response_model=List[schemas.PackingList])
def get_packing_lists_for_trip(
    trip_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Sprawdzamy czy wycieczka istnieje i należy do usera
    get_trip_data(trip_id, current_user, db)
    
    lists = db.query(models.PackingList).filter(models.PackingList.trip_id == trip_id).all()
    return lists

@router.post("/", response_model=schemas.Trip)
def create_trip_for_user(
    trip: schemas.TripCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    idempotency_key: str = Header(None, alias="Idempotency-Key") # POST once exactly
):
    if idempotency_key:
        if idempotency_key in IDEMPOTENCY_CACHE:
            print(f"Złapano duplikat! Zwracam wycieczkę dla klucza: {idempotency_key}")
            cached_trip_id = IDEMPOTENCY_CACHE[idempotency_key]
            # Sprawdzenie, czy wycieczka nie została już usunięta
            existing_trip = db.query(models.Trip).filter(models.Trip.id == cached_trip_id).first()
            if not existing_trip:
                raise HTTPException(
                    status_code=status.HTTP_410_GONE, # 410 Gone - idealny kod HTTP dla usuniętych zasobów!
                    detail="To żądanie (POST once exactly) zostało już przetworzone, ale utworzona wycieczka została w międzyczasie usunięta. (Ten idepodency key jest już w cache)"
                )
            return get_trip_data(cached_trip_id, current_user, db)
        print(f"Nowy klucz idepotencji w cache: {idempotency_key}")
    valid_start, valid_end = validate_trip_dates(trip.start_date, trip.end_date)

    
    dump_data = trip.model_dump(exclude={'source_trip_id'} if hasattr(trip, 'source_trip_id') else set())
    
    new_trip = models.Trip(
    **dump_data,
    user_id=current_user.id
    )


    new_trip.start_date = valid_start
    new_trip.end_date = valid_end

    db.add(new_trip)
    db.commit()
    db.refresh(new_trip)

    # Logika Klonowania (Zasób-kontroler)
    if hasattr(trip, 'source_trip_id') and trip.source_trip_id is not None:
        source_trip = get_trip_data(trip.source_trip_id, current_user, db)
        print(f"Klonowanie wycieczki ID: {source_trip.id}")
        old_lists = db.query(models.PackingList).filter(models.PackingList.trip_id == source_trip.id).all()
        for old_list in old_lists:
            new_list = models.PackingList(name=old_list.name, trip_id=new_trip.id)
            db.add(new_list)
            db.flush()
            old_items = db.query(models.PackingItem).filter(models.PackingItem.packing_list_id == old_list.id).all()
            for old_item in old_items:
                # Kopiujemy przedmioty (resetując status spakowania)
                new_item = models.PackingItem(
                    name=old_item.name,
                    category=old_item.category,
                    count=old_item.count,
                    weight_kg=old_item.weight_kg,
                    is_packed=False, # Nowa wycieczka = niespakowane przedmioty!
                    packing_list_id=new_list.id,
                    library_item_id=old_item.library_item_id
                )
                db.add(new_item)
    else:
        default_list = models.PackingList(
            name="Main Luggage",
            trip_id=new_trip.id
        )
        db.add(default_list)
    
    db.commit()
    db.refresh(new_trip) 
    if idempotency_key:
        IDEMPOTENCY_CACHE[idempotency_key] = new_trip.id
        print(f"Zapisano klucz {idempotency_key} do cache dla wycieczki {new_trip.id}")
    return new_trip

@router.delete("/{trip_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_trip(
    trip_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    trip = get_trip_data(trip_id, current_user, db)
    db.delete(trip)
    db.commit()
    return 

@router.get("/", response_model=list[schemas.Trip])
def get_users_trips(
    archive: bool = False,
    limit: int = Query(10, ge=1, description="Maksymalna liczba zwracanych wycieczek"),
    offset: int = Query(0, ge=0, description="Liczba wycieczek do pominięcia"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    now_utc = datetime.now(timezone.utc)
    
    query = db.query(models.Trip)

    query = query.filter(models.Trip.user_id == current_user.id)


    if archive:
        query = query.filter(models.Trip.end_date < now_utc)
        query = query.order_by(models.Trip.start_date.desc())

    else:
        query = query.filter(models.Trip.end_date >= now_utc)
        query = query.order_by(models.Trip.start_date.asc())
    query = query.limit(limit).offset(offset)

    
    return query.all()

@router.get("/{trip_id}", response_model=schemas.Trip)
def get_trip_details(
    trip_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    
    trip = get_trip_data(trip_id, current_user, db)
    return trip


@router.patch("/{trip_id}", response_model=schemas.Trip)
def update_trip(
    trip_id: int,
    trip_update: schemas.TripUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    if_match: str = Header(None, alias="If-Match")
):
    db_trip = get_trip_data(trip_id, current_user, db)

    check_lost_update(db_trip, if_match)

    temp_start = trip_update.start_date if trip_update.start_date else db_trip.start_date
    temp_end = trip_update.end_date if trip_update.end_date else db_trip.end_date

    valid_start, valid_end = validate_trip_dates(temp_start, temp_end)

    update_data = trip_update.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_trip, key, value)

    if trip_update.start_date:
         db_trip.start_date = valid_start
    if trip_update.end_date:
        db_trip.end_date = valid_end
        
    db.add(db_trip)
    db.commit()
    db.refresh(db_trip)

    return db_trip


@router.get("/{trip_id}/weather", response_model=schemas.WeatherResponse)
async def get_weather_for_trip(
    trip_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    
    trip = get_trip_data(trip_id, current_user, db) 
    
    coords = {
        "latitude": trip.destination_lat,
        "longitude": trip.destination_lon,
        "timezone": trip.destination_timezone
    }
    
    now_utc = datetime.now(timezone.utc)
    
    start_date_aware = trip.start_date.astimezone(timezone.utc)
    days_until_trip = (start_date_aware - now_utc).days
    

    is_forecast = days_until_trip <= 16
    weather_days = await weather_client.get_weather_data(
        coords, 
        trip.start_date, 
        trip.end_date,
        is_forecast=is_forecast,
        trip_id=trip_id
    )

    data_type = "Prognoza" if is_forecast else "Dane historyczne (średnia sprzed 5 lat)"
    summary = f"{data_type} dla {trip.destination_name}."
    
    return schemas.WeatherResponse(
        location=trip.destination_name,
        summary=summary,
        daily_forecast=weather_days
    )


@router.put("/{trip_id}", response_model=schemas.Trip)
def replace_trip(
    trip_id: int,
    trip_update: schemas.TripUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    if_match: str = Header(None, alias="If-Match")
):
    db_trip = get_trip_data(trip_id, current_user, db)
    
    check_lost_update(db_trip, if_match)

    update_data = trip_update.model_dump()
    
    for key, value in update_data.items():
        setattr(db_trip, key, value)
    
    valid_start, valid_end = validate_trip_dates(db_trip.start_date, db_trip.end_date)
    db_trip.start_date = valid_start
    db_trip.end_date = valid_end

    db.add(db_trip)
    db.commit()
    db.refresh(db_trip)
    return db_trip