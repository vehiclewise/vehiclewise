from fastapi import FastAPI

from backend.auth.routes import router as auth_router
from backend.database.connection import Base, engine

# Register all database models before creating tables.
from backend.auth import models as auth_models
from member4_dashboard import models as saved_feature_models

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
