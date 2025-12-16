import os
from firebase_admin import credentials, messaging
import firebase_admin
from typing import Optional

CREDENTIALS_PATH = "notofine-firebase-adminsdk-fbsvc-0feb8386dc.json"

def initialize_firebase():
    """
    Initialise l'application Firebase Admin SDK.
    Cette fonction doit être appelée au démarrage de l'application FastAPI.
    """
    if not firebase_admin._apps:
        if not os.path.exists(CREDENTIALS_PATH):
            # Lever une exception arrête le démarrage de l'application si le fichier est manquant.
            # C'est une bonne pratique pour éviter les erreurs en production.
            raise FileNotFoundError(f"Le fichier de crédentials Firebase '{CREDENTIALS_PATH}' est introuvable.")
        
        cred = credentials.Certificate(CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred)
        print("✅ Firebase initialisé avec succès.")

def send_push_notification(token: str, title: str, body: str, image_url: Optional[str] = None):
    """
    Envoie une notification push à un appareil via son token FCM.
    
    Args:
        token: Le token FCM de l'appareil cible.
        title: Le titre de la notification.
        body: Le corps du message de la notification.
        image_url: (Optionnel) L'URL d'une image à afficher dans la notification.
    
    Returns:
        La réponse de l'API FCM.
    
    Raises:
        firebase_admin.FirebaseError: Si une erreur se produit lors de l'envoi.
    """
    # Construction de la notification de base
    notification = messaging.Notification(
        title=title,
        body=body
    )
    
    # Ajout de l'image seulement si elle est fournie
    if image_url:
        notification.image = image_url
        
    # Assemblage du message final
    message = messaging.Message(
        notification=notification,
        token=token,
        android=messaging.AndroidConfig(priority="high"),
        apns=messaging.APNSConfig(payload=messaging.APNSPayload(aps=messaging.Aps(content_available=True)))
    )

    try:
        response = messaging.send(message)
        print(f"✅ Notification push envoyée avec succès à un appareil (réponse: {response})")
        return response
    except firebase_admin.FirebaseError as e:
        print(f"🔥 ERREUR FIREBASE lors de l'envoi: {e}")
        raise  # Fait remonter l'exception pour que le contrôleur la gère
