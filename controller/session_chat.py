import os
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, EmailStr
from firebase_admin import credentials, db
import firebase_admin
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/chat", tags=["Chat Sessions"])

# ============================================================
# MODELS PYDANTIC
# ============================================================

class ChatMessage(BaseModel):
    """Modèle pour un message dans une session de chat."""
    sender: str  # 'user' ou 'admin'
    sender_email: str
    content: str
    timestamp: str


class InitiateChatSession(BaseModel):
    """Modèle pour initier une session de chat."""
    user_email: EmailStr
    user_name: Optional[str] = None
    subject: Optional[str] = "Support"


class SendMessage(BaseModel):
    """Modèle pour envoyer un message."""
    user_email: EmailStr
    sender: str  # 'user' ou 'admin'
    content: str


class ChatSessionInfo(BaseModel):
    """Modèle pour les informations d'une session de chat."""
    user_email: str
    user_name: Optional[str]
    subject: str
    created_at: str
    updated_at: str
    status: str  # 'active', 'closed'
    admin_name: Optional[str] = None
    message_count: int = 0


# ============================================================
# FIREBASE DATABASE INITIALIZATION
# ============================================================

def initialize_firebase_database():
    """
    Initialise la connexion à Firebase Realtime Database.
    """
    if not firebase_admin._apps:
        firebase_credentials_json = os.getenv("FIREBASE_CREDENTIALS_JSON")

        if not firebase_credentials_json:
            raise ValueError(
                "La variable d'environnement 'FIREBASE_CREDENTIALS_JSON' est manquante."
            )

        try:
            cred_dict = json.loads(firebase_credentials_json)

            # Correction pour DigitalOcean (remplacer les espaces d'échappement)
            if "private_key" in cred_dict:
                cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")

            cred = credentials.Certificate(cred_dict)
            
            # Initialiser Firebase avec l'URL de la Realtime Database
            firebase_admin.initialize_app(
                cred,
                {
                    'databaseURL': 'https://notofine-default-rtdb.firebaseio.com'
                }
            )
            print("✅ Firebase Realtime Database initialisé avec succès.")

        except json.JSONDecodeError as e:
            raise ValueError(
                f"Impossible de parser le JSON des credentials Firebase : {e}"
            )
        except Exception as e:
            raise RuntimeError(
                f"Erreur lors de l'initialisation de Firebase Realtime Database : {e}"
            )


# Initialiser Firebase au démarrage
try:
    initialize_firebase_database()
except Exception as e:
    print(f"⚠️ Avertissement : {e}")


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def sanitize_email(email: str) -> str:
    """
    Sanitize l'email pour l'utiliser comme clé Firebase.
    Firebase n'accepte pas certains caractères (., #, $, [, ]) en tant que clés.
    """
    return email.replace(".", "_").replace("@", "_at_")


def get_chat_session_ref(user_email: str):
    """Retourne la référence au nœud de chat pour un utilisateur."""
    sanitized_email = sanitize_email(user_email)
    return db.reference(f"chat_sessions/{sanitized_email}")


def get_messages_ref(user_email: str):
    """Retourne la référence aux messages pour une session de chat."""
    sanitized_email = sanitize_email(user_email)
    return db.reference(f"chat_sessions/{sanitized_email}/messages")


# ============================================================
# ENDPOINTS
# ============================================================

@router.post("/sessions/initiate", response_model=ChatSessionInfo)
async def initiate_chat_session(session_data: InitiateChatSession):
    """
    Crée une nouvelle session de chat avec l'administrateur.
    
    Structure Firebase:
    ```
    chat_sessions/
      user_email_at_domain_com/
        user_info/
          email: "user@example.com"
          name: "John Doe"
          created_at: "2024-01-17T10:30:00"
        subject: "Support"
        status: "active"
        updated_at: "2024-01-17T10:30:00"
        messages/
          message_1/
            sender: "user"
            sender_email: "user@example.com"
            content: "Bonjour..."
            timestamp: "2024-01-17T10:30:10"
    ```
    """
    try:
        user_email = session_data.user_email
        sanitized_email = sanitize_email(user_email)
        
        # Vérifier si une session existe déjà
        session_ref = get_chat_session_ref(user_email)
        existing_session = session_ref.get()
        
        if existing_session and existing_session.get("status") == "active":
            # Mettre à jour le timestamp
            session_ref.update({
                "updated_at": datetime.now().isoformat(),
            })
            
            return ChatSessionInfo(
                user_email=user_email,
                user_name=existing_session.get("user_info", {}).get("name"),
                subject=existing_session.get("subject", "Support"),
                created_at=existing_session.get("user_info", {}).get("created_at", ""),
                updated_at=datetime.now().isoformat(),
                status="active",
                admin_name=existing_session.get("admin_name"),
                message_count=len(existing_session.get("messages", {})) if existing_session.get("messages") else 0
            )
        
        # Créer une nouvelle session
        current_time = datetime.now().isoformat()
        
        new_session = {
            "user_info": {
                "email": user_email,
                "name": session_data.user_name or "Unknown",
                "created_at": current_time,
            },
            "subject": session_data.subject,
            "status": "active",
            "updated_at": current_time,
            "admin_name": None,
            "messages": {}
        }
        
        session_ref.set(new_session)
        
        print(f"✅ Session de chat créée pour : {user_email}")
        
        return ChatSessionInfo(
            user_email=user_email,
            user_name=session_data.user_name,
            subject=session_data.subject,
            created_at=current_time,
            updated_at=current_time,
            status="active",
            admin_name=None,
            message_count=0
        )
        
    except Exception as e:
        print(f"❌ Erreur lors de la création de la session de chat : {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la création de la session de chat : {str(e)}"
        )


