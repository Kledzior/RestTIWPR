import sys
import os

from sqlalchemy.orm import Session
from typing import List, Dict
import models
import schemas
import schemas_baggage
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class AirlineService:
    def __init__(self, db: Session):
        self.db = db

    def get_merged_baggage_info(self, airline_code: str) -> schemas_baggage.AirlineBaggageResponse:
        code = airline_code.upper().strip()
        
        airline = self.db.query(models.Airline).filter(models.Airline.iata_code == code).first()

        if not airline:
            return self._create_empty_response(code)

        variants = self._map_db_limits_to_tariffs(airline)

        composite = self._create_composite_tariff(variants)

        return schemas_baggage.AirlineBaggageResponse(
            airline_code=airline.iata_code,
            airline_name=airline.name,
            composite_tariff=composite,
            available_variants=variants
        )

    def _map_db_limits_to_tariffs(self, airline: models.Airline) -> List[schemas_baggage.TariffDTO]:
        if not airline.baggage_limits:
            return []

        grouped = {}

        for limit in airline.baggage_limits:
            t_name = limit.tariff_name or "Standard"
            
            if t_name not in grouped:
                grouped[t_name] = []

        
            dims = None
            if limit.max_length_cm and limit.max_width_cm:
                dims = f"{limit.max_length_cm}x{limit.max_width_cm}x{limit.max_height_cm}"

            
            item = schemas_baggage.BaggageItemDTO(
                type="cabin" if limit.is_cabin else "checked",
                weight_kg=limit.max_weight_kg,
                dimensions=dims,
                quantity=1,
                is_included=True,
                source=f"DB ({airline.source})"
            )
            grouped[t_name].append(item)

        
        results = []
        for name, items in grouped.items():
            results.append(schemas_baggage.TariffDTO(name=name, items=items))
        
        return results

    def _create_composite_tariff(self, variants: List[schemas_baggage.TariffDTO]) -> schemas_baggage.TariffDTO:
        composite_items = []
        
        found_cabin = False
        found_checked = False

        for variant in variants:
            for item in variant.items:
                if item.type == "cabin" and not found_cabin:
                    new_item = item.model_copy() 
                    new_item.source = "AUTO_COMPOSITE"
                    composite_items.append(new_item)
                    found_cabin = True
                
                if item.type == "checked" and not found_checked:
                    new_item = item.model_copy()
                    new_item.source = "AUTO_COMPOSITE"
                    composite_items.append(new_item)
                    found_checked = True
            
            if found_cabin and found_checked:
                break
        
        return schemas_baggage.TariffDTO(name="Sugerowana", items=composite_items)

    def _create_empty_response(self, code: str):
        return schemas_baggage.AirlineBaggageResponse(
            airline_code=code,
            airline_name=code,
            composite_tariff=schemas_baggage.TariffDTO(name="Brak danych", items=[]),
            available_variants=[]
        )