import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SERVER_NAME = "EMAIL_SENDER"

def send_email_notification(user_email, subject, message):
    """
    Envoie une notification par email via SMTP Hostinger.
    
    Args:
        user_email (str): Email du destinataire
        subject (str): Sujet de l'email
        message (str): Corps du message
    
    Retourne:
        tuple: (success: bool, error_message: str or None)

    """


    
    # Config Hostinger SMTP
    HOSTINGER_EMAIL = "noreply@notofine.app"
    HOSTINGER_PASSWORD = "Yaourt150@"  # <-- mettre le mot de passe réel ici
    HOSTINGER_SMTP_SERVER = "smtp.hostinger.com"
    HOSTINGER_SMTP_PORT = 465  # SSL

    try:
        if not HOSTINGER_PASSWORD or HOSTINGER_PASSWORD == "":
            error = "HOSTINGER_PASSWORD non configuré."
            print(f"[{SERVER_NAME}] ✗ {error}")
            return False, error
        
        # Créer le message email
        msg = MIMEMultipart()
        msg['From'] = HOSTINGER_EMAIL
        msg['To'] = user_email
        msg['Subject'] = subject
        
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f9f9f9; border-radius: 8px;">
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h2 style="color: #2c3e50; margin: 0;">NoToFine</h2>
                        <p style="color: #7f8c8d; font-size: 12px; margin: 5px 0;">Payment reminder system</p>
                    </div>
                    
                    <div style="background-color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px;">
                        {message.replace(chr(10), '<br>')}
                    </div>
                    
                    <hr style="margin-top: 30px; border: none; border-top: 1px solid #ecf0f1;">
                    <p style="font-size: 11px; color: #95a5a6; text-align: center;">
                        This email was automatically sent by the NoToFine system.
                        Please do not reply to this email.
                    </p>
                </div>
            </body>
        </html>
        """
        msg.attach(MIMEText(html_body, 'html'))

        # Connecter au serveur SMTP Hostinger et envoyer
        with smtplib.SMTP_SSL(HOSTINGER_SMTP_SERVER, HOSTINGER_SMTP_PORT) as server:
            server.login(HOSTINGER_EMAIL, HOSTINGER_PASSWORD)
            server.send_message(msg)

        print(f"[{SERVER_NAME}] ✓ Email envoyé à {user_email}")
        return True, None

    except smtplib.SMTPAuthenticationError:
        error = "Erreur d'authentification Hostinger - Vérifiez le mot de passe"
        print(f"[{SERVER_NAME}] ✗ {error}")
        return False, error
    except smtplib.SMTPException as e:
        error = f"Erreur SMTP : {str(e)}"
        print(f"[{SERVER_NAME}] ✗ {error}")
        return False, error
    except Exception as e:
        error = f"Erreur d'envoi email : {str(e)}"
        print(f"[{SERVER_NAME}] ✗ {error}")
        return False, error
