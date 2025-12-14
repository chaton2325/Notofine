import json
import stripe
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query, Header
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from databaseone import get_db
from models import models
from schemas import subscription_plan_schema
from .subscription_controller import _create_subscription_logic # Import de la fonction de service


# Configurer la clé API Stripe depuis les variables d'environnement
# C'est la manière la plus sécurisée de gérer vos clés secrètes.
stripe.api_key = '' # Remplacez par votre clé secrète Stripe

# ATTENTION : Il est fortement déconseillé de stocker cette clé en clair dans le code pour la production.
# Cette clé n'est plus utilisée dans cette configuration, mais conservée si vous réactivez le webhook.


router = APIRouter(
    prefix="/api/payment", 
    tags=["Payment"]
)

@router.post("/create-checkout-session", status_code=status.HTTP_200_OK)
def create_checkout_session(
    checkout_data: subscription_plan_schema.SubscriptionCreate, 
    db: Session = Depends(get_db)
):
    """
    Crée une session de paiement Stripe pour un abonnement.
    Le frontend utilisera l'URL retournée pour rediriger l'utilisateur vers la page de paiement.
    """
    user = db.query(models.User).filter(models.User.email == checkout_data.user_email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Utilisateur avec l'email {checkout_data.user_email} non trouvé.")

    plan = db.query(models.Plan).filter(models.Plan.id == checkout_data.plan_id).first()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Plan avec l'ID {checkout_data.plan_id} non trouvé.")

    if user.abonnement_finish and user.abonnement_finish > datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="L'utilisateur a déjà un abonnement actif.")

    try:
        # URL de base de votre backend. Pour le développement, vous pouvez utiliser un service comme ngrok.
        BACKEND_DOMAIN = "http://localhost:8080" #Sandbox
        
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': plan.name,
                        },
                        'unit_amount': int(plan.price * 100), # Le prix doit être en centimes
                    },
                    'quantity': 1,
                },
            ],
            mode='payment',
            success_url=BACKEND_DOMAIN + '/api/payment/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=BACKEND_DOMAIN + '/api/payment/cancel',
            # Nous passons les IDs en métadonnées pour les retrouver dans le webhook
            metadata={
                'user_id': user.id,
                'plan_id': plan.id
            }
        )
        return {"checkout_url": checkout_session.url}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# @router.post("/webhook")
# async def stripe_webhook(request: Request, stripe_signature: str = Header(None), db: Session = Depends(get_db)):
#     """
#     NOTE : Ce webhook est désactivé. La logique de création d'abonnement a été déplacée
#     vers la route /api/payment/success à la demande de l'utilisateur.
#     Cette approche est moins fiable et n'est pas recommandée pour la production.
#     """
#     payload = await request.body()
#     try:
#         event = stripe.Webhook.construct_event(
#             payload=payload, sig_header=stripe_signature, secret=STRIPE_WEBHOOK_SECRET
#         )
#     except (ValueError, stripe.error.SignatureVerificationError) as e:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
#
#     if event['type'] == 'checkout.session.completed':
#         session = event['data']['object']
#         metadata = session.get('metadata', {})
#         user_id = metadata.get('user_id')
#         plan_id = metadata.get('plan_id')
#
#         if user_id and plan_id:
#             user = db.query(models.User).filter(models.User.id == user_id).first()
#             plan = db.query(models.Plan).filter(models.Plan.id == plan_id).first()
#
#             if user and plan:
#                 _create_subscription_logic(user=user, plan=plan, db=db)
#                 db.commit()
#
#     return {"status": "success"}

