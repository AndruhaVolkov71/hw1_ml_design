from airflow import DAG
from airflow.operators.python import PythonOperator
from minio import Minio
from datetime import datetime

def delete_minio_bucket():
    client = Minio(
        "minio:9000",
        access_key="minioaccesskey",
        secret_key="miniosecretkey",
        secure=False
    )

    bucket_name = "movielens"

    if client.bucket_exists(bucket_name):
        try:
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

dag = DAG(
    'delete_minio_bucket_dag',
    description='Delete bucket in MinIO',
    schedule_interval=None,
    start_date=datetime(2024, 12, 15),
    catchup=False,
)

delete_bucket_task = PythonOperator(
    task_id='delete_minio_bucket',
    python_callable=delete_minio_bucket,
    dag=dag
)
