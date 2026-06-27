FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y socat && \
    pip install pycryptodome 
COPY src/chall.py .
COPY src/aes.py .
COPY src/flag.txt .
COPY src/xor.py .

CMD socat TCP-LISTEN:8080,fork,reuseaddr EXEC:"python3 chall.py",stderr