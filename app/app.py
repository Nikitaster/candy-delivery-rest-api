"""Main module."""

import json
from datetime import datetime

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from pydantic import ValidationError

from connect_db import database, orders_intervals_model, couriers_intervals_model, \
    orders_model, couriers_model, couriers_types_model
from models import OrdersList, OrderComplete, CouriersList, CourierAssign, Courier
from queries import HAS_ORDERS_QUERY, GET_FREE_SPACE_QUERY, GET_COURIER_MAX_WEIGHT_QUERY, \
    GET_SUITABLE_ORDERS_QUERY, CHECK_ORDER_EXIST_QUERY, GET_COURIER_PRICE_QUERY, \
    GET_COMPLETED_ORDERS_FOR_COURIER_QUERY

from methods import get_couriers_types_dict, get_intervals_from_hours_line, courier_update, \
    parse_orders_to_times_by_regions, calculate_new_rating_for_courier

app = FastAPI()


@app.on_event('startup')
async def startup():
    await database.connect()


@app.on_event('shutdown')
async def shutdown():
    await database.disconnect()


@app.post('/couriers')
async def couriers_create(request: Request) -> JSONResponse:
    query_values = []
    couriers_intervals = []
    successful = []

    try:
        data = await request.json()
        # сделать словарик, чтобы потом подставить значения ключа из таблицы couriers_types
        couriers_types_dict = await get_couriers_types_dict()

        couriers = CouriersList.parse_obj(data)
        for courier in couriers.list_couriers:
            courier.courier_type = couriers_types_dict[str(courier.courier_type)]
            query_values.append(courier.dict())
            couriers_intervals += get_intervals_from_hours_line(
                courier.working_hours, 'courier_id', courier.courier_id)
            successful.append({'id': courier.courier_id})

    except ValidationError as errs:
        errs = json.loads(errs.json())
        msg = []
        for err in errs:
            index = err['loc'][1]
            msg.append({'id': data['data'][index]['courier_id']})
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                            content={'validation_error': {'couriers': msg}})

    except KeyError as err:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                            content={'validation_error': {'courier_type': err.args}})

    try:
        await database.execute_many(couriers_model.insert(), values=query_values)
        # заполним табличку с временными метками
        await database.execute_many(couriers_intervals_model.insert(), values=couriers_intervals)
        return JSONResponse(status_code=status.HTTP_201_CREATED, content={'couriers': successful})
    except Exception as errs:
        # есть гарантия, что courier_id всегда уникальны
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=errs.args)


@app.patch('/couriers/{courier_id}', response_model=Courier,
           response_model_exclude={'rating', 'earnings'})
async def couriers_edit(courier_id: int, request: Request) -> JSONResponse:
    try:
        request_json = await request.json()
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
            return await courier_update(courier, request_json)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                            content={'errs': {'courier_id': courier_id, 'msg': 'Not exist'}})
    except ValueError as errs:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                            content={'validation_error': errs.args})


@app.post('/orders')
async def orders_create(request: Request) -> JSONResponse:
    orders_intervals_queries = []
    try:
        data = await request.json()
        orders = OrdersList.parse_obj(data)

        for order in orders.list_orders:
            orders_intervals_queries += get_intervals_from_hours_line(
                order.delivery_hours, 'order_id', order.order_id)

    except ValidationError as errs:
        errs = json.loads(errs.json())
        msg = []
        for err in errs:
            index = err['loc'][1]
            if {'id': data['data'][index]['order_id']} not in msg:
                msg.append({'id': data['data'][index]['order_id']})
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                            content={'validation_error': {'orders': msg}})
    except Exception as errs:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={'errs': errs.args})
    try:
        successful = [{'id': order.order_id} for order in orders.list_orders]
        queries = [order.dict() for order in orders.list_orders]
        await database.execute_many(orders_model.insert(), values=queries)
        # сохраним в бд временные метки (если добавление заказов вызовет исключение, не выполнится)
        await database.execute_many(orders_intervals_model.insert(),
                                    values=orders_intervals_queries)
        return JSONResponse(status_code=status.HTTP_201_CREATED, content={'orders': successful})
    except Exception as errs:
        # есть гарантия, что order_id всегда уникальны
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=errs.args)


