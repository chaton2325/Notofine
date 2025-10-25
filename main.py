from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from databaseone import SessionLocal
from models.models import User, Ticket, Reminder, ReminderChannel, NotificationChannel, Notification
from fonctions_utiles import NotificationService, process_reminders
from controller.auth_controller import router as auth_router

app = FastAPI(
    title="Notofine API", 
    description="API de gestion des contraventions avec notifications",
    version="1.0.0"
)

# Inclure les routes d'authentification
app.include_router(auth_router)

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

@app.post("/users/{user_id}/reminders")
def create_reminder(
    user_id: int,
    frequency_days: int = 7,
    channels: List[str] = ["email"],
    db: Session = Depends(get_db)
):
    """Créer un rappel pour un utilisateur avec les canaux spécifiés"""
    try:
        # Vérifier que l'utilisateur existe
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
        
        # Créer le rappel
        reminder = Reminder(
            user_id=user_id,
            frequency_days=frequency_days,
            active=True
        )
        db.add(reminder)
        db.flush()
        
        # Ajouter les canaux
        for channel_name in channels:
            if channel_name in ["email", "sms", "push"]:
                channel = ReminderChannel(
                    reminder_id=reminder.id,
                    channel=NotificationChannel(channel_name),
                    enabled=True
                )
                db.add(channel)
        
        db.commit()
        return {"message": "Rappel créé avec succès", "reminder_id": reminder.id}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/notifications/send")
def send_notification(
    user_id: int,
    message: str,
    channel: str,
    subject: str = None,
    ticket_id: int = None,
    db: Session = Depends(get_db)
):
    """Envoyer une notification à un utilisateur"""
    try:
        service = NotificationService(db)
        success = service.send_notification(
            user_id=user_id,
            message=message,
            channel=NotificationChannel(channel),
            subject=subject,
            ticket_id=ticket_id
        )
        
        if success:
            return {"message": "Notification envoyée avec succès"}
        else:
            raise HTTPException(status_code=500, detail="Échec de l'envoi de la notification")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reminders/process")
def process_all_reminders(db: Session = Depends(get_db)):
    """Traiter tous les rappels en attente"""
    try:
        results = process_reminders(db)
        return {
            "message": "Traitement des rappels terminé",
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users/{user_id}/notifications")
def get_user_notifications(
    user_id: int,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Récupérer les notifications d'un utilisateur"""
    notifications = db.query(Notification).filter(
        Notification.user_id == user_id
    ).order_by(Notification.created_at.desc()).limit(limit).all()
    
    return {
        "user_id": user_id,
        "notifications": [
            {
                "id": n.id,
                "channel": n.channel.value,
                "message": n.message,
                "status": n.status,
                "created_at": n.created_at.isoformat(),
                "sent_at": n.sent_at.isoformat() if n.sent_at else None
            }
            for n in notifications
        ]
    }

@app.get("/users/{user_id}/reminders")
def get_user_reminders(user_id: int, db: Session = Depends(get_db)):
    """Récupérer les rappels d'un utilisateur"""
    reminders = db.query(Reminder).filter(Reminder.user_id == user_id).all()
    
    result = []
    for reminder in reminders:
        channels = db.query(ReminderChannel).filter(
            ReminderChannel.reminder_id == reminder.id
        ).all()
        
        result.append({
            "id": reminder.id,
            "frequency_days": reminder.frequency_days,
            "active": reminder.active,
            "channels": [{"channel": c.channel.value, "enabled": c.enabled} for c in channels]
        })
    
    return {"user_id": user_id, "reminders": result}


