"""Module contains env, static variables."""

import os

POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
POSTGRES_DB = os.getenv('POSTGRES_DB')

DATABASE_URL = 'postgresql://{}:{}@db:5432/{}'.format(
    POSTGRES_USER,
    POSTGRES_PASSWORD,
    POSTGRES_DB,
)

RATING_RATIO = 3600
RATING_MAX = 5

regular_expression_for_matching_time = """^([0-1]?[0-9]|2[0-3]):[0-5][0-9]-([0-1]?[0-9]|2[0-3]):[0-5][0-9]$"""
