import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# --- Configuration SMTP ---
# Les informations sensibles sont chargées depuis les variables d'environnement.
HOSTINGER_EMAIL = os.getenv("HOSTINGER_EMAIL")
HOSTINGER_PASSWORD = os.getenv("HOSTINGER_PASSWORD")
HOSTINGER_SMTP_SERVER = "smtp.hostinger.com"
HOSTINGER_SMTP_PORT = 465  # Port SSL


def send_password_reset_email(recipient_email: str, reset_code: str):
    """
    Envoie un email de réinitialisation de mot de passe à l'utilisateur.
    """
    subject = "Your NoToFine password reset code"
    
    # Corps de l'email en HTML pour un meilleur rendu
    html_body = f"""
    <html>
    <body>
        <p>Hello,</p>
        <p>You have requested a password reset for your NoToFine account.</p>
        <p>Please use the code below to reset your password. This code is valid for 15 minutes.</p>
        <h2 style="text-align:center; letter-spacing: 5px; font-size: 28px;">{reset_code}</h2>
        <p>If you did not request this, please ignore this email.</p>
        <p>Best regards,<br>The No2Fine Team</p>
    </body>
    </html>
    """


    msg = MIMEMultipart()
    msg['From'] = f"No2Fine <{HOSTINGER_EMAIL}>"
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(html_body, 'html'))

    if not HOSTINGER_EMAIL or not HOSTINGER_PASSWORD:
        error_msg = "Les variables d'environnement HOSTINGER_EMAIL ou HOSTINGER_PASSWORD ne sont pas configurées."
        print(f"Erreur: {error_msg}")
        # Dans une application réelle, vous devriez logger cette erreur.
        return
    try:
        with smtplib.SMTP_SSL(HOSTINGER_SMTP_SERVER, HOSTINGER_SMTP_PORT) as server:
            server.login(HOSTINGER_EMAIL, HOSTINGER_PASSWORD)
            server.send_message(msg)
        print(f"Email de réinitialisation envoyé avec succès à {recipient_email}")
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'email à {recipient_email}: {e}")
        # Dans une application réelle, vous devriez logger cette erreur.