FROM python:3.13-alpine

WORKDIR /opt/checkeragent

RUN pip install requests

COPY ./main.py .

CMD ["python3", "main.py"]