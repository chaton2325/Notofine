from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, HttpUrl
from typing import Optional
import firebase_admin # Importer la racine pour accéder à FirebaseError

from .email_service1 import send_email_notification
from .firebase_notifications import send_push_notification

router = APIRouter(
    prefix="/api/notifications",
    tags=["Notifications"]
)

class EmailNotificationSchema(BaseModel):
    """Schéma pour l'envoi d'un email de notification."""
    user_email: EmailStr
    subject: str
    message: str

class PushNotificationSchema(BaseModel):
    """Schéma pour l'envoi d'une notification push."""
    token: str
    title: str
    body: str
    image_url: Optional[HttpUrl] = None

@router.post("/email", status_code=status.HTTP_200_OK, summary="Envoyer un email de notification")
def send_generic_email(notification_data: EmailNotificationSchema):
    """
    Envoie un email générique à un utilisateur.
    Cette route est principalement destinée à des fins de test ou d'administration.
    """
    success, error_message = send_email_notification(
        user_email=notification_data.user_email,
        subject=notification_data.subject,
        message=notification_data.message
    )

    if not success:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erreur lors de l'envoi de l'email : {error_message}")

    return {"message": f"Email envoyé avec succès à {notification_data.user_email}"}

@router.post("/push", status_code=status.HTTP_200_OK, summary="Envoyer une notification push")
def send_generic_push(notification_data: PushNotificationSchema):
    """
    Envoie une notification push générique à un appareil via son token FCM.
    Cette route est principalement destinée à des fins de test ou d'administration.
    """
    try:
        response = send_push_notification(
            token=notification_data.token,
            title=notification_data.title,
            body=notification_data.body,
            # Pydantic v2 retourne un objet URL, on le convertit en string
            image_url=str(notification_data.image_url) if notification_data.image_url else None
        )
        return {"message": "Notification push envoyée avec succès", "response": response}
    except Exception as e: # Garder une capture générale pour les autres erreurs
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erreur inattendue lors de l'envoi de la notification : {e}")