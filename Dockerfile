FROM apache/airflow:3.3.1

USER root

COPY requirements.txt /requirements.txt

USER airflow

RUN pip install -r /requirements.txt

WORKDIR /opt/airflow