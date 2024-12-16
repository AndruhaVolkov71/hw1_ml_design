from airflow import DAG
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from datetime import datetime

# Определяем основной DAG
with DAG(
    dag_id="orchestrate_dags",
    start_date=datetime(2023, 1, 1),
    schedule_interval=None,
    catchup=False,
) as dag:
    
    delete_bucket_task = TriggerDagRunOperator(
        task_id="trigger_delete_bucket",
        trigger_dag_id="delete_minio_bucket_dag",  # ID DAG'а, создающего бакет
        wait_for_completion=True,  # Ждем завершения DAG перед переходом к следующей задаче
    )

    # Задача 1: Запуск DAG для создания бакета
    create_bucket_task = TriggerDagRunOperator(
        task_id="trigger_create_bucket",
        trigger_dag_id="create_minio_bucket_dag",  # ID DAG'а, создающего бакет
        wait_for_completion=True,  # Ждем завершения DAG перед переходом к следующей задаче
    )

    # Задача 2: Запуск DAG для скачивания датасета
    download_dataset_task = TriggerDagRunOperator(
        task_id="trigger_download_movielens",
        trigger_dag_id="download_and_split",  # ID DAG'а, скачивающего датасет
        wait_for_completion=True,
    )

    # Задача 3: Запуск DAG для обработки данных в Spark
    spark_process_task = TriggerDagRunOperator(
        task_id="trigger_spark_process",
        trigger_dag_id="spark_process",  # ID DAG'а, запускающего Spark обработку
        wait_for_completion=True,
    )

    # Указываем порядок выполнения задач
    delete_bucket_task >> create_bucket_task >> download_dataset_task >> spark_process_task
