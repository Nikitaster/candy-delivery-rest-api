from datetime import datetime
from typing import List
import re

from pydantic import BaseModel, Field, ValidationError, validator


class Courier(BaseModel):
    courier_id: int
    courier_type: str
    regions: List[int]
    working_hours: List[str]
    rating: float = 0
    earnings: float = 0

    @validator('working_hours')
    def working_hours_match(cls, v):
        for times in v:
            if not re.match('\d{2}:\d{2}-\d{2}:\d{2}', times):
                raise ValueError(times)
        return v

class CourierAssign(BaseModel):
    courier_id: int

class CouriersList(BaseModel):
    list_couriers: List[Courier] = Field(..., alias='data')

class Order(BaseModel):
    order_id: int
    courier_id: int = None
    weight: float = Field(..., ge=0.01, le=50)
    region: int
    delivery_hours: List[str]
    assign_time: datetime = None
    completed_at: datetime = None

    @validator('delivery_hours')
    def delivery_hours_match(cls, v):
        for times in v:
            if not re.match('\d{2}:\d{2}-\d{2}:\d{2}', times):
                raise ValueError(times)
        return v

class OrderComplete(BaseModel):
    order_id: int
    courier_id: int
    completed_at: datetime = Field(..., alias='complete_time')

class OrdersList(BaseModel):
    list_orders: List[Order] = Field(..., alias='data')
