import os
import uuid
import shutil
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from databaseone import get_db
from models.models import User, Ticket, TicketStatus

# Créer un router pour les tickets, ce qui nous permet de regrouper les routes
router = APIRouter(
    prefix="/tickets",
    tags=["Tickets"],
    responses={404: {"description": "Non trouvé"}},
)

# Répertoire où seront stockées les images des contraventions.
# Il sera créé automatiquement s'il n'existe pas.
UPLOAD_DIRECTORY = "static/images/tickets"
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

# --- Fonction utilitaire pour éviter la répétition ---

def get_user_by_email(email: str, db: Session) -> User:
    """Trouve un utilisateur par son email ou renvoie une erreur 404."""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"Utilisateur avec l'email '{email}' non trouvé.")
    return user

# --- Endpoints de l'API pour les Tickets ---

@router.post("/", status_code=201)
def create_ticket(
    db: Session = Depends(get_db),
    email: str = Form(...),
    ticket_number: str = Form(...),
    amount_usd: float = Form(...),
    description: Optional[str] = Form(None),
    payment_url: Optional[str] = Form(None),
    image: UploadFile = File(...)
):
    """
    Crée une nouvelle contravention pour un utilisateur et stocke l'image associée.
    Les données sont envoyées en 'multipart/form-data'.
    """
    user = get_user_by_email(email, db)

    # Gérer le stockage de l'image sur le serveur
    file_path = ""
    try:
        # Générer un nom de fichier unique pour éviter les conflits
        file_extension = os.path.splitext(image.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(UPLOAD_DIRECTORY, unique_filename)

        # Sauvegarder le fichier sur le disque
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

        # Générer l'URL qui sera stockée en base de données et accessible par l'API
        image_url = f"/static/images/tickets/{unique_filename}"

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du stockage de l'image : {e}")
    finally:
        image.file.close()

    # Créer la contravention en base de données
    try:
        new_ticket = Ticket(
            user_id=user.id,
            ticket_number=ticket_number,
            amount_usd=amount_usd,
            description=description,
            payment_url=payment_url,
            image_url=image_url,
            status=TicketStatus.en_cours
        )
        db.add(new_ticket)
        db.commit()
        db.refresh(new_ticket)

        return {
            "message": "Contravention créée avec succès",
            "ticket_id": new_ticket.id,
            "image_url": image_url,
            "payment_url": new_ticket.payment_url
        }
    except Exception as e:
        db.rollback()
        # En cas d'erreur avec la BDD, on supprime l'image qui a été uploadée
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Erreur lors de la création de la contravention: {e}")


@router.get("/user/{email}")
def get_user_tickets(email: str, db: Session = Depends(get_db)):
    """
    Récupère l'historique de toutes les contraventions pour un utilisateur.
    """
    user = get_user_by_email(email, db)
    tickets = db.query(Ticket).filter(Ticket.user_id == user.id).order_by(Ticket.created_at.desc()).all()
    
    return [
        {
            "id": t.id,
            "ticket_number": t.ticket_number,
            "description": t.description,
            "amount_usd": float(t.amount_usd),
            "payment_url": t.payment_url,
            "image_url": t.image_url,
            "status": t.status.value,
            "created_at": t.created_at.isoformat()
        } for t in tickets
    ]

@router.put("/{ticket_id}")
def update_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    description: Optional[str] = Form(None),
    status: Optional[TicketStatus] = Form(None),
    amount_usd: Optional[float] = Form(None),
    payment_url: Optional[str] = Form(None)
):
    """
    Met à jour les informations d'une contravention (description, statut, montant, lien de paiement).
    """
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Contravention non trouvée.")

    if description is not None:
        ticket.description = description
    if status is not None:
        ticket.status = status
    if amount_usd is not None:
        ticket.amount_usd = amount_usd
    if payment_url is not None:
        ticket.payment_url = payment_url

    try:
        db.commit()
        db.refresh(ticket)
        return {"message": "Contravention mise à jour avec succès", "id": ticket.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur lors de la mise à jour : {e}")


@router.delete("/{ticket_id}")
def delete_ticket(ticket_id: int, db: Session = Depends(get_db)):
    """
    Supprime une contravention et son image associée du serveur.
    """
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Contravention non trouvée.")

    image_path_to_delete = None
    if ticket.image_url:
        # L'URL est /static/..., on enlève le / au début pour avoir un chemin relatif
        image_path_to_delete = ticket.image_url.lstrip('/')

    try:
    
        db.delete(ticket)
        db.commit()

        # On supprime le fichier image seulement si la transaction BDD a réussi
        if image_path_to_delete and os.path.exists(image_path_to_delete):
            os.remove(image_path_to_delete)

        return {"message": "Contravention supprimée avec succès."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression : {e}")