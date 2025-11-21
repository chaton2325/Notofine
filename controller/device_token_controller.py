from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from databaseone import get_db
from models import models
from schemas import device_token_schema

router = APIRouter(
    prefix="/api",
    tags=["Device Tokens"]
)

@router.post("/device-tokens", response_model=device_token_schema.DeviceToken, status_code=status.HTTP_201_CREATED, summary="Ajouter ou mettre à jour un token d'appareil")
def add_or_update_device_token(token_data: device_token_schema.DeviceTokenCreate, db: Session = Depends(get_db)):
    """
    Associe un token d'appareil (pour les notifications push) à un utilisateur.
    Si le token existe déjà, il est mis à jour avec le nouvel utilisateur (utile si un autre utilisateur se connecte sur le même appareil).
    Sinon, un nouvel enregistrement est créé.
    """
    user = db.query(models.User).filter(models.User.email == token_data.user_email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Utilisateur avec l'email {token_data.user_email} non trouvé.")

    # Logique "Upsert" : chercher le token, s'il existe on met à jour, sinon on crée.
    db_token = db.query(models.UserDeviceToken).filter(models.UserDeviceToken.device_token == token_data.device_token).first()

    if db_token:
        # Le token existe, on s'assure qu'il est bien associé au bon utilisateur.
        db_token.user_id = user.id
        db_token.device_type = token_data.device_type # Mettre à jour le type au cas où
    else:
        # Le token n'existe pas, on le crée.
        db_token = models.UserDeviceToken(
            user_id=user.id,
            device_token=token_data.device_token,
            device_type=token_data.device_type
        )
        db.add(db_token)
    
    db.commit()
    db.refresh(db_token)
    return db_token

@router.delete("/device-tokens/{device_token}", status_code=status.HTTP_204_NO_CONTENT, summary="Supprimer un token d'appareil")
def delete_device_token(device_token: str, db: Session = Depends(get_db)):
    """
    Supprime un token d'appareil de la base de données.
    Utile lorsqu'un utilisateur se déconnecte de l'application sur un appareil.
    """
    db_token = db.query(models.UserDeviceToken).filter(models.UserDeviceToken.device_token == device_token).first()
    
    if db_token:
        db.delete(db_token)
        db.commit()
    
    return

@router.get("/device-tokens/user/{user_email}", response_model=List[device_token_schema.DeviceToken], summary="Lister les tokens d'appareils d'un utilisateur")
def get_user_device_tokens(user_email: str, db: Session = Depends(get_db)):
    """
    Récupère la liste de tous les tokens d'appareils enregistrés pour un utilisateur spécifique.
    """
    user = db.query(models.User).filter(models.User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Utilisateur avec l'email {user_email} non trouvé.")
    
    return user.device_tokens