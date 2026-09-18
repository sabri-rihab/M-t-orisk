import os
from datetime import datetime, timedelta
import pandas as pd
from airflow import DAG
from airflow.decorators import task

from extract import extract
from transform import transform
from load import load_to_postgres, transform_silver_to_gold


default_args = { 
    'retries': 2, 
    'retry_delay': timedelta(minutes=5),
    # 'owner': 'airflow', 
    # 'execution_timeout',
    # 'depends_on_past':
    # 'email' : '..........@......'
    # 'email_on_failure': true/false
    }

with DAG(
    dag_id='meteorisk_etl_pipeline',
    default_args = default_args,
    description='Automated daily ETL pipeline for Météorisk',
    schedule='@daily',
    start_date=datetime(2026, 9, 10),
    catchup=False,
) as dag:

    @task
    def extract_task():
        extract()

    @task
    def transform_task():
        transform()

    @task
    def load_task():
        db_url = os.getenv("DATABASE_URL", "postgresql://postgres:2004@postgres:5432/meteorisk")
        silver_df = pd.read_csv("Silver/silver_data.csv")
        gold_df = transform_silver_to_gold(silver_df)
        load_to_postgres(gold_df, db_url)

    # execution order
    extract_task() >> transform_task() >> load_task()