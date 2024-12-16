from airflow.decorators import dag, task
from datetime import datetime

from pyspark import SparkContext
from pyspark.sql import SparkSession
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
import pandas as pd
    
@dag(
    dag_id="spark_process",
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
)
def my_dag():
    
    submit_job = SparkSubmitOperator(
        task_id="spark_process",
        conn_id="my_spark_conn",
        application="/spark/app/train_model.py",
        verbose=True,
        jars="/opt/airflow/aws-java-sdk-bundle-1.12.540.jar,/opt/airflow/hadoop-aws-3.3.4.jar",
    )
    
    submit_job

my_dag()