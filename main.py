import time
import uuid
from collections import defaultdict, deque

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

EMAIL = "22f1001730@ds.study.iitm.ac.in"

app = FastAPI()

# -----------------------------
# CORS
# -----------------------------
allowed_origins = [
    "https://app-f5d4jo.example.com",
    "https://exam.sanand.workers.dev",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
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

requests = defaultdict(deque)


@app.middleware("http")
async def middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id

    client_id = request.headers.get("X-Client-Id", "anonymous")

    now = time.time()
    q = requests[client_id]

    while q and now - q[0] > WINDOW:
        q.popleft()

    if len(q) >= RATE_LIMIT:
        response = JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"},
        )
        response.headers["X-Request-ID"] = request_id
        return response

    q.append(now)

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

from fastapi import Response

@app.api_route("/", methods=["GET", "HEAD"])
def root():
    return Response(status_code=200)
@app.get("/ping")
async def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.state.request_id,
    }
