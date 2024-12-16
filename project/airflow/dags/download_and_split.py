from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import requests
import zipfile
import os
import pandas as pd
from minio import Minio
from minio.error import S3Error

# Функция для скачивания датасета
def download_movielens_dataset():
    url = "https://files.grouplens.org/datasets/movielens/ml-latest-small.zip"
    local_path = "/opt/airflow/data/ml-latest-small.zip"
    os.makedirs(os.path.dirname(local_path), exist_ok=True)

    response = requests.get(url)
    with open(local_path, "wb") as f:
        f.write(response.content)

# Функция для распаковки датасета
def unzip_movielens_dataset():
    local_path = "/opt/airflow/data/ml-latest-small.zip"
    extract_path = "/opt/airflow/data/ml-latest-small/"
    os.makedirs(extract_path, exist_ok=True)

    with zipfile.ZipFile(local_path, "r") as zip_ref:
        zip_ref.extractall(extract_path)

# Функция для разбиения данных на train и test
def split_dataset():
    source_file = "/opt/airflow/data/ml-latest-small/ml-latest-small/ratings.csv"
    train_file = "/opt/airflow/data/ml-latest-small/train.csv"
    test_file = "/opt/airflow/data/ml-latest-small/test.csv"

    data = pd.read_csv(source_file)

    train_size = int(0.8 * len(data))
    train = data.iloc[:train_size]
    test = data.iloc[train_size:]

    train.to_csv(train_file, index=False)
    test.to_csv(test_file, index=False)

def upload_to_minio():
    client = Minio(
        "minio:9000",
        access_key="minioaccesskey",
        secret_key="miniosecretkey",
        secure=False
    )

    bucket_name = "movielens"
    source_folder = "/opt/airflow/data/ml-latest-small/"

    if not client.bucket_exists(bucket_name):
        raise Exception(f"Bucket '{bucket_name}' does not exist")

    # Загружаем каждый файл из папки в бакет
    for root, dirs, files in os.walk(source_folder):
        for file in files:
            file_path = os.path.join(root, file)
            object_name = os.path.relpath(file_path, source_folder)
            client.fput_object(bucket_name, object_name, file_path)
            print(f"Файл {file_path} успешно загружен в бакет {bucket_name} как {object_name}")

# Определение DAG
with DAG(
    dag_id="download_and_split",
    start_date=datetime(2023, 1, 1),
    schedule_interval=None,
    catchup=False,
) as dag:
    # Шаг 1: Скачивание датасета
    download_task = PythonOperator(
        task_id="download_movielens",
        python_callable=download_movielens_dataset,
    )

    # Шаг 2: Распаковка датасета
    unzip_task = PythonOperator(
        task_id="unzip_dataset",
        python_callable=unzip_movielens_dataset,
    )

    # Шаг 3: Разбиение на train и test
    split_task = PythonOperator(
        task_id="split_dataset",
        python_callable=split_dataset,
    )

    # Шаг 4: Загрузка в MinIO
    upload_task = PythonOperator(
        task_id="upload_to_minio",
        python_callable=upload_to_minio,
    )

    download_task >> unzip_task >> split_task >> upload_task
