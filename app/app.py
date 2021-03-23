import os

from fastapi import FastAPI, Response, status, Request
from fastapi.responses import JSONResponse

import databases

from sqlalchemy import MetaData, create_engine, Table, Column, Integer, String, ForeignKey, Float, ARRAY, TIMESTAMP
# from sqlalchemy.orm import relationship, mapper, session
from sqlalchemy.ext.declarative import declarative_base

from pydantic import BaseModel, Field, ValidationError
from typing import List, Dict
from datetime import datetime
import json

DATABASE_URL = "postgresql://{}:{}@db:5432/{}".format(
    os.getenv('POSTGRES_USER'), 
    os.getenv('POSTGRES_PASSWORD'), 
    os.getenv('POSTGRES_DB'),
)


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

class Courier(BaseModel):
    courier_id: int
    courier_type: str
    regions: List[int]
    working_hours: List[str]
    rating: float = None
    earnings: float = None

class CouriersList(BaseModel):
    list_couriers: List[Courier] = Field(..., alias='data')

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

async def get_couriers_types_dict():
    couriers_types_dict = dict()
    try:
        courier_types = await database.fetch_all(couriers_types_model.select())
        for t in courier_types:
            couriers_types_dict[t['name']] = t['id']
    except Exception as e:
        print(JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=e.json()))
    return couriers_types_dict

@app.post("/couriers")
async def couriers_create(request: Request) -> JSONResponse:
    data = await request.json()

    # сделать словарик, чтобы потом подставить значения ключа из таблицы couriers_types
    couriers_types_dict = await get_couriers_types_dict()
    
    query_values = []
    successful = []
    
    try:
        couriers = CouriersList.parse_obj(data)
        for courier in couriers.list_couriers:
            courier.courier_type = couriers_types_dict[str(courier.courier_type)]
            query_values.append(courier.dict())
            successful.append({'id': courier.courier_id})

    except ValidationError as errs:
        errs = json.loads(errs.json())
        msg = []
        for e in errs:
            index = e['loc'][1]
            msg.append({'id': data['data'][index]['courier_id']})
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={'validation_error': {'couriers':msg}})

    except KeyError as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={'validation_error': {'courier_type':e.args}})

    try:
        await database.execute_many(couriers_model.insert(), values=query_values)
        return JSONResponse(status_code=status.HTTP_201_CREATED, content={'couriers':successful})
    except Exception as errs:
        # есть гарантия, что courier_id всегда уникальны
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=errs.args)
    

@app.patch("/couriers/{courier_id}", response_model=Courier, response_model_exclude={'rating', 'earnings'})
async def couriers_edit(courier_id: int, request: Request) -> JSONResponse:
    request_json = await request.json()

    # сделать словарик, чтобы потом подставить значения ключа из таблицы couriers_types
    couriers_types_dict = await get_couriers_types_dict()

    try:
        query = couriers_model.select().where(couriers_model.c.courier_id == courier_id)
        courier_select = await database.fetch_one(query)
        if courier_select:
            courier = Courier.parse_obj(courier_select)
            errs = []
            for key in request_json:
                if key not in {'courier_type', 'regions', 'working_hours'} or not request_json[key]:
                    errs.append(key)
            if errs:
                return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={'errs': errs})
            
            if 'regions' in request_json.keys():
                courier.regions = request_json['regions']
            if 'working_hours' in request_json.keys():
                courier.working_hours = request_json['working_hours']
            if 'courier_type' in request_json.keys():
                courier.courier_type = request_json['courier_type']

            # update db db 
            update_dict = courier.dict()
            update_dict['courier_type'] = couriers_types_dict[courier.courier_type]
            await database.execute(couriers_model.update().where(couriers_model.c.courier_id == courier_id), values=update_dict)
            
            # TODO: обновить заказы
        
            return courier
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={'errs': {"courier_id": courier_id, "msg": "Not exist"}})
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=e.args)
    