from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from databaseone import SessionLocal, engine # 1. Importer l'engine
from models import models # 2. Importer tous les modèles

# 3. Créer les tables dans la base de données (si elles n'existent pas)
models.Base.metadata.create_all(bind=engine)

from controller.auth_controller import router as auth_router
from controller.ticket_controller import router as ticket_router
from controller.reminder_controller import router as reminder_router
from controller.subscription_controller import router as subscription_router
from controller.admin_controller import router as admin_router
from controller.device_token_controller import router as device_token_router
from controller.payment_controller import router as payment_router
from controller.notification_controller import router as notification_router # Ajout du nouveau routeur
from controller.firebase_notifications import initialize_firebase
from fastapi.middleware.cors import CORSMiddleware # 1. Importez le middleware

app = FastAPI(
    title="Notofine API", 
    description="API de gestion des contraventions avec notifications",
    version="1.0.0"
)

@app.on_event("startup")
def on_startup():
    """
    Fonctions à exécuter une seule fois au démarrage de l'application.
    """
    print("🚀 Démarrage des services externes...")
    initialize_firebase()

# Monter le répertoire statique pour servir les images uploadées
# Les fichiers dans le dossier "static" seront accessibles via l'URL "/static"
app.mount("/static", StaticFiles(directory="static"), name="static")

# Inclure les routers pour l'authentification et les tickets
app.include_router(auth_router)
app.include_router(ticket_router)
app.include_router(reminder_router)
app.include_router(subscription_router)
app.include_router(admin_router)
app.include_router(device_token_router)
app.include_router(payment_router)
app.include_router(notification_router) # Inclusion du nouveau routeur

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
