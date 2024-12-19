from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Histogram

from app.api import notes, ping, predictions
from app.db import engine, metadata, database

metadata.create_all(engine)

app = FastAPI()
Instrumentator().instrument(app).expose(app)

origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:5173",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["DELETE", "GET", "POST", "PUT"],
    allow_headers=["*"],
)

# Define a counter metric
REQUESTS_COUNT = Counter(
    "requests_total", "Total number of requests", ["method", "endpoint", "status_code"]
)
# Define a histogram metric
REQUESTS_TIME = Histogram("requests_time", "Request processing time", ["method", "endpoint"])
api_request_summary = Histogram("api_request_summary", "Request processing time", ["method", "endpoint"])
api_request_counter = Counter("api_request_counter", "Request processing time", ["method", "endpoint", "http_status"])



@app.get("/notes")
async def get_notes():
    api_request_counter.labels(method="GET", endpoint="/notes", http_status=200).inc()
    api_request_summary.labels(method="GET", endpoint="/notes").observe(0.1)
    return await notes.read_all_notes()


@app.get("/notes/{id}")
async def get_note_by_id(id: int):
    api_request_counter.labels(method="GET", endpoint="/notes/{id}", http_status=200).inc()
    api_request_summary.labels(method="GET", endpoint="/notes/{id}").observe(0.1)
    return await notes.read_note(id)

@app.post("/notes")
async def create_note():
    api_request_counter.labels(method="POST", endpoint="/notes", http_status=200).inc()
    api_request_summary.labels(method="POST", endpoint="/notes").observe(0.1)
    return await notes.create_note()


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

@app.get("/predictions/{user_id}")
async def get_predictions_by_user_id(user_id: int):
    api_request_counter.labels(method="GET", endpoint="/predictions/{user_id}", http_status=200).inc()
    api_request_summary.labels(method="GET", endpoint="/predictions/{user_id}").observe(0.1)
    return await predictions.get_predictions(user_id)

@app.get("/predictions")
async def get_user_ids(user_id: int):
    api_request_counter.labels(method="GET", endpoint="/predictions/users", http_status=200).inc()
    api_request_summary.labels(method="GET", endpoint="/predictions/users").observe(0.1)
    return await predictions.get_user_ids(user_id)


app.include_router(ping.router, tags=["ping"],  responses={404: {"description": "Not found"}})
app.include_router(notes.router, prefix="/notes", tags=["notes"],  responses={404: {"description": "Not found"}})
app.include_router(predictions.router, prefix="/predictions", tags=["predictions"],  responses={404: {"description": "Not found"}})

