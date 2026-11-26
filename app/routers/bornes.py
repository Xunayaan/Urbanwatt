from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import crud
from app.crud import Page
from app.database import get_db
from app.models import Borne, Incident, SessionRecharge
from app.schemas import (
    BorneCreate,
    BorneEtat,
    BorneEtatUpdate,
    BorneRead,
    BorneUpdate,
    IncidentRead,
    SessionRead,
)

router = APIRouter(prefix="/bornes", tags=["Bornes"])


@router.get("", response_model=list[BorneRead], summary="Lister les bornes (avec filtres)")
def lister_bornes(
    id_station: int | None = None,
    etat: BorneEtat | None = None,
    connecteur: str | None = Query(None, description="Filtre exact (insensible à la casse)"),
    puissance_min: float | None = Query(None, gt=0, description="Puissance minimale en kW"),
    page: Page = Depends(),
    db: Session = Depends(get_db),
):
    stmt = select(Borne).order_by(Borne.id_borne)
    if id_station is not None:
        stmt = stmt.where(Borne.id_station == id_station)
    if etat:
        stmt = stmt.where(Borne.etat == etat)
    if connecteur:
        stmt = stmt.where(func.lower(Borne.connecteur) == connecteur.lower())
    if puissance_min is not None:
        stmt = stmt.where(Borne.puissance_kw >= puissance_min)
    return crud.paginate(db, stmt, page)


@router.get("/{id_borne}", response_model=BorneRead, summary="Détail d'une borne")
def lire_borne(id_borne: int, db: Session = Depends(get_db)):
    return crud.get_or_404(db, Borne, id_borne, "Borne")


@router.post("", response_model=BorneRead, status_code=status.HTTP_201_CREATED,
             summary="Créer une borne")
def creer_borne(data: BorneCreate, db: Session = Depends(get_db)):
    return crud.create(db, Borne, data)


@router.patch("/{id_borne}", response_model=BorneRead, summary="Modifier une borne")
def modifier_borne(id_borne: int, data: BorneUpdate, db: Session = Depends(get_db)):
    borne = crud.get_or_404(db, Borne, id_borne, "Borne")
    return crud.update(db, borne, data)


@router.patch("/{id_borne}/etat", response_model=BorneRead,
              summary="Changer l'état d'une borne (disponible / hors_service / maintenance)")
def changer_etat(id_borne: int, data: BorneEtatUpdate, db: Session = Depends(get_db)):
    borne = crud.get_or_404(db, Borne, id_borne, "Borne")
    return crud.update(db, borne, data)


@router.delete("/{id_borne}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Supprimer une borne (refusé si elle a des sessions ou incidents)")
def supprimer_borne(id_borne: int, db: Session = Depends(get_db)):
    crud.delete(db, crud.get_or_404(db, Borne, id_borne, "Borne"))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{id_borne}/sessions", response_model=list[SessionRead],
            summary="Sessions de recharge d'une borne")
def sessions_de_la_borne(id_borne: int, page: Page = Depends(), db: Session = Depends(get_db)):
    crud.get_or_404(db, Borne, id_borne, "Borne")
    stmt = (
        select(SessionRecharge)
        .where(SessionRecharge.id_borne == id_borne)
        .order_by(SessionRecharge.debut_session.desc())
    )
    return crud.paginate(db, stmt, page)


@router.get("/{id_borne}/incidents", response_model=list[IncidentRead],
            summary="Incidents d'une borne")
def incidents_de_la_borne(id_borne: int, db: Session = Depends(get_db)):
    crud.get_or_404(db, Borne, id_borne, "Borne")
    stmt = (
        select(Incident)
        .where(Incident.id_borne == id_borne)
        .order_by(Incident.date_signalement.desc())
    )
    return db.scalars(stmt).all()
