FROM python:3.12
RUN mkdir /auth

WORKDIR /auth

COPY ./requirements.txt /auth/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /auth/requirements.txt

ENV PYTHONPATH=/app

COPY . .
