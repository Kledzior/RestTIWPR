from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime, date
from typing import List


class Token(BaseModel):
    access_token: str
    token_type: str

class UserCreate(BaseModel):
    email: EmailStr
    password: str


class User(BaseModel):
    id: int
    email: EmailStr

    class Config:
        from_attributes = True 
        

class AirlineBase(BaseModel):
    name: str

class AirlineResponse(AirlineBase):
    id: int
    iata_code: str
    last_updated: datetime

    class Config:
        from_attributes = True

class PackingItemBase(BaseModel):
    
    name: str
    category: str
    count: int = Field(ge=0)
    is_packed: bool

    weight_kg: Optional[float] = None
    library_item_id: Optional[int] = None

class PackingItemCreate(PackingItemBase):

    pass

class PackingItem(PackingItemBase):
    id: int

    class Config:
        from_attributes = True

class PackingItemUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    count: Optional[int] = Field(default=None, ge=0)

    is_packed: Optional[bool] = None
    
    weight_kg: Optional[float] = None


class PackingListBase(BaseModel):
    name: str

class PackingListCreate(PackingListBase):
    pass 

class PackingList(PackingListBase):
    id: int
    trip_id: int
    packing_items: List[PackingItem] = []

    class Config:
        from_attributes = True

class TripLocationBase(BaseModel):
    destination_name: str
    destination_lat: float
    destination_lon: float
    destination_timezone: str

class Trip(TripLocationBase):
    id: int
    start_date: datetime
    end_date: datetime
    user_id: int
    
    travel_with_pet: bool
    num_passengers: int = 1
    packing_lists: List[PackingList] = [] 
    airline: Optional[AirlineResponse]

    class Config:
        from_attributes = True

class TripCreate(TripLocationBase):

    start_date: datetime
    end_date: datetime
    airline_id: Optional[int] = None
    travel_with_pet: bool = Field(default=False)
    source_trip_id: Optional[int] = None


class TripUpdate(BaseModel):
    destination_name: Optional[str] = None
    destination_lat: Optional[float] = None
    destination_lon: Optional[float] = None
    destination_timezone: Optional[str] = None



    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    airline_id: Optional[int] = None
    travel_with_pet: Optional[bool] = None

class LocationSuggestion(BaseModel):
    name: str
    latitude: float
    longitude: float
    timezone: str


class HourlyWeatherPoint(BaseModel):
    time: str
    temp: float
    cloud_cover: int

class DailyWeather(BaseModel):
    date: date
    temp_max: float
    temp_min: float
    precipitation_mm: float
    avg_cloud_cover: float
    hourly_chart: List[HourlyWeatherPoint]

class WeatherResponse(BaseModel):
    location: str
    summary: str
    daily_forecast: List[DailyWeather]

    class Config:
        from_attributes = True
