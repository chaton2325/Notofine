# fonctions_utiles.py
"""
Service de notification pour l'application Notofine
Gère l'envoi de notifications via différents canaux selon les préférences utilisateur
"""

import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from models.models import (
    User, Ticket, Reminder, ReminderChannel, Notification, 
    NotificationChannel, TicketStatus
)


class NotificationService:
    """Service centralisé pour la gestion des notifications"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def send_notification(
        self, 
        user_id: int, 
        message: str, 
        channel: NotificationChannel,
        subject: Optional[str] = None,
        ticket_id: Optional[int] = None,
        reminder_id: Optional[int] = None
    ) -> bool:
        """
        Envoie une notification via le canal spécifié
        
        Args:
            user_id: ID de l'utilisateur
            message: Message à envoyer
            channel: Canal de notification (email, sms, push)
            subject: Sujet pour les emails
            ticket_id: ID du ticket associé (optionnel)
            reminder_id: ID du rappel associé (optionnel)
            
        Returns:
            bool: True si l'envoi a réussi, False sinon
        """
        try:
            # Récupérer l'utilisateur
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            
            # Créer l'enregistrement de notification
            notification = Notification(
                user_id=user_id,
                ticket_id=ticket_id,
                reminder_id=reminder_id,
                channel=channel,
                message=message,
                subject=subject,
                status="pending"
            )
            self.db.add(notification)
            self.db.flush()  # Pour obtenir l'ID
            
            # Envoyer selon le canal
            success = False
            error_msg = None
            
            if channel == NotificationChannel.email:
                success, error_msg = self._send_email(user.email, message, subject)
            elif channel == NotificationChannel.sms:
                success, error_msg = self._send_sms(user.phone, message)
            elif channel == NotificationChannel.push:
                success, error_msg = self._send_push_notification(user_id, message)
            
            # Mettre à jour le statut
            if success:
                notification.status = "sent"
                notification.sent_at = datetime.utcnow()
            else:
                notification.status = "failed"
                notification.error_message = error_msg
            
            self.db.commit()
            return success
            
        except Exception as e:
            self.db.rollback()
            print(f"Erreur lors de l'envoi de notification: {e}")
            return False
    
    def send_reminder_notifications(self, reminder_id: int) -> Dict[str, int]:
        """
        Envoie les notifications de rappel selon les canaux configurés
        
        Args:
            reminder_id: ID du rappel
            
        Returns:
            Dict avec le nombre de notifications envoyées par canal
        """
        reminder = self.db.query(Reminder).filter(Reminder.id == reminder_id).first()
        if not reminder or not reminder.active:
            return {}
        
        # Récupérer les canaux activés pour ce rappel
        channels = self.db.query(ReminderChannel).filter(
            and_(
                ReminderChannel.reminder_id == reminder_id,
                ReminderChannel.enabled == True
            )
        ).all()
        
        if not channels:
            return {}
        
        # Récupérer les tickets en cours de l'utilisateur
        tickets = self.db.query(Ticket).filter(
            and_(
                Ticket.user_id == reminder.user_id,
                Ticket.status == TicketStatus.en_cours
            )
        ).all()
        
        if not tickets:
            return {}
        
        # Préparer le message
        ticket_count = len(tickets)
        message = f"Rappel: Vous avez {ticket_count} contravention(s) en attente de paiement."
        if ticket_count == 1:
            ticket = tickets[0]
            message += f" Numéro: {ticket.ticket_number}"
        
        # Envoyer via chaque canal activé
        results = {}
        for channel_config in channels:
            channel = channel_config.channel
            success = self.send_notification(
                user_id=reminder.user_id,
                message=message,
                channel=channel,
                subject="Rappel de paiement - Notofine",
                reminder_id=reminder_id
            )
            
            if channel.value not in results:
                results[channel.value] = 0
            if success:
                results[channel.value] += 1
        
        return results
    
    def send_ticket_notification(
        self, 
        ticket_id: int, 
        message: str, 
        subject: Optional[str] = None
    ) -> Dict[str, int]:
        """
        Envoie une notification pour un ticket spécifique selon les préférences utilisateur
        
        Args:
            ticket_id: ID du ticket
            message: Message à envoyer
            subject: Sujet pour les emails
            
        Returns:
            Dict avec le nombre de notifications envoyées par canal
        """
        ticket = self.db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            return {}
        
        # Récupérer les canaux préférés de l'utilisateur
        user_reminders = self.db.query(Reminder).filter(
            and_(
                Reminder.user_id == ticket.user_id,
                Reminder.active == True
            )
        ).all()
        
        if not user_reminders:
            # Par défaut, envoyer par email
            success = self.send_notification(
                user_id=ticket.user_id,
                message=message,
                channel=NotificationChannel.email,
                subject=subject,
                ticket_id=ticket_id
            )
            return {"email": 1 if success else 0}
        
        # Envoyer via les canaux configurés
        results = {}
        for reminder in user_reminders:
            channels = self.db.query(ReminderChannel).filter(
                and_(
                    ReminderChannel.reminder_id == reminder.id,
                    ReminderChannel.enabled == True
                )
            ).all()
            
            for channel_config in channels:
                channel = channel_config.channel
                success = self.send_notification(
                    user_id=ticket.user_id,
                    message=message,
                    channel=channel,
                    subject=subject,
                    ticket_id=ticket_id
                )
                
                if channel.value not in results:
                    results[channel.value] = 0
                if success:
                    results[channel.value] += 1
        
        return results
    
    def _send_email(self, email: str, message: str, subject: str = "Notification Notofine") -> tuple[bool, Optional[str]]:
        """
        Envoie un email (implémentation basique - à configurer avec un vrai service SMTP)
        """
        try:
            # Configuration SMTP (à adapter selon votre fournisseur)
            # smtp_server = "smtp.gmail.com"
            # smtp_port = 587
            # username = "your-email@gmail.com"
            # password = "your-password"
            
            # Pour l'instant, on simule l'envoi
            print(f"📧 EMAIL envoyé à {email}")
            print(f"   Sujet: {subject}")
            print(f"   Message: {message}")
            
            # TODO: Implémenter l'envoi réel avec SMTP
            # msg = MIMEMultipart()
            # msg['From'] = username
            # msg['To'] = email
            # msg['Subject'] = subject
            # msg.attach(MIMEText(message, 'plain'))
            
            # server = smtplib.SMTP(smtp_server, smtp_port)
            # server.starttls()
            # server.login(username, password)
            # server.send_message(msg)
            # server.quit()
            
            return True, None
            
        except Exception as e:
            return False, str(e)
    
    def _send_sms(self, phone: str, message: str) -> tuple[bool, Optional[str]]:
        """
        Envoie un SMS (implémentation basique - à configurer avec un vrai service SMS)
        """
        try:
            if not phone:
                return False, "Numéro de téléphone manquant"
            
            # Pour l'instant, on simule l'envoi
            print(f"📱 SMS envoyé au {phone}")
            print(f"   Message: {message}")
            
            # TODO: Implémenter l'envoi réel avec un service SMS (Twilio, etc.)
            # from twilio.rest import Client
            # client = Client(account_sid, auth_token)
            # message = client.messages.create(
            #     body=message,
            #     from_='+1234567890',
            #     to=phone
            # )
            
            return True, None
            
        except Exception as e:
            return False, str(e)
    
    def _send_push_notification(self, user_id: int, message: str) -> tuple[bool, Optional[str]]:
        """
        Envoie une notification push (implémentation basique - à configurer avec FCM)
        """
        try:
            # Pour l'instant, on simule l'envoi
            print(f"🔔 PUSH envoyé à l'utilisateur {user_id}")
            print(f"   Message: {message}")
            
            # TODO: Implémenter l'envoi réel avec Firebase Cloud Messaging
            # import firebase_admin
            # from firebase_admin import messaging
            # 
            # # Récupérer le token FCM de l'utilisateur (à stocker dans la DB)
            # # user_token = get_user_fcm_token(user_id)
            # 
            # message = messaging.Message(
            #     notification=messaging.Notification(
            #         title='Notofine',
            #         body=message,
            #     ),
            #     token=user_token,
            # )
            # 
            # response = messaging.send(message)
            
            return True, None
            
        except Exception as e:
            return False, str(e)


def get_pending_reminders(db: Session) -> List[Reminder]:
    """
    Récupère les rappels qui doivent être envoyés maintenant
    """
    now = datetime.utcnow()
    
    # Récupérer les rappels actifs
    reminders = db.query(Reminder).filter(Reminder.active == True).all()
    
    pending_reminders = []
    for reminder in reminders:
        # Calculer la prochaine date d'envoi
        last_notification = db.query(Notification).filter(
            and_(
                Notification.reminder_id == reminder.id,
                Notification.status == "sent"
            )
        ).order_by(Notification.sent_at.desc()).first()
        
        if last_notification:
            next_send = last_notification.sent_at + timedelta(days=reminder.frequency_days)
            if now >= next_send:
                pending_reminders.append(reminder)
        else:
            # Premier envoi
            pending_reminders.append(reminder)
    
    return pending_reminders


def process_reminders(db: Session) -> Dict[str, Any]:
    """
    Traite tous les rappels en attente
    """
    service = NotificationService(db)
    pending_reminders = get_pending_reminders(db)
    
    results = {
        "processed": len(pending_reminders),
        "channels": {}
    }
    
    for reminder in pending_reminders:
        channel_results = service.send_reminder_notifications(reminder.id)
        for channel, count in channel_results.items():
            if channel not in results["channels"]:
                results["channels"][channel] = 0
            results["channels"][channel] += count
    
    return results
