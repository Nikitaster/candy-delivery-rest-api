import os

from typing import List, Dict
from datetime import datetime
import json

from fastapi import FastAPI, Response, status, Request
from fastapi.responses import JSONResponse

import databases

from sqlalchemy import MetaData, create_engine, Table, Column, Integer, \
    String, ForeignKey, Float, ARRAY, TIMESTAMP, Time, Interval, DateTime

from sqlalchemy.ext.declarative import declarative_base

from pydantic import BaseModel, Field, ValidationError


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
    Column('order_id', Integer, primary_key=True),
    Column('courier_id', Integer, ForeignKey('couriers.courier_id'), nullable=True),
    Column('weight', Float, nullable=False),
    Column('region', Integer, nullable=False),
    Column('delivery_hours', ARRAY(String)),
    Column('assign_time', DateTime, nullable=True),
    Column('completed_at', DateTime, nullable=True),

    # courier = relationship('Couriers', back_populates='orders')
)

couriers_intervals_model = Table(
    'couriers_intervals',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('courier_id', Integer, ForeignKey('couriers.courier_id')),
    Column('time_from', Time),
    Column('time_to', Time),
)

orders_intervals_model = Table(
    'orders_intervals',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('order_id', Integer, ForeignKey('orders.order_id')),
    Column('time_from', Time),
    Column('time_to', Time),
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

app = FastAPI()


@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

@app.get("/")
async def root():
    return {"message": "Hello World"}

async def get_couriers_types_dict():
    couriers_types_dict = dict()
    try:
        courier_types = await database.fetch_all(couriers_types_model.select())
        for t in courier_types:
            couriers_types_dict[t['name']] = t['id']
    except Exception as e:
        print(e.args)
    return couriers_types_dict

def get_intervals_from_hours_line(hours_list: List[str], foreign_field_name: str, foreign_field_value: str):
    result = []
    for hours_line in hours_list:
        times = hours_line.split('-')
        result.append({foreign_field_name: foreign_field_value, 'time_from': datetime.strptime(times[0], '%H:%M').time(), 'time_to': datetime.strptime(times[1], '%H:%M').time()})
    return result

@app.post("/couriers")
async def couriers_create(request: Request) -> JSONResponse:
    data = await request.json()

    # сделать словарик, чтобы потом подставить значения ключа из таблицы couriers_types
    couriers_types_dict = await get_couriers_types_dict()

    query_values = []
    couriers_intervals = []
    successful = []

    try:
        couriers = CouriersList.parse_obj(data)
        for courier in couriers.list_couriers:
            courier.courier_type = couriers_types_dict[str(courier.courier_type)]
            query_values.append(courier.dict())
            couriers_intervals += get_intervals_from_hours_line(courier.working_hours, 'courier_id', courier.courier_id)
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
        # заполним табличку с временными метками
        await database.execute_many(couriers_intervals_model.insert(), values=couriers_intervals)
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
                couriers_intervals = get_intervals_from_hours_line(courier.working_hours, 'courier_id', courier.courier_id)
                # удалить старые интревалы
                await database.execute(couriers_intervals_model.delete().where(couriers_intervals_model.c.courier_id == courier_id))
                # сохранить новые
                await database.execute_many(couriers_intervals_model.insert(), values=couriers_intervals)
            if 'courier_type' in request_json.keys():
                courier.courier_type = request_json['courier_type']

            # update db
            update_dict = courier.dict()
            update_dict['courier_type'] = couriers_types_dict[courier.courier_type]
            await database.execute(couriers_model.update().where(couriers_model.c.courier_id == courier_id), values=update_dict)
            
            # TODO: обновить заказы
        
            return courier
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={'errs': {"courier_id": courier_id, "msg": "Not exist"}})
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=e.args)
    
