import os
import json
from firebase_admin import credentials, messaging
import firebase_admin
from typing import Optional
from dotenv import load_dotenv # Importez load_dotenv
load_dotenv() # Charge les variables depuis le fichier .env


def initialize_firebase():
    """
    Initialise l'application Firebase Admin SDK.
    Cette fonction doit être appelée au démarrage de l'application FastAPI.
    """
    if not firebase_admin._apps:
        firebase_credentials_json = os.getenv("FIREBASE_CREDENTIALS_JSON")

        if not firebase_credentials_json:
            raise ValueError(
                "La variable d'environnement 'FIREBASE_CREDENTIALS_JSON' est manquante."
            )

        try:
            cred_dict = json.loads(firebase_credentials_json)

            # 🔴 LIGNE CRITIQUE POUR DIGITALOCEAN
            if "private_key" in cred_dict:
                cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")

            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)

            print("✅ Firebase initialisé avec succès.")

        except json.JSONDecodeError:
            raise ValueError(
                "Impossible de parser le JSON des credentials Firebase. Vérifiez la variable d'environnement."
            )
        except Exception as e:
            raise RuntimeError(
                f"Erreur lors de l'initialisation de Firebase : {e}"
            )
      


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
    except :
        print(f"🔥 ERREUR FIREBASE lors de l'envoi:")
        raise  # Fait remonter l'exception pour que le contrôleur la gère
