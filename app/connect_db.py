import databases

from sqlalchemy import MetaData, create_engine, Table, Column, Integer, \
    String, ForeignKey, Float, ARRAY, TIMESTAMP, Time, Interval, DateTime

from sqlalchemy.ext.declarative import declarative_base

from conf import DATABASE_URL

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
    Column('regions', ARRAY(Integer)),
    Column('working_hours', ARRAY(String)),
    Column('rating', Float, nullable=True),
    Column('earnings', Float, nullable=True),
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