@app.post('/orders')
async def orders_create(request: Request) -> JSONResponse:
    data = await request.json()

    orders_intervals_queries = []

    try:
        orders = OrdersList.parse_obj(data)
        for order in orders.list_orders: 
            orders_intervals_queries += get_intervals_from_hours_line(order.delivery_hours, 'order_id', order.order_id)

    except ValidationError as errs:
        errs = json.loads(errs.json())
        msg = []
        for e in errs:
            index = e['loc'][1]
            msg.append({'id': data['data'][index]['order_id']})
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={'validation_error': {'orders':msg}})
    
    try:
        successful = [{'id': order.order_id} for order in orders.list_orders]
        queries = [order.dict() for order in orders.list_orders]
        await database.execute_many(orders_model.insert(), values=queries)
        # сохраним в бд временные метки (если доабвление заказов вызовет исключение, не выполнится)
        await database.execute_many(orders_intervals_model.insert(), values=orders_intervals_queries)
        return JSONResponse(status_code=status.HTTP_201_CREATED, content={'orders':successful})
    except Exception as errs:
        # есть гарантия, что order_id всегда уникальны
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=errs.args)


@app.post('/orders/assign')
async def order_assing(courier: CourierAssign) -> JSONResponse:
    # проверим, есть ли курьер c таким courier_id
    try:
        record = await database.fetch_one(couriers_model.select().where(couriers_model.c.courier_id == courier.courier_id))
        if not record:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"errs:": {"courier_id": courier.courier_id, "msg": "Not found"}})
        courier = Courier.parse_obj(record)
    except Exception:
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    # выяснить, есть ли у курьера действующие заказы
    query = """
    select * from couriers c 
    inner join orders o on o.courier_id = c.courier_id 
    where c.courier_id = :courier_id_value;
    """

    has_orders = await(database.fetch_val(query, values={'courier_id_value': courier.courier_id}))

    if has_orders:
        # получим количество свободного места у курьера
        query = """
            select weight - sum as free_space from
            (SELECT sum(o.weight), ct.weight FROM orders o
                inner join couriers c on c.courier_id = :courier_id_value
                inner join couriers_types ct on c.courier_type = ct.id
                where o.courier_id = c.courier_id AND o.assign_time IS NOT NULL AND o.completed_at is NULL
                group by ct.weight
                ) SUMQUERY
        """
    else:
        # получим количество места у курьера
        query = """
            select ct.weight from couriers c 
            inner join couriers_types ct on c.courier_type = ct.id 
            where c.courier_id = :courier_id_value;
        """

    free_space = await(database.fetch_val(query, values={'courier_id_value': courier.courier_id}))

    # макс. кол-во заказов: выбока по весу, району и графику работы. 
    # сортируем по весу, чтобы взять больше. completed_at, assign_time должны быть NULL
    query = """ SELECT DISTINCT * from (
        SELECT o.order_id, o.weight FROM orders o
            inner join orders_intervals oi on oi.order_id = o.order_id
            inner join couriers_intervals ci on ci.courier_id = :courier_id_value
            inner join couriers c on c.courier_id = :courier_id_value
            where o.assign_time is NULL AND o.region = ANY(c.regions)
            AND oi.time_from <= ci.time_to AND oi.time_to >= ci.time_from
            AND o.weight <= :free_space
            order by o.weight ASC
            ) subquery
    """

    orders = await(database.fetch_all(query, values={'courier_id_value': courier.courier_id, "free_space": free_space}))

    if orders:
        assignments = {"orders": [], 'assign_time': datetime.now()}
        # получен список подходящих заказов. Назначать их курьеру пока есть место
        for order in orders:
            if int(order['weight']) <= free_space:
                assignments['orders'].append({'id': order['order_id']})
                await database.execute(orders_model.update().where(orders_model.c.order_id == order['order_id']).values(courier_id=courier.courier_id, assign_time=assignments['assign_time']))
                free_space -= int(order['weight'])
            else:
                break

        return assignments
    return {}


@app.post('/orders/complete', response_model=OrderComplete, response_model_include={'order_id'})
async def order_complete(order: OrderComplete) -> JSONResponse:
    # проверить, есть ли такой заказ 
    query = """
        SELECT * FROM orders o 
            inner join couriers c on c.courier_id = o.courier_id
            where o.order_id = :order_id
                AND o.courier_id = :courier_id
                AND o.completed_at is NULL
    """

    order_check = await database.fetch_one(query, values=order.dict(exclude={'completed_at'}, by_alias=True))
    if not order_check:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={'err': 'Not Found'})

    await database.execute(orders_model.update().where(orders_model.c.order_id == order.order_id), 
    values={ **order.dict(exclude={'completed_at'}), **{'completed_at': order.completed_at.replace(tzinfo=None)} })

    return order


    
