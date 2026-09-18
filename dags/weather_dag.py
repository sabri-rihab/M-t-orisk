from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

# Import your ETL logic functions from root directory scripts
from extract import extract
from transform import transform
from load import load_to_postgres, transform_silver_to_gold
import pandas as pd
import os

default_args = {
    'owner': 'meteorisk',
    'depends_on_past': False,
    'email_on_failure': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def extract_wrapper():
    extract()

def transform_wrapper():
    transform()

def load_wrapper():
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:2004@postgres:5432/meteorisk")
    silver_df = pd.read_parquet("Silver/silver_weather.parquet")
    gold_df = transform_silver_to_gold(silver_df)
    load_to_postgres(gold_df, db_url)

with DAG(
    'meteorisk_etl_pipeline',
    default_args=default_args,
    description='Automated daily ETL pipeline for Météorisk',
    schedule_interval='@daily',
    start_date=datetime(2026, 09, 10),
    catchup=False,
) as dag:

    task_extract = PythonOperator(
        task_id='extract_bronze',
        python_callable=extract_wrapper,
    )

    task_transform = PythonOperator(
        task_id='transform_silver',
        python_callable=transform_wrapper,
    )

    task_load = PythonOperator(
        task_id='load_gold_to_postgres',
        python_callable=load_wrapper,
    )

    # Set execution order: Extract -> Transform -> Load
    task_extract >> task_transform >> task_load