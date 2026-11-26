from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import crud
from app.crud import Page
from app.database import get_db
from app.models import SessionRecharge, Vehicule
from app.schemas import SessionRead, VehiculeCreate, VehiculeRead, VehiculeUpdate

router = APIRouter(prefix="/vehicules", tags=["Véhicules"])


@router.get("", response_model=list[VehiculeRead], summary="Lister les véhicules")
def lister_vehicules(
    id_client: int | None = None,
    marque: str | None = Query(None, description="Filtre exact (insensible à la casse)"),
    page: Page = Depends(),
    db: Session = Depends(get_db),
):
    stmt = select(Vehicule).order_by(Vehicule.id_vehicule)
    if id_client is not None:
        stmt = stmt.where(Vehicule.id_client == id_client)
    if marque:
        stmt = stmt.where(func.lower(Vehicule.marque) == marque.lower())
    return crud.paginate(db, stmt, page)


@router.get("/{id_vehicule}", response_model=VehiculeRead, summary="Détail d'un véhicule")
def lire_vehicule(id_vehicule: int, db: Session = Depends(get_db)):
    return crud.get_or_404(db, Vehicule, id_vehicule, "Véhicule")


@router.post("", response_model=VehiculeRead, status_code=status.HTTP_201_CREATED,
             summary="Créer un véhicule")
def creer_vehicule(data: VehiculeCreate, db: Session = Depends(get_db)):
    return crud.create(db, Vehicule, data)


@router.patch("/{id_vehicule}", response_model=VehiculeRead, summary="Modifier un véhicule")
def modifier_vehicule(id_vehicule: int, data: VehiculeUpdate, db: Session = Depends(get_db)):
    vehicule = crud.get_or_404(db, Vehicule, id_vehicule, "Véhicule")
    return crud.update(db, vehicule, data)


@router.delete("/{id_vehicule}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Supprimer un véhicule (refusé s'il a des sessions)")
def supprimer_vehicule(id_vehicule: int, db: Session = Depends(get_db)):
    crud.delete(db, crud.get_or_404(db, Vehicule, id_vehicule, "Véhicule"))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{id_vehicule}/sessions", response_model=list[SessionRead],
            summary="Sessions de recharge d'un véhicule")
def sessions_du_vehicule(id_vehicule: int, page: Page = Depends(), db: Session = Depends(get_db)):
    crud.get_or_404(db, Vehicule, id_vehicule, "Véhicule")
    stmt = (
        select(SessionRecharge)
        .where(SessionRecharge.id_vehicule == id_vehicule)
        .order_by(SessionRecharge.debut_session.desc())
    )
    return crud.paginate(db, stmt, page)
