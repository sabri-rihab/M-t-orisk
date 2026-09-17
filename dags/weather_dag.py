from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator


with DAG(
    dag_id="weather_pipeline",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
) as dag:

    extract = BashOperator(
        task_id="extract",
        bash_command="python /opt/airflow/extract.py",
    )

    transform = BashOperator(
        task_id="transform",
        bash_command="python /opt/airflow/transform.py",
    )

    extract >> transform