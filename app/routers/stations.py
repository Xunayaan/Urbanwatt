from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import crud
from app.crud import Page
from app.database import get_db
from app.models import Borne, Station
from app.schemas import BorneEtat, BorneRead, StationCreate, StationRead, StationUpdate

router = APIRouter(prefix="/stations", tags=["Stations"])


@router.get("", response_model=list[StationRead], summary="Lister les stations")
def lister_stations(
    ville: str | None = Query(None, description="Filtre exact (insensible à la casse)"),
    page: Page = Depends(),
    db: Session = Depends(get_db),
):
    stmt = select(Station).order_by(Station.id_station)
    if ville:
        stmt = stmt.where(func.lower(Station.ville) == ville.lower())
    return crud.paginate(db, stmt, page)


@router.get("/{id_station}", response_model=StationRead, summary="Détail d'une station")
def lire_station(id_station: int, db: Session = Depends(get_db)):
    return crud.get_or_404(db, Station, id_station, "Station")


@router.post("", response_model=StationRead, status_code=status.HTTP_201_CREATED,
             summary="Créer une station")
def creer_station(data: StationCreate, db: Session = Depends(get_db)):
    return crud.create(db, Station, data)


@router.patch("/{id_station}", response_model=StationRead, summary="Modifier une station")
def modifier_station(id_station: int, data: StationUpdate, db: Session = Depends(get_db)):
    station = crud.get_or_404(db, Station, id_station, "Station")
    return crud.update(db, station, data)


@router.delete("/{id_station}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Supprimer une station (refusé si elle a des bornes)")
def supprimer_station(id_station: int, db: Session = Depends(get_db)):
    crud.delete(db, crud.get_or_404(db, Station, id_station, "Station"))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{id_station}/bornes", response_model=list[BorneRead],
            summary="Bornes d'une station")
def bornes_de_la_station(
    id_station: int,
    etat: BorneEtat | None = None,
    db: Session = Depends(get_db),
):
    crud.get_or_404(db, Station, id_station, "Station")
    stmt = select(Borne).where(Borne.id_station == id_station).order_by(Borne.id_borne)
    if etat:
        stmt = stmt.where(Borne.etat == etat)
    return db.scalars(stmt).all()
