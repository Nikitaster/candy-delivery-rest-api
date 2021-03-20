#!/bin/bash

echo "======Waiting for the database image======"
while ! curl http://db:5432/ 2>&1 | grep '52'
do
  echo "Waiting for the database image"
  sleep 0.1
done
echo "Database is ready"

echo "======Стартуем сервер======"
cd app
uvicorn app:app --host 0.0.0.0 --port 8080 --reload
