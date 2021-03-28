"""Module contains sql queries."""

HAS_ORDERS_QUERY = """
    select * from couriers c 
    inner join orders o on o.courier_id = c.courier_id 
    where c.courier_id = :courier_id_value;
"""

GET_FREE_SPACE_QUERY = """
    select weight - sum as free_space from
        (SELECT sum(o.weight), ct.weight FROM orders o
            inner join couriers c on c.courier_id = :courier_id_value
            inner join couriers_types ct on c.courier_type = ct.id                
            where 
                o.courier_id = c.courier_id 
                AND o.assign_time IS NOT NULL 
                AND o.completed_at is NULL
            group by ct.weight
        ) SUMQUERY
"""

GET_COURIER_MAX_WEIGHT_QUERY = """
    select ct.weight from couriers c 
    inner join couriers_types ct on c.courier_type = ct.id 
    where c.courier_id = :courier_id_value;
"""

GET_SUITABLE_ORDERS_QUERY = """
    SELECT DISTINCT * from (
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


CHECK_ORDER_EXIST_QUERY = """
    SELECT * FROM orders o 
    inner join couriers c on c.courier_id = o.courier_id
    where o.order_id = :order_id
        AND o.courier_id = :courier_id
        AND o.completed_at is NULL
"""


GET_COURIER_PRICE_QUERY = """
    SELECT * FROM couriers c 
    inner join couriers_types ct on ct.id = c.courier_type 
    where c.courier_id = :courier_id
"""


GET_UNSUITABLE_BY_TIME_ORDERS_QUERY = """
    select * from orders
        inner join orders_intervals oi 
            on oi.order_id = orders.order_id 
        inner join couriers_intervals ci
            on ci.courier_id = orders.courier_id 
        where 
            orders.courier_id = :courier_id
            AND NOT (oi.time_from <= ci.time_to AND oi.time_to >= ci.time_from)
"""


GET_COMPLETED_ORDERS_FOR_COURIER_QUERY = """
    SELECT o.region, o.assign_time, o.completed_at FROM orders o
    WHERE o.courier_id = :courier_id
        AND o.completed_at IS NOT NULL
        AND o.assign_time IS NOT NULL
    group by o.region, o.assign_time, o.completed_at
    order by o.region ASC, o.completed_at DESC
"""
