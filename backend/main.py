from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
from routers import safety, neighborhoods, alerts


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="SafeStep API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(safety.router, prefix="/api/safety", tags=["safety"])
app.include_router(neighborhoods.router, prefix="/api/neighborhoods", tags=["neighborhoods"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["alerts"])


@app.get("/health")
async def health():
    return {"status": "ok"}
