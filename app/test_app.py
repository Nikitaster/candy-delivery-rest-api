import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient

from app import app, database

from test_queries import couriers_create_test_json, couriers_patch_test_json
import json

client = TestClient(app)


@pytest.mark.asyncio
async def test_couriers_create():
    await database.connect()
    for i in range(len(couriers_create_test_json['requests'])):
        async with AsyncClient(app=app, base_url="http://0.0.0.0:8080") as ac:
            response = await ac.post("/couriers",
                                     data=json.dumps(couriers_create_test_json['requests'][i]))
        assert response.status_code == couriers_create_test_json['responses'][i]['status_code']
        assert response.json() == couriers_create_test_json['responses'][i]['json']
    await database.disconnect()


@pytest.mark.asyncio
async def test_courier_patch():
    await database.connect()
    for i in range(len(couriers_patch_test_json['requests'])):
        async with AsyncClient(app=app, base_url="http://0.0.0.0:8080") as ac:
            response = await ac.patch("/couriers/1",
                                      data=json.dumps(couriers_patch_test_json['requests'][i]))
        assert response.status_code == couriers_patch_test_json['responses'][i]['status_code']
        assert response.json() == couriers_patch_test_json['responses'][i]['json']
    await database.disconnect()


@pytest.mark.asyncio
async def test_no_exist_courier_patch():
    await database.connect()
    async with AsyncClient(app=app, base_url="http://0.0.0.0:8080") as ac:
        response = await ac.patch("/couriers/0",
                                  data=json.dumps(couriers_patch_test_json['requests'][0]))
    assert response.status_code == 400
    assert response.json() == {"errs": {"courier_id": 0, "msg": "Not exist"}}
    await database.disconnect()
