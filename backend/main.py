from fastapi import FastAPI

from backend.database.connection import Base, engine
from backend.auth import models
from backend.auth.routes import router as auth_router

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="VehicleWise API",
    description="Vehicle comparison and recommendation platform API",
    version="1.0.0",
)

app.include_router(auth_router)


@app.get("/")
def root():
    return {"message": "VehicleWise API is running"}
