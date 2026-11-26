"""Connexion à PostgreSQL : moteur, session et dépendance FastAPI."""
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings
# pool_pre_ping : teste la connexion avant usage (évite les erreurs si la base a redémarré)
engine = create_engine(settings.database_url, pool_pre_ping=True)

# expire_on_commit=False : les objets restent lisibles après commit()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

class Base(DeclarativeBase):
    """Classe mère de tous les modèles ORM."""
def get_db() -> Iterator[Session]:
    """Une session par requête HTTP ; rollback en cas d'erreur, fermeture dans tous les cas."""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
