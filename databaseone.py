from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.models import Base

# Configuration de la base de données PostgreSQL (DigitalOcean)
DATABASE_URL = (
    "postgresql+psycopg2://doadmin:AVNS_-hDiidQW0t2qt4D2L74@"
    "db-postgresql-nyc3-60694-do-user-27894668-0.k.db.ondigitalocean.com:25060/"
    "defaultdb?sslmode=require"
)

# Création du moteur SQLAlchemy
engine = create_engine(DATABASE_URL)

# Création d'une session locale
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialise la base de données en créant toutes les tables"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Dépendance pour FastAPI : fournit une session DB et la ferme après usage"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
