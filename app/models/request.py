from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import date
from typing import Optional

class PackingRequest(BaseModel):

    airport_code: str = Field(..., min_length=3, max_length=3, pattern=r"^[A-Za-z]{3}$")
    arrival_date: date
    return_date: Optional[date] = None

    @field_validator('airport_code')
    @classmethod
    def validate_airport_code(cls, v: str) -> str:
        return v.upper()

    @model_validator(mode='after')
    def check_date_range(self) -> 'PackingRequest':
        if self.return_date and self.return_date < self.arrival_date:
            raise ValueError("Дата возврата (return_date) не может быть раньше даты прилета (arrival_date)")
        return self