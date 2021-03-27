from typing import List, Dict
from datetime import datetime
import json

from fastapi import FastAPI, Response, status, Request
from fastapi.responses import JSONResponse

from models import *
from connect_db import *
from queries import *


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
                # освободить неподходящие заказы
                unsuitable_orders = await database.fetch_all(GET_UNSUITABLE_BY_TIME_ORDERS, values={'courier_id': courier_id})
                for order in unsuitable_orders:
                    await database.execute(orders_model.update().where(orders_model.c.order_id == order['order_id']), values={'assign_time': None, 'courier_id': None})
            if 'courier_type' in request_json.keys():
                courier.courier_type = request_json['courier_type']
                # TODO: очистить неподходящие заказы по весу

            # update db
            update_dict = courier.dict()
            update_dict['courier_type'] = couriers_types_dict[courier.courier_type]
            await database.execute(couriers_model.update().where(couriers_model.c.courier_id == courier_id), values=update_dict)
        
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
    has_orders = await database.fetch_val(HAS_ORDERS_QUERY, values={'courier_id_value': courier.courier_id})

    if has_orders:
        # получим количество свободного места у курьера
        query = GET_FREE_SPACE_QUERY
    else:
        # получим количество места у курьера
        query = GET_COURIER_MAX_WEIGHT_QUERY

    free_space = await database.fetch_val(query, values={'courier_id_value': courier.courier_id})

    # макс. кол-во заказов: выбока по весу, району и графику работы. 
    # сортируем по весу, чтобы взять больше. completed_at, assign_time должны быть NULL
    orders = await database.fetch_all(GET_SUITABLE_ORDERS_QUERY, 
        values={
            'courier_id_value': courier.courier_id, 
            "free_space": free_space
        })

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
    order_check = await database.fetch_one(CHECK_ORDER_EXIST_QUERY, values=order.dict(exclude={'completed_at'}, by_alias=True))
    if not order_check:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={'err': 'Not Found'})

    courier_id = order_check['courier_id']

    await database.execute(orders_model.update().where(orders_model.c.order_id == order.order_id), 
        values={ **order.dict(exclude={'completed_at'}), **{'completed_at': order.completed_at.replace(tzinfo=None)} })

    # update earnings for current courier
    courier_raw = await database.fetch_one(GET_COURIER_PRICE_QUERY, values={'courier_id':courier_id})
    await database.execute(couriers_model.update().where(couriers_model.c.courier_id == courier_id), values={'earnings':courier_raw['earnings'] + 500 * courier_raw['price']})

    # TODO: update rating for current courier
    # select avg((completed_at - assign_time)) from orders group by region order by avg asc;

    return order
    
@app.get('/couriers/{courier_id}', response_model=Courier, response_model_exclude_defaults=True)
async def get_courier(courier_id: int) -> JSONResponse:
    courier = await database.fetch_one(couriers_model.select().where(couriers_model.c.courier_id == courier_id))
    if courier:
        courier = Courier.parse_obj(courier)
        # из-за моей идеи хранить не наименование типа, а фк id, пришлось сделать лишний запрос
        courier_type = await database.fetch_one(couriers_types_model.select().where(couriers_types_model.c.id == int(courier.courier_type)))
        courier.courier_type = courier_type['name']
        return courier
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={'err': 'Not Found'})