import time
import uuid
from collections import defaultdict, deque

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

EMAIL = "22f1001730@ds.study.iitm.ac.in"  # <-- Replace with your login email

app = FastAPI()

# -----------------------------
# CORS
# -----------------------------
allowed_origins = [
    "https://app-f5d4jo.example.com",
    "https://exam.sanand.workers.dev",
    # Add the exam page origin here if it is different.
    # Example:
    # "https://exam.example.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app-f5d4jo.example.com",
        "https://exam.sanand.workers.dev",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)
# -----------------------------
# Rate Limiter
# -----------------------------
RATE_LIMIT = 13
WINDOW = 10

clients = defaultdict(deque)


# -----------------------------
# Request Context
# -----------------------------
@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID")

    if not request_id:
        request_id = str(uuid.uuid4())

    request.state.request_id = request_id

    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id

    return response


# -----------------------------
# Rate Limiter
# -----------------------------
@app.middleware("http")
async def rate_limit(request: Request, call_next):

    # Only apply rate limit to /ping
    if request.url.path == "/ping":

        client = request.headers.get("X-Client-Id", "anonymous")

        now = time.time()
        bucket = clients[client]

        while bucket and bucket[0] <= now - WINDOW:
            bucket.popleft()

        if len(bucket) >= RATE_LIMIT:
            response = JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
            )
            response.headers["X-Request-ID"] = request.state.request_id
            return response

        bucket.append(now)

    return await call_next(request)

# -----------------------------
# Endpoint
# -----------------------------
@app.get("/ping")
async def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.state.request_id,
    }
