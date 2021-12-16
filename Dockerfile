# syntax=docker/dockerfile:1

FROM python:3.8.12-slim-buster

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY bikeWrenchFlask .

CMD ["python", "bikeWrench.py"]
