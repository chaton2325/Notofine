from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from databaseone import get_db
from models.models import User, Ticket, Reminder, ReminderChannel, NotificationChannel

# --- Pydantic Schemas for Request/Response Validation ---

class ReminderCreate(BaseModel):
    """Schema for creating a reminder."""
    ticket_id: int
    frequency_days: int = 7
    channels: List[NotificationChannel] = [NotificationChannel.email]

class ReminderUpdate(BaseModel):
    """Schema for updating a reminder."""
    frequency_days: Optional[int] = None
    active: Optional[bool] = None
    channels: Optional[List[NotificationChannel]] = None


# --- Router Definition ---

router = APIRouter(
    prefix="/reminders",
    tags=["Reminders"],
    responses={404: {"description": "Non trouvé"}},
)

# --- Utility Function ---

def get_user_by_email(email: str, db: Session) -> User:
    """Trouve un utilisateur par son email ou renvoie une erreur 404."""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"Utilisateur avec l'email '{email}' non trouvé.")
    return user

# --- API Endpoints ---

@router.post("/", status_code=201)
def create_user_reminder(reminder_data: ReminderCreate, db: Session = Depends(get_db)):
    """
    Crée une nouvelle configuration de rappel pour une contravention spécifique.
    Une seule alerte/rappel est autorisée par ticket.
    """
    # Vérifier que la contravention existe
    ticket = db.query(Ticket).filter(Ticket.id == reminder_data.ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=404,
            detail=f"Contravention avec l'ID '{reminder_data.ticket_id}' non trouvée."
        )
    
    # Vérifier qu'il n'existe pas déjà un rappel pour ce ticket
    existing_reminder = db.query(Reminder).filter(Reminder.ticket_id == reminder_data.ticket_id).first()
    if existing_reminder:
        raise HTTPException(
            status_code=409,
            detail=f"Un rappel existe déjà pour cette contravention (ID: {existing_reminder.id}). Vous ne pouvez créer qu'un seul rappel par ticket."
        )

    try:
        # Créer l'enregistrement principal du rappel
        new_reminder = Reminder(
            ticket_id=ticket.id,
            frequency_days=reminder_data.frequency_days,
            active=True
        )
        db.add(new_reminder)
        db.flush()  # Pour obtenir l'ID du nouveau rappel

        # Ajouter les canaux de notification sélectionnés
        for channel_name in reminder_data.channels:
            channel = ReminderChannel(
                reminder_id=new_reminder.id,
                channel=channel_name,  # Déjà un enum grâce à la validation Pydantic
                enabled=True
            )
            db.add(channel)
        
        db.commit()
        db.refresh(new_reminder)
        
        return {"message": "Rappel créé avec succès", "reminder_id": new_reminder.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Impossible de créer le rappel : {e}")


@router.get("/{email}")
def get_all_reminders_for_user(email: str, db: Session = Depends(get_db)):
    """
    Récupère toutes les configurations de rappel pour toutes les contraventions
    d'un utilisateur spécifique.
    """
    user = get_user_by_email(email, db)
    
    # Jointure pour trouver les rappels via les contraventions de l'utilisateur
    reminders = db.query(Reminder).join(Ticket).filter(Ticket.user_id == user.id).all()
    
    return [
        {
            "id": r.id,
            "frequency_days": r.frequency_days,
            "ticket_id": r.ticket_id,
            "active": r.active,
            "channels": [{"channel": c.channel.value, "enabled": c.enabled} for c in r.notification_channels]
        } for r in reminders
    ]

@router.put("/{reminder_id}")
def update_reminder(reminder_id: int, reminder_data: ReminderUpdate, db: Session = Depends(get_db)):
    """
    Met à jour une configuration de rappel (fréquence, statut, canaux).
    """
    reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
    if not reminder:
        raise HTTPException(status_code=404, detail="Rappel non trouvé.")

    try:
        if reminder_data.frequency_days is not None:
            reminder.frequency_days = reminder_data.frequency_days
        if reminder_data.active is not None:
            reminder.active = reminder_data.active
        
        # Si de nouveaux canaux sont fournis, remplacer les anciens
        if reminder_data.channels is not None:
            # Supprimer les anciens canaux
            db.query(ReminderChannel).filter(ReminderChannel.reminder_id == reminder_id).delete()
            # Ajouter les nouveaux
            for channel_name in reminder_data.channels:
                new_channel = ReminderChannel(
                    reminder_id=reminder_id,
                    channel=channel_name,
                    enabled=True
                )
                db.add(new_channel)

        db.commit()
        db.refresh(reminder)
        return {"message": "Rappel mis à jour avec succès", "reminder_id": reminder.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Impossible de mettre à jour le rappel : {e}")


@router.delete("/{reminder_id}", status_code=200)
def delete_reminder(reminder_id: int, db: Session = Depends(get_db)):
    """
    Supprime une configuration de rappel.
    """
    reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
    if not reminder:
        raise HTTPException(status_code=404, detail="Rappel non trouvé.")

    try:
        # Grâce à "cascade='all, delete-orphan'", les ReminderChannel associés seront aussi supprimés.
        db.delete(reminder)
        db.commit()
        return {"message": "Rappel supprimé avec succès."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Impossible de supprimer le rappel : {e}")