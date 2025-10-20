from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
import cloudinary

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from rich.console import Console

from app.routers import user, auth, post
from app.mongo_connect import connect_database, disconnect_from_database

console = Console()

# Charger les variables d'environnement
load_dotenv()

# Configurer Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

# Créer le dossier uploads/images s'il n'existe pas (au cas où tu veux garder local aussi)
UPLOAD_DIR = "uploads/images"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    console.print(":banana: [cyan underline]Immobilier APIs is starting ...[/]")
    await connect_database()
    yield
    console.print(":mango: [bold red underline]Immobilier APIs shutting down ...[/]")
    await disconnect_from_database()


app = FastAPI(lifespan=lifespan)

# CORS
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Monter le dossier uploads comme fichiers statiques
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Inclure les routers
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(post.router)


# Route de test pour vérifier que l'API fonctionne
@app.get("/")
async def root():
    return {
        "message": "Immobilier API",
        "status": "running",
        "uploads_directory": UPLOAD_DIR
    }


# Route de santé pour vérifier les uploads
@app.get("/health")
async def health_check():
    uploads_exists = os.path.exists(UPLOAD_DIR)
    uploads_writable = os.access(UPLOAD_DIR, os.W_OK) if uploads_exists else False

    return {
        "status": "healthy",
        "uploads_directory": {
            "path": UPLOAD_DIR,
            "exists": uploads_exists,
            "writable": uploads_writable
        }
    }
