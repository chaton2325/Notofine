from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta, timezone

from databaseone import get_db
from models import models
from schemas import subscription_plan_schema

router = APIRouter(
    prefix="/api",
    tags=["Subscriptions & Plans"]
)

# =================================
# Endpoints pour les Plans
# =================================

@router.post("/plans", response_model=subscription_plan_schema.Plan, status_code=status.HTTP_201_CREATED, summary="Créer un nouveau plan de souscription")
def create_plan(plan: subscription_plan_schema.PlanCreate, db: Session = Depends(get_db)):
    """
    Crée un nouveau plan de souscription (ex: Basic, Premium).
    - **name**: Nom unique du plan.
    - **price**: Prix en USD.
    - **duration_days**: Durée de validité en jours.
    """
    db_plan = models.Plan(**plan.dict())
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)
    return db_plan

@router.get("/plans", response_model=List[subscription_plan_schema.Plan], summary="Lister tous les plans actifs")
def get_all_plans(db: Session = Depends(get_db)):
    """
    Retourne une liste de tous les plans de souscription actifs.
    """
    plans = db.query(models.Plan).filter(models.Plan.is_active == True).all()
    return plans

# =================================
# Endpoints pour les Abonnements
# =================================

@router.post("/subscriptions", response_model=subscription_plan_schema.Subscription, status_code=status.HTTP_201_CREATED, summary="Créer un abonnement pour un utilisateur")
def create_subscription(sub_data: subscription_plan_schema.SubscriptionCreate, db: Session = Depends(get_db)):
    """
    Crée un nouvel abonnement pour un utilisateur en se basant sur son email et l'ID du plan.
    Met automatiquement à jour la date de fin d'abonnement de l'utilisateur (`abonnement_finish`).
    """
    user = db.query(models.User).filter(models.User.email == sub_data.user_email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Utilisateur avec l'email {sub_data.user_email} non trouvé.")

    plan = db.query(models.Plan).filter(models.Plan.id == sub_data.plan_id).first()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Plan avec l'ID {sub_data.plan_id} non trouvé.")

    if user.abonnement_finish and user.abonnement_finish > datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="L'utilisateur a déjà un abonnement actif.")

    start_date = datetime.now(timezone.utc)
    end_date = start_date + timedelta(days=plan.duration_days)
    
    new_sub = models.Subscription(
        user_id=user.id,
        plan_id=plan.id,
        start_date=start_date,
        end_date=end_date,
        auto_renew=sub_data.auto_renew,
        payment_status=models.SubscriptionStatus.paid
    )

    user.abonnement_finish = end_date

    db.add(new_sub)
    db.commit()
    db.refresh(new_sub)
    
    return new_sub

@router.get("/subscriptions/user/{user_email}", response_model=List[subscription_plan_schema.Subscription], summary="Obtenir les abonnements d'un utilisateur")
def get_user_subscriptions(user_email: str, db: Session = Depends(get_db)):
    """
    Récupère l'historique des abonnements pour un utilisateur donné.
    """
    user = db.query(models.User).filter(models.User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Utilisateur avec l'email {user_email} non trouvé.")
    
    return user.subscriptions

@router.get("/subscriptions/user/{user_email}/status", response_model=subscription_plan_schema.SubscriptionStatusResponse, summary="Vérifier le statut de l'abonnement d'un utilisateur")
def check_user_subscription_status(user_email: str, db: Session = Depends(get_db)):
    """
    Vérifie si un utilisateur a un abonnement actif.
    """
    user = db.query(models.User).filter(models.User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Utilisateur avec l'email {user_email} non trouvé.")

    if user.abonnement_finish and user.abonnement_finish > datetime.now(timezone.utc):
        active_sub = db.query(models.Subscription).filter(models.Subscription.user_id == user.id, models.Subscription.end_date == user.abonnement_finish).first()
        return subscription_plan_schema.SubscriptionStatusResponse(
            is_subscribed=True, is_active=True, end_date=user.abonnement_finish, plan_name=active_sub.plan.name if active_sub else "Inconnu"
        )
    
    return subscription_plan_schema.SubscriptionStatusResponse(is_subscribed=False, is_active=False)

@router.delete("/subscriptions/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Supprimer un abonnement")
def delete_subscription(subscription_id: int, db: Session = Depends(get_db)):
    """
    Supprime un abonnement par son ID. Si c'était l'abonnement actif,
    la date de fin d'abonnement de l'utilisateur est réinitialisée.
    """
    sub = db.query(models.Subscription).filter(models.Subscription.id == subscription_id).first()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Abonnement non trouvé.")

    user = sub.user
    if user and user.abonnement_finish == sub.end_date:
        user.abonnement_finish = None

    db.delete(sub)
    db.commit()
    return