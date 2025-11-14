from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from api.v1 import auth, users, collections, projects, organizations

# Use /api prefix only in non-local environments
root_path = "/api" if os.getenv("ENV_NAME") != "local" else ""

app = FastAPI(
    title="Virtual Try-On API",
    description="Virtual Try-On Backend API",
    version="1.0.0",
    root_path=root_path,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(collections.router, prefix="/api/v1")
app.include_router(projects.router, prefix="/api/v1")
app.include_router(organizations.router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "Virtual Try-On API Server"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run("fast_api:app", host="0.0.0.0", port=8000, reload=True)

# uv run uvicorn fast_api:app --host 0.0.0.0 --port 8000 --reload
