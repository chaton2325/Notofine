from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.models import Base

# Configuration de la base de données
# Remplacez par vos vraies informations de connexion
'''DATABASE_URL = "postgresql://doadmin:AVNS_-hDiidQW0t2qt4D2L74@db-postgresql-nyc3-60694-do-user-27894668-0.k.db.ondigitalocean.com:25060/defaultdb?sslmode=require"

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
        db.close()'''
