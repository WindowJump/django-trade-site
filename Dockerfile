FROM python:3.11.5-alpine3.18

COPY requirements.txt /temp/requirements.txt
COPY project /project
WORKDIR /project
EXPOSE 8000

RUN apk add python3-dev postgresql-client build-base postgresql-dev

RUN pip install -r /temp/requirements.txt

RUN adduser --disabled-password admin

USER admin
