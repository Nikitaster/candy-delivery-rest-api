import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient

from app import app, database

from test_queries import couriers_create_test_json
import json

# from connect_db import database
import databases

# DATABASE_URL = "postgresql://postgres:postgres@db:5432/test"

client = TestClient(app)

# database = databases.Database('postgresql://postgres:postgres@db:5432/')


@pytest.fixture()
async def setup_function(function):
    await database.connect()


@pytest.fixture()
async def teardown_function(function):
    await database.disconnect()


def test_a():
    for i in range(1, len(couriers_create_test_json['requests'])):
        response = client.post("/couriers",
                               data=json.dumps(couriers_create_test_json['requests'][i]))
        assert response.status_code == couriers_create_test_json['responses'][i]['status_code']
        assert response.json() == couriers_create_test_json['responses'][i]['json']


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


