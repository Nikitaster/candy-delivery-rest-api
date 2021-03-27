FROM python:3.8-slim-buster

LABEL author="Nikita Gudkov nikitaster2001@gmail.com"

# запрет для python на создание файлов *.pyc
ENV PYTHONDONTWRITEBYTECODE 1
# запрет на буферизацию вывода в консоль для python
ENV PYTHONUNBUFFERED 1

WORKDIR /root/app

RUN apt update && apt install -y curl

# install dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt
