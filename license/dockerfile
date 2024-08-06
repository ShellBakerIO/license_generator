FROM python:3.12
RUN mkdir /license
WORKDIR /license
COPY ./requirements.txt /license/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /license/requirements.txt
ENV PYTHONPATH=/app
COPY . .

