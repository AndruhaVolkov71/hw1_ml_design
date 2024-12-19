from app.api import crud
from app.api.models import NoteDB, NoteSchema
from fastapi import APIRouter, HTTPException, Path
from typing import List 
from datetime import datetime as dt
import boto3
from io import StringIO
import pandas as pd

router = APIRouter()

# Данные для подключения к MinIO
minio_client = boto3.client(
    "s3",
    endpoint_url="http://minio:9000",  # Используйте внешний адрес, если доступ снаружи
    aws_access_key_id="minioaccesskey",
    aws_secret_access_key="miniosecretkey",
)

BUCKET_NAME = "movielens"
PREDICTIONS_FILE = "predictions.csv"


@router.get("/{user_id}/")
async def get_predictions(user_id: int):
    try:
        response = minio_client.get_object(Bucket=BUCKET_NAME, Key=PREDICTIONS_FILE)
        predictions_data = response['Body'].read().decode('utf-8')

        predictions_df = pd.read_csv(StringIO(predictions_data))

        user_predictions = predictions_df[predictions_df["userId"] == user_id]

        if user_predictions.empty:
            raise HTTPException(status_code=404, detail="No predictions found for this user_id")
        
        max_pred = user_predictions.loc[user_predictions["prediction"].idxmax()]

        return {
            "userId": max_pred.userId,
            "movieId": max_pred.movieId,
            "rating": max_pred.rating,
            "prediction": max_pred.prediction
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    

@router.get("/")
async def get_user_ids():
    try:
        # Получаем файл с предсказаниями из MinIO
        response = minio_client.get_object(Bucket=BUCKET_NAME, Key=PREDICTIONS_FILE)
        predictions_data = response['Body'].read().decode('utf-8')

        # Читаем данные в DataFrame
        predictions_df = pd.read_csv(StringIO(predictions_data))

        # Получаем уникальные userId
        user_ids = predictions_df["userId"].unique().tolist()

        return {"user_ids": user_ids}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

