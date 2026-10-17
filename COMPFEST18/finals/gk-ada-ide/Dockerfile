FROM python:3.9-slim

WORKDIR /app

# Install required packages
RUN apt-get update && \
    apt-get install -y socat && \
    pip install pycryptodome

# Copy challenge files
COPY src/chall.py .
COPY src/flag.txt .

# Run with socat
CMD socat TCP-LISTEN:8080,fork,reuseaddr EXEC:"python3 chall.py",stderr