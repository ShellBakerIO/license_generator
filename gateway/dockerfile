FROM python:3.12
RUN mkdir /gateway
WORKDIR /gateway
COPY ./requirements.txt /gateway/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /gateway/requirements.txt
ENV PYTHONPATH=/app
COPY . .

