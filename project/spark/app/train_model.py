print('########### BEFORE IMPORT ############')

import json
from pyspark.sql import SparkSession
from pyspark.ml.recommendation import ALS
from pyspark.sql.functions import col
from pyspark.sql.types import StructType, StructField, FloatType, IntegerType, TimestampType
from pyspark.ml.evaluation import RegressionEvaluator
import sys
import boto3
sys.path.append('.')
import os

print('############## AFTER IMPORT ################')
# Создаем SparkSession
spark = SparkSession.builder.appName('TrainRecommendationModel').master('spark://spark-master:7077').getOrCreate()
minio_access_key = 'minioaccesskey'
minio_secret_key = 'miniosecretkey'
# minio_endpoint = 'http://localhost:9000'
minio_endpoint = 'http://minio:9000'
bucket_name = "movielens"
predictions_file = "predictions.csv"

print('############## AFTER CONNECTION SERVER ############')

spark.sparkContext._jsc.hadoopConfiguration().set("fs.s3a.access.key", os.getenv("AWS_ACCESS_KEY_ID", minio_access_key))
spark.sparkContext._jsc.hadoopConfiguration().set("fs.s3a.secret.key", os.getenv("AWS_SECRET_ACCESS_KEY", minio_secret_key))
spark.sparkContext._jsc.hadoopConfiguration().set("fs.s3a.endpoint", os.getenv("ENDPOINT", minio_endpoint))
spark.sparkContext._jsc.hadoopConfiguration().set("fs.s3a.connection.ssl.enabled", "true")
spark.sparkContext._jsc.hadoopConfiguration().set("fs.s3a.path.style.access", "true")
spark.sparkContext._jsc.hadoopConfiguration().set("fs.s3a.attempts.maximum", "1")
spark.sparkContext._jsc.hadoopConfiguration().set("fs.s3a.connection.establish.timeout", "5000")
spark.sparkContext._jsc.hadoopConfiguration().set("fs.s3a.connection.timeout", "10000")
spark.sparkContext.setLogLevel("WARN")

train_path = "s3a://movielens/train.csv"
test_path = "s3a://movielens/test.csv"
output_metrics_path = "/opt/airflow/data/metrics.json" 
output_model_path = "s3a://movielens/model"

ratings_schema = StructType([
    StructField("userId", IntegerType(), True),
    StructField("movieId", IntegerType(), True),
    StructField("rating", FloatType(), True),
    StructField('timestamp', IntegerType(), True)
])

ratings_train = spark.read.csv(train_path, header=True, schema=ratings_schema)
ratings_test = spark.read.csv(test_path, header=True, schema=ratings_schema)

print('############ CREATE MODEL #################')
als = ALS(
    userCol="userId",
    itemCol="movieId",
    ratingCol="rating",
    nonnegative=True,
    implicitPrefs=False,
    coldStartStrategy="drop"
)

print('#################### FIT MODEL ###############')
model = als.fit(ratings_train)

print('####################### SAVE MODEL ################')
model.write().overwrite().save(output_model_path)
print(f"Модель успешно сохранена в {output_model_path}")
predictions = model.transform(ratings_test)
# predictions = predictions.dropna(subset=["prediction"])


# Сохранение предсказаний в MinIO
def save_predictions_to_minio(predictions, bucket_name, output_file):
    # Настройка клиента MinIO
    minio_client = boto3.client(
        "s3",
        endpoint_url=minio_endpoint,
        aws_access_key_id=minio_access_key,
        aws_secret_access_key=minio_secret_key,
    )

    # Конвертация Spark DataFrame в Pandas DataFrame
    predictions_pd = predictions.toPandas()

    # Сохранение предсказаний как CSV
    predictions_pd.to_csv(output_file, index=False)

    # Загрузка CSV в MinIO
    minio_client.upload_file(output_file, bucket_name, output_file)
    print(f"Файл {output_file} успешно сохранен в бакет {bucket_name}")

print(predictions.show(20, False))
save_predictions_to_minio(predictions, bucket_name, predictions_file)

evaluator = RegressionEvaluator(
    metricName="rmse",
    labelCol="rating",
    predictionCol="prediction"
)
print('############## START EVAL MODEL #################')
rmse = evaluator.evaluate(predictions)
print(f"Root-mean-square error (RMSE) on the training dataset: {rmse}")

metrics = {
    "rmse": rmse
}
print('############## START WRITE RESULT ################')
with open(output_metrics_path, "w") as f:
    json.dump(metrics, f)
    print(f"Метрика RMSE сохранена в {output_metrics_path}")
spark.stop()
