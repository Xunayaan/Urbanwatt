"""Fonctions utilitaires partagées par tous les routers (évite de répéter le même code 8 fois)."""
from typing import Any

from fastapi import HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import Select, func, select, text
from sqlalchemy.orm import Session


class Page:
    """Paramètres de pagination ?skip=0&limit=50, utilisables via Depends(Page)."""

    def __init__(
        self,
        skip: int = Query(0, ge=0, description="Nombre de lignes à sauter"),
        limit: int = Query(50, ge=1, le=200, description="Nombre max de lignes renvoyées"),
    ):
        self.skip = skip
        self.limit = limit


def paginate(db: Session, stmt: Select, page: Page):
    return db.scalars(stmt.offset(page.skip).limit(page.limit)).all()


def get_or_404(db: Session, model, pk: int, label: str = "Ressource", for_update: bool = False):
    """Récupère une ligne par clé primaire ou lève 404.

    for_update=True -> SELECT ... FOR UPDATE : la ligne est verrouillée jusqu'au commit,
    ce qui évite que deux requêtes concurrentes la modifient en même temps.
    """
    obj = db.get(model, pk, with_for_update=for_update)
    if obj is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"{label} {pk} introuvable")
    return obj


def create(db: Session, model, data: BaseModel | dict[str, Any]):
    values = data if isinstance(data, dict) else data.model_dump()
    obj = model(**values)
    db.add(obj)
    db.commit()  # une violation de contrainte lève IntegrityError ici (gérée dans errors.py)
    db.refresh(obj)
    return obj


def update(db: Session, obj, data: BaseModel):
    # exclude_unset : on ne modifie que les champs réellement envoyés (PATCH partiel)
    for champ, valeur in data.model_dump(exclude_unset=True).items():
        setattr(obj, champ, valeur)
    db.commit()
    db.refresh(obj)
    return obj


def delete(db: Session, obj) -> None:
    db.delete(obj)
    db.commit()


def next_id(db: Session, model, pk_column) -> int:
    """Prochain identifiant pour une table SANS IDENTITY (cas de `incident`).

    LOCK TABLE ... EXCLUSIVE bloque les autres écritures concurrentes sur la table
    jusqu'à la fin de la transaction : deux requêtes ne peuvent donc pas obtenir le même id.
    """
    db.execute(text(f"LOCK TABLE {model.__tablename__} IN EXCLUSIVE MODE"))
    return db.scalar(select(func.coalesce(func.max(pk_column), 0) + 1))