@router.get("/success", response_class=HTMLResponse)
async def payment_success(session_id: str = Query(...), db: Session = Depends(get_db)):
    """
    Page de succès affichée après le paiement.
    Cette route récupère les détails de la session, valide le paiement et crée l'abonnement.
    """
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        if session.payment_status == "paid":
            #print("paid")
            metadata = session.get('metadata', {})
            user_id = metadata.get('user_id')
            plan_id = metadata.get('plan_id')

            if user_id and plan_id:
                user = db.query(models.User).filter(models.User.id == int(user_id)).first()
                plan = db.query(models.Plan).filter(models.Plan.id == int(plan_id)).first()

                if user and plan:
                    # On vérifie si l'utilisateur n'a pas déjà un abonnement actif
                    # pour éviter les créations multiples si la page est rafraîchie.
                    if not user.abonnement_finish or user.abonnement_finish < datetime.now(timezone.utc):
                        _create_subscription_logic(user=user, plan=plan, db=db)
                        db.commit()
        else:

            # ❌ Paiement non payé → page info
            return """
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Payment Not Completed | NoToFine</title>
                <style>
                    body {
                        margin: 0;
                        font-family: Arial, sans-serif;
                        background: linear-gradient(135deg, #111, #333);
                        min-height: 100vh;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                    }
                    .box {
                        background: white;
                        padding: 40px;
                        border-radius: 12px;
                        max-width: 500px;
                        width: 90%;
                        text-align: center;
                    }
                    h1 { color: #111; }
                    p { color: #555; }
                </style>
            </head>
            <body>
                <div class="box">
                    <h1>Payment Not Completed</h1>
                    <p>Your payment has not been completed or is still pending.</p>
                    <p>No charges were applied.</p>
                    <p>Please return to the NoToFine app and try again.</p>
                </div>
            </body>
            </html>
            """
    except Exception as e:
        # En cas d'erreur (ex: session invalide), on affiche quand même une page de succès générique
        # pour ne pas bloquer l'utilisateur, mais on pourrait logger l'erreur.
        print(f"Erreur lors de la validation du paiement : {e}")


    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Payment Successful | NoToFine</title>
        <style>
            body {
                margin: 0;
                font-family: Arial, Helvetica, sans-serif;
                background: linear-gradient(135deg, #ff7a18, #ffb347);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .container {
                background: #ffffff;
                max-width: 500px;
                width: 90%;
                padding: 40px 30px;
                border-radius: 12px;
                text-align: center;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
            }
            .logo {
                font-size: 28px;
                font-weight: bold;
                color: #ff7a18;
                margin-bottom: 10px;
            }
            h1 {
                color: #222;
                margin-bottom: 15px;
            }
            p {
                color: #555;
                font-size: 16px;
                line-height: 1.6;
            }
            .success-icon {
                font-size: 60px;
                color: #ff7a18;
                margin-bottom: 20px;
            }
            .footer {
                margin-top: 30px;
                font-size: 12px;
                color: #888;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="success-icon">✔</div>
            <div class="logo">NoToFine</div>
            <h1>Payment Successful!</h1>
            <p>
                Thank you for your payment.<br>
                Your subscription is currently being validated.
            </p>
            <p>
                You can now safely return to the NoToFine application.
            </p>
            <div class="footer">
                © NoToFine – Payment secured
            </div>
        </div>
    </body>
    </html>
    """


@router.get("/cancel", response_class=HTMLResponse)
async def payment_cancel():
    """
    Page displayed if the user cancels the payment process.
    """
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Payment Cancelled | NoToFine</title>
        <style>
            body {
                margin: 0;
                font-family: Arial, Helvetica, sans-serif;
                background: linear-gradient(135deg, #111, #333);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .container {
                background: #ffffff;
                max-width: 500px;
                width: 90%;
                padding: 40px 30px;
                border-radius: 12px;
                text-align: center;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
            }
            .logo {
                font-size: 28px;
                font-weight: bold;
                color: #ff7a18;
                margin-bottom: 10px;
            }
            h1 {
                color: #222;
                margin-bottom: 15px;
            }
            p {
                color: #555;
                font-size: 16px;
                line-height: 1.6;
            }
            .cancel-icon {
                font-size: 60px;
                color: #111;
                margin-bottom: 20px;
            }
            .footer {
                margin-top: 30px;
                font-size: 12px;
                color: #888;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="cancel-icon">✖</div>
            <div class="logo">NoToFine</div>
            <h1>Payment Cancelled</h1>
            <p>
                The payment process has been cancelled.<br>
                No charges have been made.
            </p>
            <p>
                You may return to the NoToFine application and try again at any time.
            </p>
            <div class="footer">
                © NoToFine – Secure payments
            </div>
        </div>
    </body>
    </html>
    """
