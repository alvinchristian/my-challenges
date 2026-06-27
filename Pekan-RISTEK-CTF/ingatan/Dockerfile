FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y socat
COPY ./src/server.py .

CMD socat TCP-LISTEN:8080,fork,reuseaddr EXEC:"python3 server.py",stderr