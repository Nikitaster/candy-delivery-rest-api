"""Module contains methods."""
import re
from typing import List
from datetime import datetime
from conf import RATING_RATIO, RATING_MAX, regular_expression_for_matching_time
from connect_db import database, couriers_intervals_model, \
    orders_model, couriers_model, couriers_types_model
from queries import GET_UNSUITABLE_BY_TIME_ORDERS_QUERY


async def get_couriers_types_dict():
    couriers_types_dict = {}
    try:
        courier_types = await database.fetch_all(couriers_types_model.select())
        for c_type in courier_types:
            couriers_types_dict[c_type['name']] = c_type['id']
    except Exception as err:
        # настроить логирование
        print(err.args)
    return couriers_types_dict


async def get_couriers_types_reverse_dict():
    couriers_types_dict = {}
    try:
        courier_types = await database.fetch_all(couriers_types_model.select())
        for c_type in courier_types:
            couriers_types_dict[c_type['id']] = c_type['name']
    except Exception as err:
        print(err.args)
    return couriers_types_dict


def get_intervals_from_hours_line(hours_list: List[str],
                                  foreign_field_name: str,
                                  foreign_field_value: str):
    result = []
    for hours_line in hours_list:
        times = hours_line.split('-')
        result.append({
            foreign_field_name: foreign_field_value,
            'time_from': datetime.strptime(times[0], '%H:%M').time(),
            'time_to': datetime.strptime(times[1], '%H:%M').time()
        })
    return result


async def reset_couriers_intervals(courier):
    couriers_intervals = get_intervals_from_hours_line(
        courier.working_hours, 'courier_id', courier.courier_id)
    # удалить старые интревалы
    await database.execute(couriers_intervals_model.delete().where(
        couriers_intervals_model.c.courier_id == courier.courier_id))
    # сохранить новые
    await database.execute_many(couriers_intervals_model.insert(), values=couriers_intervals)


async def remove_orders_by_time(courier):
    unsuitable_orders = await database.fetch_all(GET_UNSUITABLE_BY_TIME_ORDERS_QUERY,
                                                 values={'courier_id': courier.courier_id})
    for order in unsuitable_orders:
        await database.execute(orders_model.update().where(
            orders_model.c.order_id == order['order_id']),
            values={'assign_time': None, 'courier_id': None})


async def remove_orders_by_weight(courier):
    # получить новый максимальный вес курьера
    max_weight_raw = await database.fetch_one(couriers_types_model.select().where(
        couriers_types_model.c.name == courier.courier_type))
    max_weight = max_weight_raw['weight']
    free_space = max_weight

    # цель: сохранить больше заказов
    # получить все заказы, отсортированные по возрастанию веса, отменить неподходящие
    all_orders = await database.fetch_all(orders_model.select().where(
        orders_model.c.courier_id == courier.courier_id).order_by(orders_model.c.weight.asc()))
    for order in all_orders:
        print(max_weight, free_space, order['weight'])
        if order['weight'] > free_space or order['weight'] > max_weight or free_space > max_weight:
            print('DELETED')
            await database.execute(orders_model.update().where(
                orders_model.c.order_id == order['order_id']),
                values={'assign_time': None, 'courier_id': None})
        else:
            free_space -= order['weight']


async def courier_update(courier, update_dict):
    if 'regions' in update_dict.keys():
        courier.regions = update_dict['regions']
    if 'working_hours' in update_dict.keys():
        for times in update_dict['working_hours']:
            if not re.match(regular_expression_for_matching_time, times):
                raise ValueError({'courier_id': courier.courier_id,
                                  'working_hours': times})
        courier.working_hours = update_dict['working_hours']
        await reset_couriers_intervals(courier)
        await remove_orders_by_time(courier)

    new_values_dict = courier.dict()
    new_values_dict['courier_type'] = int(new_values_dict['courier_type'])

    if 'courier_type' in update_dict.keys():
        courier.courier_type = update_dict['courier_type']
        couriers_types_dict = await get_couriers_types_dict()
        new_values_dict['courier_type'] = int(couriers_types_dict[courier.courier_type])
        await remove_orders_by_weight(courier)
    else:
        couriers_types_dict = await get_couriers_types_reverse_dict()
        courier.courier_type = str(couriers_types_dict[int(courier.courier_type)])

    await database.execute(couriers_model.update().where(
        couriers_model.c.courier_id == courier.courier_id),
        values=new_values_dict)

    return courier


def parse_orders_to_times_by_regions(all_orders):
    times = {}
    for i in range(len(all_orders)):
        region = all_orders[i]['region']
        assign_time = all_orders[i]['assign_time'].timestamp()
        completed_at = all_orders[i]['completed_at'].timestamp()
        if region not in times.keys():
            times[region] = {}
        if assign_time not in times[region]:
            times[region] = {**times[region], **{assign_time: []}}
        times[region][assign_time].append(completed_at)
    return times


def calculate_new_rating_for_courier(times):
    delivery_times = {x: [] for x in times.keys()}
    avg_times = []
    # СЧИТАЕМ Времена на доставку в каждом районе
    for region in times:
        for assign_time in times[region]:
            length_of_completed = len(times[region][assign_time])
            if length_of_completed == 1:
                delivery_times[region].append(times[region][assign_time][0] - assign_time)
            elif length_of_completed > 1:
                for i in range(1, len(times[region][assign_time])):
                    delivery_times[region].append(times[region][assign_time][i - 1] -
                                                  times[region][assign_time][i])
    # СЧИТАЕМ AVG
    for region in delivery_times:
        delivery_times_sum = 0
        delivery_times_count = 0
        for delivery_time in delivery_times[region]:
            delivery_times_sum += delivery_time
            delivery_times_count += 1
        avg_times.append(delivery_times_sum / delivery_times_count)

    return round((RATING_RATIO - min(min(avg_times), RATING_RATIO)) /
                 RATING_RATIO * RATING_MAX, 2)
