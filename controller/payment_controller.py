import json
import stripe
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

from databaseone import get_db
from models import models
from schemas import subscription_plan_schema


# Configurer la clé API Stripe depuis les variables d'environnement
# C'est la manière la plus sécurisée de gérer vos clés secrètes.
stripe.api_key = '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' #Ca c'est la clé de plana

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
        #BACKEND_DOMAIN = "https://notofine-backend-ancaw.ondigitalocean.app" # Mode Production
        BACKEND_DOMAIN = "http://localhost:8080" #Mode test
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
            cancel_url=BACKEND_DOMAIN + '/api/payment/success?session_id={CHECKOUT_SESSION_ID}',
            success_url=BACKEND_DOMAIN + '/api/payment/cancel',
            # Nous passons les IDs en métadonnées pour les retrouver dans le webhook
            metadata={
                'user_id': user.id,
                'plan_id': plan.id
            }
        )
        return {"checkout_url": checkout_session.url}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Webhook pour écouter les événements de Stripe, notamment la réussite d'un paiement.
    ATTENTION : Cette version ne vérifie PAS la signature du webhook.
    Elle est moins sécurisée et ne doit être utilisée qu'avec prudence.
    """
    payload = await request.body()
    try:
        # On parse simplement le JSON reçu, sans vérifier la signature.
        event = json.loads(payload)
    except json.JSONDecodeError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payload invalide : impossible de parser le JSON.")

    # Gérer l'événement
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        metadata = session.get('metadata', {})
        user_id = metadata.get('user_id')
        plan_id = metadata.get('plan_id')

        if user_id and plan_id:
            # Logique de création d'abonnement (similaire à votre route existante)
            user = db.query(models.User).filter(models.User.id == user_id).first()
            plan = db.query(models.Plan).filter(models.Plan.id == plan_id).first()

            if user and plan:
                start_date = datetime.now(timezone.utc)
                end_date = start_date + timedelta(days=plan.duration_days)
                
                new_sub = models.Subscription(user_id=user.id, plan_id=plan.id, start_date=start_date, end_date=end_date, payment_status=models.SubscriptionStatus.paid)
                user.abonnement_finish = end_date
                db.add(new_sub)
                db.commit()

    return {"status": "success"}

@router.get("/success", response_class=HTMLResponse)
async def payment_success(session_id: str = Query(...)):
    """
    Page de succès affichée à l'utilisateur après un paiement réussi.
    Ceci est purement informatif pour l'utilisateur. La logique métier est dans le webhook.
    """
    # Vous pourriez vérifier la session Stripe ici pour plus de sécurité, mais ce n'est pas critique
    # car la logique de création d'abonnement est dans le webhook.
    return """
    <html>
        <head><title>Paiement Réussi</title></head>
        <body><h1>Paiement réussi !</h1><p>Votre abonnement est en cours de validation. Vous pouvez maintenant retourner à l'application.</p></body>
    </html>
    """

@router.get("/cancel", response_class=HTMLResponse)
async def payment_cancel():
    """Page affichée à l'utilisateur s'il annule le processus de paiement."""
    return """
    <html>
        <head><title>Paiement Annulé</title></head>
        <body><h1>Paiement annulé.</h1><p>Le processus de paiement a été annulé. Vous pouvez retourner à l'application.</p></body>
    </html>
    """