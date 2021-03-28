"""Test module."""

import json
import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient

from test_queries import couriers_create_test_json, couriers_patch_test_json, \
    orders_create_test_json, orders_complete_test_json, orders_assign_test_json
from app import app, database

client = TestClient(app)


@pytest.mark.asyncio
async def test_couriers_create():
    await database.connect()
    for i in range(len(couriers_create_test_json['requests'])):
        async with AsyncClient(app=app, base_url="http://0.0.0.0:8080") as async_client:
            response = await async_client.post("/couriers",
                                     data=json.dumps(couriers_create_test_json['requests'][i]))
        assert response.status_code == couriers_create_test_json['responses'][i]['status_code']
        assert response.json() == couriers_create_test_json['responses'][i]['json']
    await database.disconnect()


@pytest.mark.asyncio
async def test_orders_create():
    await database.connect()
    for i in range(len(orders_create_test_json['requests'])):
        async with AsyncClient(app=app, base_url="http://0.0.0.0:8080") as async_client:
            response = await async_client.post("/orders",
                                     data=json.dumps(orders_create_test_json['requests'][i]))
        assert response.status_code == orders_create_test_json['responses'][i]['status_code']
        assert response.json() == orders_create_test_json['responses'][i]['json']
    await database.disconnect()


@pytest.mark.asyncio
async def test_orders_assign():
    await database.connect()
    for i in range(len(orders_assign_test_json['requests'])):
        async with AsyncClient(app=app, base_url="http://0.0.0.0:8080") as async_client:
            response = await async_client.post("/orders/assign",
                                     data=json.dumps(orders_assign_test_json['requests'][i]))
        assert response.status_code == orders_assign_test_json['responses'][i]['status_code']
    await database.disconnect()


@pytest.mark.asyncio
async def test_courier_patch():
    await database.connect()
    for i in range(len(couriers_patch_test_json['requests'])):
        async with AsyncClient(app=app, base_url="http://0.0.0.0:8080") as async_client:
            response = await async_client.patch("/couriers/1",
                                      data=json.dumps(couriers_patch_test_json['requests'][i]))
        assert response.status_code == couriers_patch_test_json['responses'][i]['status_code']
        assert response.json() == couriers_patch_test_json['responses'][i]['json']
    await database.disconnect()


@pytest.mark.asyncio
async def test_no_exist_courier_patch():
    await database.connect()
    async with AsyncClient(app=app, base_url="http://0.0.0.0:8080") as async_client:
        response = await async_client.patch("/couriers/0",
                                  data=json.dumps(couriers_patch_test_json['requests'][0]))
    assert response.status_code == 400
    assert response.json() == {"errs": {"courier_id": 0, "msg": "Not exist"}}
    await database.disconnect()


@pytest.mark.asyncio
async def test_orders_complete():
    await database.connect()
    for i in range(len(orders_complete_test_json['requests'])):
        async with AsyncClient(app=app, base_url="http://0.0.0.0:8080") as async_client:
            response = await async_client.post("/orders/complete",
                                     data=json.dumps(orders_complete_test_json['requests'][i]))
        assert response.status_code == orders_complete_test_json['responses'][i]['status_code']
        assert response.json() == orders_complete_test_json['responses'][i]['json']
    await database.disconnect()


@pytest.mark.asyncio
async def test_courier_get():
    await database.connect()
    async with AsyncClient(app=app, base_url="http://0.0.0.0:8080") as async_client:
        response = await async_client.get("/couriers/1")
    assert response.status_code == 200
    async with AsyncClient(app=app, base_url="http://0.0.0.0:8080") as async_client:
        response = await async_client.get("/couriers/2")
    assert response.status_code == 200
    await database.disconnect()


@pytest.mark.asyncio
async def test_not_exist_courier_get():
    await database.connect()
    async with AsyncClient(app=app, base_url="http://0.0.0.0:8080") as async_client:
        response = await async_client.get("/couriers/0")
    assert response.status_code == 400
    await database.disconnect()
