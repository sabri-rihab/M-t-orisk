import os
from datetime import datetime
import pandas as pd
from airflow import DAG
from airflow.decorators import task

from extract import extract
from transform import transform
from load import load_to_postgres, transform_silver_to_gold

with DAG(
    dag_id='meteorisk_etl_pipeline',
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
        # Fetch connection string injected by Docker Compose memory
        db_url = os.getenv("DATABASE_URL", "postgresql://postgres:2004@postgres:5432/meteorisk")
        silver_df = pd.read_csv("Silver/silver_data.csv")
        gold_df = transform_silver_to_gold(silver_df)
        load_to_postgres(gold_df, db_url)

    # Set execution order: Extract -> Transform -> Load
    extract_task() >> transform_task() >> load_task()