@router.post("/messages/send")
async def send_message(message_data: SendMessage):
    """
    Envoie un message dans une session de chat.
    """
    try:
        user_email = message_data.user_email
        
        # Vérifier que la session existe
        session_ref = get_chat_session_ref(user_email)
        session = session_ref.get()
        
        if not session:
            raise HTTPException(
                status_code=404,
                detail="Session de chat non trouvée. Veuillez d'abord initier une session."
            )
        
        if session.get("status") != "active":
            raise HTTPException(
                status_code=403,
                detail="Cette session de chat est fermée."
            )
        
        # Créer le nouveau message
        current_time = datetime.now().isoformat()
        message_id = f"msg_{int(datetime.now().timestamp() * 1000)}"
        
        new_message = {
            "sender": message_data.sender,  # 'user' ou 'admin'
            "sender_email": message_data.sender if "@" in message_data.sender else message_data.sender,
            "content": message_data.content,
            "timestamp": current_time
        }
        
        # Ajouter le message à la session
        messages_ref = get_messages_ref(user_email)
        messages_ref.child(message_id).set(new_message)
        
        # Mettre à jour le timestamp de la session
        session_ref.update({
            "updated_at": current_time,
        })
        
        print(f"✅ Message envoyé pour : {user_email}")
        
        return {
            "status": "success",
            "message_id": message_id,
            "timestamp": current_time
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi du message : {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'envoi du message : {str(e)}"
        )


@router.get("/sessions/{user_email}", response_model=ChatSessionInfo)
async def get_chat_session(user_email: str):
    """
    Récupère les informations d'une session de chat.
    """
    try:
        session_ref = get_chat_session_ref(user_email)
        session = session_ref.get()
        
        if not session:
            raise HTTPException(
                status_code=404,
                detail="Session de chat non trouvée."
            )
        
        message_count = len(session.get("messages", {})) if session.get("messages") else 0
        
        return ChatSessionInfo(
            user_email=user_email,
            user_name=session.get("user_info", {}).get("name"),
            subject=session.get("subject", "Support"),
            created_at=session.get("user_info", {}).get("created_at", ""),
            updated_at=session.get("updated_at", ""),
            status=session.get("status", "active"),
            admin_name=session.get("admin_name"),
            message_count=message_count
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"❌ Erreur lors de la récupération de la session : {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération de la session : {str(e)}"
        )


@router.get("/messages/{user_email}", response_model=List[ChatMessage])
async def get_chat_messages(user_email: str):
    """
    Récupère tous les messages d'une session de chat.
    """
    try:
        messages_ref = get_messages_ref(user_email)
        messages_data = messages_ref.get()
        
        if not messages_data:
            return []
        
        messages = []
        for message_id, message_data in messages_data.items():
            messages.append(ChatMessage(
                sender=message_data.get("sender", ""),
                sender_email=message_data.get("sender_email", ""),
                content=message_data.get("content", ""),
                timestamp=message_data.get("timestamp", "")
            ))
        
        # Trier par timestamp
        messages.sort(key=lambda m: m.timestamp)
        
        return messages
        
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des messages : {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des messages : {str(e)}"
        )


@router.put("/sessions/{user_email}/close")
async def close_chat_session(user_email: str):
    """
    Ferme une session de chat.
    """
    try:
        session_ref = get_chat_session_ref(user_email)
        session = session_ref.get()
        
        if not session:
            raise HTTPException(
                status_code=404,
                detail="Session de chat non trouvée."
            )
        
        # Mettre à jour le statut
        session_ref.update({
            "status": "closed",
            "updated_at": datetime.now().isoformat(),
        })
        
        print(f"✅ Session de chat fermée pour : {user_email}")
        
        return {
            "status": "success",
            "message": "Session de chat fermée avec succès.",
            "user_email": user_email
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"❌ Erreur lors de la fermeture de la session : {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la fermeture de la session : {str(e)}"
        )


@router.get("/sessions")
async def list_all_chat_sessions():
    """
    Récupère toutes les sessions de chat (pour l'admin).
    """
    try:
        sessions_ref = db.reference("chat_sessions")
        sessions_data = sessions_ref.get()
        
        if not sessions_data:
            return []
        
        sessions_list = []
        for sanitized_email, session_data in sessions_data.items():
            user_email = sanitized_email.replace("_at_", "@").replace("_", ".")
            message_count = len(session_data.get("messages", {})) if session_data.get("messages") else 0
            
            sessions_list.append({
                "user_email": user_email,
                "user_name": session_data.get("user_info", {}).get("name"),
                "subject": session_data.get("subject", "Support"),
                "status": session_data.get("status", "active"),
                "created_at": session_data.get("user_info", {}).get("created_at", ""),
                "updated_at": session_data.get("updated_at", ""),
                "message_count": message_count,
                "admin_name": session_data.get("admin_name")
            })
        
        # Trier par updated_at (les plus récentes en premier)
        sessions_list.sort(key=lambda s: s["updated_at"], reverse=True)
        
        return sessions_list
        
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des sessions : {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des sessions : {str(e)}"
        )
