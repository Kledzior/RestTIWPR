from datetime import datetime, timezone
from typing import List
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from database import Base 

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)


    trips = relationship("Trip", back_populates="user")

class Airline(Base):
    __tablename__ = "airlines"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    iata_code = Column(String(2), unique=True, index=True)

    icao_code = Column(String(3), unique=True, index=True)
    baggage_limits = relationship("BaggageLimit", back_populates="airline")
    trips = relationship("Trip", back_populates="airline")

    last_updated = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    source = Column(String)

class BaggageLimit(Base):
    __tablename__ = "baggage_limits"

    id = Column(Integer, primary_key=True, index=True)
    tariff_name = Column(String, index=True, nullable=True)
    
    max_weight_kg = Column(Float, nullable=True)
    max_length_cm = Column(Integer, nullable=True)
    max_width_cm = Column(Integer, nullable=True)
    max_height_cm = Column(Integer, nullable=True)

    is_cabin = Column(Boolean, default=False, nullable=False)
    
    airline_id = Column(Integer, ForeignKey("airlines.id"))
    airline = relationship("Airline", back_populates="baggage_limits")

class Trip(Base):
    __tablename__ = "trips"


    id = Column(Integer, primary_key=True, index=True)
    destination_name = Column(String, index=True)
    destination_lat = Column(Float)
    destination_lon = Column(Float)
    destination_timezone = Column(String)

    start_date = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True))  

    travel_with_pet = Column(Boolean, default=False)
    num_passengers = Column(Integer, default=1)

    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="trips") 

    airline_id = Column(Integer, ForeignKey("airlines.id"), nullable=True)
    airline = relationship("Airline", back_populates="trips")
    
    packing_lists = relationship("PackingList", back_populates="trip", cascade="all, delete-orphan")
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class PackingList(Base):
    __tablename__ = "packing_lists"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    trip_id = Column(Integer, ForeignKey("trips.id"))
    trip = relationship("Trip", back_populates="packing_lists")

    packing_items = relationship("PackingItem", back_populates="packing_list", cascade="all, delete-orphan")


class PackingItem(Base):
    __tablename__ = "packing_items"

    id = Column(Integer, primary_key=True, index=True)
    
    name = Column(String, index=True)    
    category = Column(String, index=True) 
    count = Column(Integer, default=1)
    is_packed = Column(Boolean, default=False)
    weight_kg = Column(Float, nullable=True)
    
    packing_list_id = Column(Integer, ForeignKey("packing_lists.id"))
    packing_list = relationship("PackingList", back_populates="packing_items")
    
    library_item_id = Column(Integer, ForeignKey("library_items.id"), nullable=True)
    library_item = relationship("LibraryItem", back_populates="packing_items") 

    
class LibraryItem(Base):
    __tablename__ = "library_items"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    category = Column(String, index=True)        
    default_weight_kg = Column(Float, nullable=True)
    
    packing_items = relationship("PackingItem", back_populates="library_item")


