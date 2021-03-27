from datetime import datetime
from typing import List

from pydantic import BaseModel, Field, ValidationError


class Courier(BaseModel):
    courier_id: int
    courier_type: str
    regions: List[int]
    working_hours: List[str]
    rating: float = 0
    earnings: float = 0

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

class OrderComplete(BaseModel):
    order_id: int
    courier_id: int
    completed_at: datetime = Field(..., alias='complete_time')

class OrdersList(BaseModel):
    list_orders: List[Order] = Field(..., alias='data')