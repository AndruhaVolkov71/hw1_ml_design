from airflow import DAG
from airflow.operators.python import PythonOperator
from minio import Minio
from datetime import datetime

def create_minio_bucket():
    # Инициализация клиента MinIO
    client = Minio(
        "minio:9000",  # Адрес MinIO
        access_key="minioaccesskey",  # Ваш access key
        secret_key="miniosecretkey",  # Ваш secret key
        secure=False  # Используем HTTP (не HTTPS)
    )

    # Имя бакета
    bucket_name = "movielens"

    # Проверка существует ли бакет
    if not client.bucket_exists(bucket_name):
        try:
            # Создание бакета
            client.make_bucket(bucket_name)
            print(f"Bucket {bucket_name} created successfully.")
        except Exception as e:
            print(f"Error creating bucket: {e}")
    else:
        print(f"Bucket {bucket_name} already exists.")

# Определение DAG
dag = DAG(
    'create_minio_bucket_dag',
    description='Create bucket in MinIO',
    schedule_interval=None,  # DAG не будет запускаться автоматически
    start_date=datetime(2024, 12, 15),
    catchup=False,
)

# Задача для создания бакета
create_bucket_task = PythonOperator(
    task_id='create_minio_bucket',
    python_callable=create_minio_bucket,
    dag=dag
)
