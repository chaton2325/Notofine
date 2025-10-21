from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models.models import Base

# Configuration de la base de données
# Remplacez par vos vraies informations de connexion
DATABASE_URL = ""

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialise la base de données en créant toutes les tables"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Dependency pour FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
