from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from databaseone import get_db
from models import models
from schemas import subscription_plan_schema

router = APIRouter(
    prefix="/api/admin",
    tags=["Admin - Plans Management"]
)

# Note: Ces endpoints devraient être protégés par une authentification d'administrateur.

@router.get("/plans", response_model=List[subscription_plan_schema.Plan], summary="[Admin] Lister tous les plans")
def admin_get_all_plans(db: Session = Depends(get_db)):
    """
    [Admin] Retourne une liste de tous les plans de souscription, y compris les inactifs.
    """
    plans = db.query(models.Plan).order_by(models.Plan.id).all()
    return plans

@router.put("/plans/{plan_id}", response_model=subscription_plan_schema.Plan, summary="[Admin] Mettre à jour un plan")
def admin_update_plan(plan_id: int, plan_update: subscription_plan_schema.PlanUpdate, db: Session = Depends(get_db)):
    """
    [Admin] Met à jour les détails d'un plan existant (prix, description, statut actif).
    Le nom et la durée ne sont pas modifiables pour garantir la cohérence des abonnements existants.
    """
    db_plan = db.query(models.Plan).filter(models.Plan.id == plan_id).first()
    if not db_plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan non trouvé.")

    update_data = plan_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_plan, key, value)

    db.commit()
    db.refresh(db_plan)
    return db_plan

@router.delete("/plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT, summary="[Admin] Supprimer (désactiver) un plan")
def admin_delete_plan(plan_id: int, db: Session = Depends(get_db)):
    """
    [Admin] Désactive un plan pour qu'il ne puisse plus être utilisé pour de nouveaux abonnements.
    Ceci est une "soft delete" (suppression douce) : l'enregistrement n'est pas supprimé de la base de données
    pour préserver l'historique des abonnements existants qui dépendent de ce plan.
    """
    db_plan = db.query(models.Plan).filter(models.Plan.id == plan_id).first()
    if not db_plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan non trouvé.")

    if not db_plan.is_active:
        # On peut choisir de retourner une erreur ou simplement de ne rien faire.
        # Une erreur est plus explicite.
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Le plan est déjà inactif.")

    db_plan.is_active = False
    db.commit()
    return