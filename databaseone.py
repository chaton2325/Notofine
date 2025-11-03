from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from models.models import Base, NotificationChannel
from sqlalchemy.dialects.postgresql import ENUM


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

# This event listener will create the ENUM type in PostgreSQL before creating tables.
@event.listens_for(Base.metadata, "before_create")
def create_enums(target, connection, **kw):
    """Crée les types ENUM personnalisés avant la création des tables."""
    # Condition moved inside the function for broader SQLAlchemy version compatibility.
    if connection.dialect.name != 'postgresql':
        return

    pg_enum = ENUM(
        *[e.value for e in NotificationChannel], 
        name="notification_channel"
    )
    pg_enum.create(connection, checkfirst=True)


def init_db():
    """Initialise la base de données en créant toutes les tables"""
    # The event listener above will be triggered automatically by create_all
    Base.metadata.create_all(bind=engine)

def get_db():
    """Dépendance pour FastAPI : fournit une session DB et la ferme après usage"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