@app.post('/orders/assign')
async def order_assign(courier: CourierAssign) -> JSONResponse:
    # проверим, есть ли курьер c таким courier_id
    try:
        record = await database.fetch_one(couriers_model.select().where(
            couriers_model.c.courier_id == courier.courier_id))
        if not record:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                                content={'errs:': {
                                    'courier_id': courier.courier_id, 'msg': 'Not found'}})
        courier = Courier.parse_obj(record)
    except Exception:
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # выяснить, есть ли у курьера действующие заказы
    has_orders = await database.fetch_val(HAS_ORDERS_QUERY,
                                          values={'courier_id_value': courier.courier_id})

    # получим количество свободного места у курьера
    free_space_query = GET_FREE_SPACE_QUERY if has_orders else GET_COURIER_MAX_WEIGHT_QUERY
    free_space = await database.fetch_val(free_space_query,
                                          values={'courier_id_value': courier.courier_id})

    # макс. кол-во заказов: выбока по весу, району и графику работы.
    # сортируем по весу, чтобы взять больше. completed_at, assign_time должны быть NULL
    orders = await database.fetch_all(GET_SUITABLE_ORDERS_QUERY,
                                      values={
                                          'courier_id_value': courier.courier_id,
                                          'free_space': free_space
                                      })

    if orders:
        assignments = {'orders': [], 'assign_time': datetime.now()}
        # получен список подходящих заказов. Назначать их курьеру пока есть место
        for order in orders:
            if int(order['weight']) <= free_space:
                assignments['orders'].append({'id': order['order_id']})
                await database.execute(orders_model.update().where(
                    orders_model.c.order_id == order['order_id']).values(
                        courier_id=courier.courier_id,
                        assign_time=assignments['assign_time']
                ))
                free_space -= int(order['weight'])
            else:
                break

        return assignments
    return {}


@app.post('/orders/complete', response_model=OrderComplete, response_model_include={'order_id'})
async def order_complete(order: OrderComplete) -> JSONResponse:
    # проверить, есть ли такой заказ
    order_check = await database.fetch_one(
        CHECK_ORDER_EXIST_QUERY,
        values=order.dict(exclude={'completed_at'}, by_alias=True))
    if not order_check:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={'err': 'Not Found'})

    courier_id = order_check['courier_id']
    await database.execute(orders_model.update().where(orders_model.c.order_id == order.order_id),
                           values={
                               **order.dict(exclude={'completed_at'}),
                               **{'completed_at': order.completed_at.replace(tzinfo=None)}
                           })

    # get current courier
    courier_raw = await database.fetch_one(GET_COURIER_PRICE_QUERY,
                                           values={'courier_id': courier_id})

    # update earnings for current courier
    await database.execute(
        couriers_model.update().where(couriers_model.c.courier_id == courier_id),
        values={'earnings': courier_raw['earnings'] + 500 * courier_raw['price']})

    # update rating
    all_orders = await database.fetch_all(GET_COMPLETED_ORDERS_FOR_COURIER_QUERY,
                                          values={'courier_id': order.courier_id})

    times = await parse_orders_to_times_by_regions(all_orders)
    new_rating = await calculate_new_rating_for_courier(times)

    await database.execute(couriers_model.update().where(
        couriers_model.c.courier_id == order.courier_id), values={'rating': new_rating})

    return order


@app.get('/couriers/{courier_id}', response_model=Courier, response_model_exclude_defaults=True)
async def get_courier(courier_id: int) -> JSONResponse:
    courier = await database.fetch_one(couriers_model.select().where(
        couriers_model.c.courier_id == courier_id))
    if not courier:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={'err': 'Not Found'})
    courier = Courier.parse_obj(courier)
    courier_type = await database.fetch_one(couriers_types_model.select().where(
        couriers_types_model.c.id == int(courier.courier_type)))
    courier.courier_type = courier_type['name']
    return courier
