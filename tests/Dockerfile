FROM python:latest

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /code

ADD ../requirements.txt /code/

RUN pip install -r requirements.txt

COPY .. /code/