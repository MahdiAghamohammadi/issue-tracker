from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.middleware.timing import timing_middleware
from app.routes.auth import router as auth_router
from app.routes.issues import router as issues_router

app = FastAPI(
    title="Issue Tracker API",
    version="0.1.0",
    description="A mini production-style API built with FastAPI",
)

app.middleware("http")(timing_middleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/v1/health")
def health_check():
    return {"status": "ok"}


app.include_router(auth_router)
app.include_router(issues_router)
