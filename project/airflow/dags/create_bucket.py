from airflow import DAG
from airflow.operators.python import PythonOperator
from minio import Minio
from datetime import datetime

def create_minio_bucket():
    client = Minio(
        "minio:9000",
        access_key="minioaccesskey",
        secret_key="miniosecretkey",
        secure=False
    )

    bucket_name = "movielens"

    if not client.bucket_exists(bucket_name):
        try:
            # Создание бакета
            client.make_bucket(bucket_name)
            print(f"Bucket {bucket_name} created successfully.")
        except Exception as e:
            print(f"Error creating bucket: {e}")
    else:
        print(f"Bucket {bucket_name} already exists.")

dag = DAG(
    'create_minio_bucket_dag',
    description='Create bucket in MinIO',
    schedule_interval=None,  # DAG не будет запускаться автоматически
    start_date=datetime(2024, 12, 15),
    catchup=False,
)

create_bucket_task = PythonOperator(
    task_id='create_minio_bucket',
    python_callable=create_minio_bucket,
    dag=dag
)
