from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from app.database import engine, Base
from app.routes import auth, users, properties, upload

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Immobilier API", version="2.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(properties.router)
app.include_router(upload.router)

@app.get("/")
async def root():
    return {"message": "Immobilier API - PostgreSQL Version"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "database": "postgresql"}
