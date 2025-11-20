from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from databaseone import SessionLocal
from models.models import User, Ticket, Reminder, ReminderChannel, NotificationChannel, Notification
from controller.auth_controller import router as auth_router
from controller.ticket_controller import router as ticket_router
from controller.reminder_controller import router as reminder_router
from fastapi.middleware.cors import CORSMiddleware # 1. Importez le middleware

app = FastAPI(
    title="Notofine API", 
    description="API de gestion des contraventions avec notifications",
    version="1.0.0"
)

# Monter le répertoire statique pour servir les images uploadées
# Les fichiers dans le dossier "static" seront accessibles via l'URL "/static"
app.mount("/static", StaticFiles(directory="static"), name="static")

# Inclure les routers pour l'authentification et les tickets
app.include_router(auth_router)
app.include_router(ticket_router)
app.include_router(reminder_router)

# 2. Définissez les "origines" autorisées (les adresses qui ont le droit de parler à votre API)
origins = [
    "*"  # En développement, "*" autorise tout le monde. C'est le plus simple.
]

# 3. Ajoutez le middleware à votre application
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Autorise toutes les méthodes (POST, GET, PUT, etc.)
    allow_headers=["*"], # Autorise tous les en-têtes
)

# Dependency pour la base de données
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "Bienvenue sur l'API Notofine 🚀", "version": "1.0.0"}
