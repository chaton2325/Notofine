# auth_controller.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext
from typing import Optional

from databaseone import get_db
from models.models import User , State
from passlib.context import CryptContext
from datetime import datetime






# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Router
router = APIRouter(prefix="/auth", tags=["authentication"])

# Pydantic models for request/response
from pydantic import BaseModel, EmailStr

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def get_user_by_email(email: str, db: Session):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    return user


class UserRegister(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None
    state: Optional[str] = None
    state_id: int  # 👈 au lieu de state: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    phone: Optional[str]
    state: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, user):
        return cls(
            id=user.id,
            full_name=user.full_name,
            email=user.email,
            phone=user.phone,
            state=user.state.name if user.state else None,  # 👈 ici on prend seulement le nom
            is_active=user.is_active,
            created_at=user.created_at
        )

class LoginResponse(BaseModel):
    user: UserResponse
    message: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    state: Optional[str] = None
    password: Optional[str] = None  # 👈 nouveau champ

# Routes
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserRegister, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    try:
        hashed_password = get_password_hash(user_data.password)
        new_user = User(
            full_name=user_data.full_name,
            email=user_data.email,
            password_hash=hashed_password,
            phone=user_data.phone,
            state_id=user_data.state_id,
            is_active=True
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # ⚡ Retourner un dictionnaire avec state.name
        response_data = {
            "id": new_user.id,
            "full_name": new_user.full_name,
            "email": new_user.email,
            "phone": new_user.phone,
            "state": new_user.state.name if new_user.state else None,  # <-- string ici
            "is_active": new_user.is_active,
            "created_at": new_user.created_at
        }
        return response_data

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email already registered")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")


# ---- 🔹 Vérification mot de passe ----
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# ---- 🔹 Schéma pour connexion ----
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# ---- 🔹 Route /auth/login ----
@router.post("/login")
def login_user(user_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_data.email).first()

    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    if not verify_password(user_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Mot de passe incorrect")

    return {
        "message": "Connexion réussie ✅",
        "user": {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "state_id": user.state_id,
            "created_at": str(user.created_at)
        }
    }

@router.get("/user/{email}", response_model=UserResponse)
def get_user_info(email: str, db: Session = Depends(get_db)):
    """
    Récupérer les informations d'un utilisateur par son email
    """
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    # ⚡ Transformer state en string
    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "phone": user.phone,
        "state": user.state.name if user.state else None,
        "is_active": user.is_active,
        "created_at": user.created_at
    }


@router.post("/logout")
def logout_user():
    """
    Déconnexion (côté client)
    """
    return {"message": "Déconnexion réussie"}

@router.put("/user/{email}", response_model=UserResponse)
def update_user_profile(
    email: str,
    user_update: UserUpdate,
    db: Session = Depends(get_db)
):
    user = get_user_by_email(email, db)
    
    if user_update.full_name:
        user.full_name = user_update.full_name
    if user_update.phone:
        user.phone = user_update.phone
    if user_update.state:
        state_obj = db.query(State).filter(State.name == user_update.state).first()
        if not state_obj:
            raise HTTPException(status_code=404, detail="État introuvable")
        user.state = state_obj
    if user_update.password:
        user.password_hash = get_password_hash(user_update.password)
    
    db.commit()
    db.refresh(user)
    return UserResponse.from_orm(user)







