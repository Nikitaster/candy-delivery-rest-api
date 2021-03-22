from fastapi import FastAPI, Response, status, Request
from fastapi.responses import JSONResponse

import databases

from sqlalchemy import MetaData, create_engine, Table, Column, Integer, String, ForeignKey, Float, ARRAY, TIMESTAMP
# from sqlalchemy.orm import relationship, mapper, session
from sqlalchemy.ext.declarative import declarative_base

from pydantic import BaseModel, Field
from typing import List, Dict
from datetime import datetime

DATABASE_URL = "postgresql://postgres:postgres@db:5432/candy_delivery_db"


database = databases.Database(DATABASE_URL)

metadata = MetaData()

couriers_types_model = Table(
    'couriers_types', 
    metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String(16), nullable=False),
    Column('weight', Float, nullable=False),
)


couriers_model = Table(
    'couriers',
    metadata,

    Column('courier_id', Integer, primary_key=True),
    Column('courier_type', Integer, ForeignKey('couriers_types.id'), nullable=False),
    # Column('courier_type', String, nullable=False),
    Column('regions', ARRAY(Integer)),
    Column('working_hours', ARRAY(String)),
    Column('rating', Float, nullable=True),
    Column('earnings', Float, nullable=True),

    # type = relationship('CouriersType')
    # orders = relationship('Orders', back_populates='courier')
)


orders_model = Table(
    'orders',
    metadata,
    
    Column('id', Integer, primary_key=True),
    Column('courier_id', Integer, ForeignKey('couriers.courier_id'), nullable=False),
    Column('weight', Float, nullable=False),
    Column('region', Integer, nullable=False),
    Column('delivery_hours', ARRAY(String)),
    Column('assign_time', TIMESTAMP, nullable=True),
    Column('completed_at', TIMESTAMP, nullable=True),

    # courier = relationship('Couriers', back_populates='orders')
)

engine = create_engine(DATABASE_URL)
metadata.create_all(engine)

class Couriers(BaseModel):
    courier_id: int = None
    courier_type: str = None
    regions: List[int] = []
    working_hours: List[str] = []
    rating: float = None
    earnings: float = None

class Orders(BaseModel):
    # id: int
    courier_id: int
    weight: float
    region: int
    delivery_hours: List[str]
    assign_time: datetime = None
    completed_at: datetime = None

app = FastAPI()


@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

@app.get("/")
async def root():
    # query = notes.insert().values(text='123', completed=True)
    # last_record_id = await database.execute(query)
    query = couriers_model.select().where(couriers_model.c.courier_id == 10)
    # query = couriers_types_model.select().where(couriers_types_model.c.name == 'foot')
    a = await database.fetch_all(query)
    if a:
        return 1
    else:
        return 0
    return {"message": "Hello World"}


@app.post("/couriers")
async def root(request: Request):
    data = await request.json()
    couriers = list(data['data'])

    errs = []
    query_values = []
    successful = []

    for courier in couriers:        
        if not {'courier_id', 'courier_type', 'regions', 'working_hours'}.issubset(set(courier.keys())):
            errs.append({'id': courier['courier_id']})
        else:
            courier_type = await database.fetch_one(
                couriers_types_model.select().where(
                    couriers_types_model.c.name == courier['courier_type']
                    )
                )
            courier['courier_type'] = courier_type['id']
            query_values.append(dict(courier))
            successful.append({'id': courier['courier_id']})

    if errs:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={'validation_error': {'couriers':errs}})

    try:
        await database.execute_many(couriers_model.insert(), values=query_values)
    except Exception as ex:
        # есть гарантия, что courier_id всегда уникальны
        print(ex)

    return JSONResponse(status_code=status.HTTP_201_CREATED, content={'couriers':successful})