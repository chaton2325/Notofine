import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# --- Configuration SMTP ---
# Il est fortement recommandé de stocker ces informations dans des variables d'environnement
# plutôt qu'en dur dans le code pour des raisons de sécurité.
HOSTINGER_EMAIL = "noreply@notofine.app"
HOSTINGER_PASSWORD = "Yaourt150@" # Remplacez par votre mot de passe réel
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
        <p>Best regards,<br>The NoToFine Team</p>
    </body>
    </html>
    """


    msg = MIMEMultipart()
    msg['From'] = f"NoToFine <{HOSTINGER_EMAIL}>"
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(html_body, 'html'))

    try:
        with smtplib.SMTP_SSL(HOSTINGER_SMTP_SERVER, HOSTINGER_SMTP_PORT) as server:
            server.login(HOSTINGER_EMAIL, HOSTINGER_PASSWORD)
            server.send_message(msg)
        print(f"Email de réinitialisation envoyé avec succès à {recipient_email}")
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'email à {recipient_email}: {e}")
        # Dans une application réelle, vous devriez logger cette erreur.