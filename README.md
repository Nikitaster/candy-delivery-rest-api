[![pipeline status](https://gitlab.com/nikitaster/candy-delivery-rest-api/badges/master/pipeline.svg)](https://gitlab.com/nikitaster/candy-delivery-rest-api/-/commits/master)
[![coverage report](https://gitlab.com/nikitaster/candy-delivery-rest-api/badges/master/coverage.svg)](https://nikitaster.gitlab.io/candy-delivery-rest-api/coverage/)
[![pylint report](https://nikitaster.gitlab.io/candy-delivery-rest-api/pylint.svg)](https://nikitaster.gitlab.io/candy-delivery-rest-api/pylint.html)

# Candy Delivery REST API
* [About](#about)
* [Dependencies](#dependencies)
* [Database diagram](#db)
* [Installation](#installation)
* [Run](#run)
* [Run Tests](#run_tests)

## About<a name="about"></a>
Проект выполнен в соответствии с заданием по <a href="https://docviewer.yandex.ru/view/363098474/?page=1&*=7Iu98stZpJVFYpagG%2F5r66Nn%2F3Z7InVybCI6InlhLWRpc2stcHVibGljOi8vRDVlaHZKcTJnS1dWMHVYUFFMSkVRMk9vdG0wNVNsNmdtSDlRWldkTkRDU2RabnF6UjRaWHVQSy9wSzJ3dEVjQ3EvSjZicG1SeU9Kb25UM1ZvWG5EYWc9PTovYXNzaWdubWVudC5wZGYiLCJ0aXRsZSI6ImFzc2lnbm1lbnQucGRmIiwibm9pZnJhbWUiOmZhbHNlLCJ1aWQiOiIzNjMwOTg0NzQiLCJ0cyI6MTYxNjc4MjEzNzcyOSwieXUiOiIyMzQ4NzIwMjQxNjEzNzM0NzUwIn0%3D">ссылке</a>.

## Dependencies<a name="dependencies"></a>
* <a href="https://fastapi.tiangolo.com/">FastAPI</a> – async web framework
* <a href="https://www.uvicorn.org">Uvicorn</a> – ASGI server
* <a href="https://docs.sqlalchemy.org">SQLAlchemy Core</a> – for sql query builds
* <a href="https://www.psycopg.org/docs/">Psycopg</a> – postgresql adapter
* <a href="https://magicstack.github.io/asyncpg/current/">asyncpg</a> – async postgresql library
* <a href="https://docs.pytest.org">Pytest, pytest-asyncio</a> – for tests
* <a href="https://coverage.readthedocs.io">Coverage</a> – code coverage 
* <a href="https://www.python-httpx.org">HTTPX</a> – http client for async requests
* <a href="https://requests.readthedocs.io">Requests</a> – http library for sync requests

## Database diagram<a name="db"></a>
<img src="https://i.ibb.co/nf4BhMP/candy-delivery-uml-db.jpg" width=50%>


## Installation<a name="installation"></a>
1.  Install docker engine, docker-compose;
2.  clone this project;

## Run<a name="run"></a>
```bash
cd candy-delivery-rest-api
docker-compose up --build 
```

## Run Tests<a name="run_tests"></a>
Я ориентировался на запуск тестов на gitlab-ci. 
К сожалению, с локальным запуском намудрил: если возникают коллизии тестируемых параметров с записями в базе, тесты ломаются.
```bash 
docker-compose exec api coverage run -m pytest --disable-warnings
docker-compose exec api coverage report --omit=app/test_app.py -m
```
or
```bash 
docker-compose exec api coverage run -m pytest --disable-warnings && docker-compose exec api coverage report --omit=app/test_app.py -m
```
