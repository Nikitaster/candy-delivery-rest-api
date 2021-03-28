import pytest
from httpx import AsyncClient

from app import app, startup

from test_queries import couriers_create_test_json
import json


@pytest.mark.asyncio
async def test_root():
    await startup()
    async with AsyncClient(app=app, base_url="http://0.0.0.0:8080") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


@pytest.mark.asyncio
async def test_couriers_create():
    async with AsyncClient(app=app, base_url="http://0.0.0.0:8080/") as ac:
        for i in range(len(couriers_create_test_json['requests'])):
            response = await ac.post("/couriers",
                                     data=json.dumps(couriers_create_test_json['requests'][i]))
            assert response.status_code == couriers_create_test_json['responses'][i]['status_code']
            assert response.json() == couriers_create_test_json['responses'][i]['json']
