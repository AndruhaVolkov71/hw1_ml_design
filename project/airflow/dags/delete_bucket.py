from airflow import DAG
from airflow.operators.python import PythonOperator
from minio import Minio
from datetime import datetime

def delete_minio_bucket():
    # Инициализация клиента MinIO
    client = Minio(
        "minio:9000",  # Адрес MinIO
        access_key="minioaccesskey",  # Ваш access key
        secret_key="miniosecretkey",  # Ваш secret key
        secure=False  # Используем HTTP (не HTTPS)
    )

    # Имя бакета
    bucket_name = "movielens"

    # Проверка существования бакета
    if client.bucket_exists(bucket_name):
        try:
            # Удаляем все объекты из бакета
            objects = client.list_objects(bucket_name, recursive=True)
            for obj in objects:
                client.remove_object(bucket_name, obj.object_name)
                print(f"Object {obj.object_name} deleted successfully.")

            # Удаляем бакет
            client.remove_bucket(bucket_name)
            print(f"Bucket {bucket_name} deleted successfully.")
        except Exception as e:
            print(f"Error deleting bucket: {e}")
    else:
        print(f"Bucket {bucket_name} does not exist.")

# Определение DAG
dag = DAG(
    'delete_minio_bucket_dag',
    description='Delete bucket in MinIO',
    schedule_interval=None,  # DAG не будет запускаться автоматически
    start_date=datetime(2024, 12, 15),
    catchup=False,
)

# Задача для удаления бакета
delete_bucket_task = PythonOperator(
    task_id='delete_minio_bucket',
    python_callable=delete_minio_bucket,
    dag=dag
)
