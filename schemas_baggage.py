from pydantic import BaseModel
from typing import List, Optional

class BaggageItemDTO(BaseModel):
    type: str            
    weight_kg: Optional[float] = None
    dimensions: Optional[str] = None
    quantity: int = 1
    is_included: bool = True
    source: str          

class TariffDTO(BaseModel):
    name: str             
    items: List[BaggageItemDTO]

class AirlineBaggageResponse(BaseModel):
    airline_code: str
    airline_name: str
    composite_tariff: TariffDTO 
    available_variants: List[TariffDTO] = []