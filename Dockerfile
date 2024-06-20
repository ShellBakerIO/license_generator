FROM python:3.12

RUN mkdir /fastapi_app

WORKDIR /fastapi_app

COPY ./requirements.txt /fastapi_app/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /fastapi_app/requirements.txt

ENV PYTHONPATH=/app

COPY . .

RUN chmod a+x docker/*.sh

#CMD uvicorn app.main:app --host 0.0.0.0 --port 8000