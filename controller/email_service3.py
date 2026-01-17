import smtplib
import os
import secrets
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from databaseone import SessionLocal
from models.models import PasswordResetToken, User


# --- Configuration SMTP ---
HOSTINGER_EMAIL = os.getenv("HOSTINGER_EMAIL")
HOSTINGER_PASSWORD = os.getenv("HOSTINGER_PASSWORD")
HOSTINGER_SMTP_SERVER = "smtp.hostinger.com"
HOSTINGER_SMTP_PORT = 465  # Port SSL


def generate_verification_code() -> str:
    """
    Génère un code de vérification aléatoire de 6 chiffres.
    """
    return ''.join([str(secrets.randbelow(10)) for _ in range(6)])


def send_verification_code_email(recipient_email: str, verification_code: str):
    """
    Envoie un email contenant un code de vérification à l'utilisateur.
    
    Args:
        recipient_email: L'adresse email du destinataire
        verification_code: Le code de vérification à envoyer
    """
    subject = "Your NoToFine verification code"
    
    # Corps de l'email en HTML
    html_body = f"""
    <html>
    <body>
        <p>Hello,</p>
        <p>You have requested a verification code for your NoToFine account.</p>
        <p>Please use the code below to verify your email. This code is valid for 15 minutes.</p>
        <h2 style="text-align:center; letter-spacing: 5px; font-size: 28px; color: #007bff;">{verification_code}</h2>
        <p>If you did not request this, please ignore this email.</p>
        <p>Best regards,<br>The NoToFine Team</p>
    </body>
    </html>
    """

    msg = MIMEMultipart()
    msg['From'] = f"NoToFine <{HOSTINGER_EMAIL}>"
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(html_body, 'html'))

    if not HOSTINGER_EMAIL or not HOSTINGER_PASSWORD:
        error_msg = "Les variables d'environnement HOSTINGER_EMAIL ou HOSTINGER_PASSWORD ne sont pas configurées."
        print(f"Erreur: {error_msg}")
        return False
    
    try:
        with smtplib.SMTP_SSL(HOSTINGER_SMTP_SERVER, HOSTINGER_SMTP_PORT) as server:
            server.login(HOSTINGER_EMAIL, HOSTINGER_PASSWORD)
            server.send_message(msg)
        print(f"✅ Email de vérification envoyé à {recipient_email}")
        return True
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi de l'email: {str(e)}")
        return False


def send_verification_code_and_store(email: str, db: Session) -> tuple[bool, str]:
    """
    Génère un code de vérification, le stocke en base de données et l'envoie par email.
    
    Args:
        email: L'adresse email de l'utilisateur
        db: La session de base de données
        
    Returns:
        tuple[bool, str]: (succès, message)
    """
    try:
        # Vérifier que l'utilisateur existe
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return False, "Utilisateur non trouvé"
        
        # Générer le code
        verification_code = generate_verification_code()
        
        # Envoyer l'email
        email_sent = send_verification_code_email(email, verification_code)
        if not email_sent:
            return False, "Impossible d'envoyer l'email"
        
        # Stocker le code dans la base de données (dans la table password_reset_tokens)
        # On réutilise cette table pour stocker les codes de vérification
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
        
        reset_token = PasswordResetToken(
            user_id=user.id,
            token=verification_code,
            expires_at=expires_at
        )
        
        db.add(reset_token)
        db.commit()
        
        return True, f"Code de vérification envoyé à {email}"
    
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur: {str(e)}")
        return False, f"Erreur: {str(e)}"


def verify_email_code(email: str, code: str, db: Session) -> tuple[bool, str]:
    """
    Vérifie le code de vérification pour une adresse email.
    
    Args:
        email: L'adresse email de l'utilisateur
        code: Le code de vérification fourni par l'utilisateur
        db: La session de base de données
        
    Returns:
        tuple[bool, str]: (succès, message)
    """
    try:
        # Récupérer l'utilisateur
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return False, "Utilisateur non trouvé"
        
        # Récupérer le token le plus récent pour cet utilisateur
        reset_token = db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.token == code
        ).order_by(PasswordResetToken.created_at.desc()).first()
        
        if not reset_token:
            return False, "Code de vérification invalide"
        
        # Vérifier que le code n'a pas expiré
        if datetime.now(timezone.utc) > reset_token.expires_at:
            db.delete(reset_token)
            db.commit()
            return False, "Le code a expiré. Demandez un nouveau code."
        
        # Le code est valide!
        db.delete(reset_token)
        db.commit()
        
        return True, "Code vérifié avec succès"
    
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur: {str(e)}")
        return False, f"Erreur: {str(e)}"
