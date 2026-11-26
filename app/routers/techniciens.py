from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import crud
from app.crud import Page
from app.database import get_db
from app.models import Intervention, Technicien
from app.schemas import InterventionRead, TechnicienCreate, TechnicienRead, TechnicienUpdate

router = APIRouter(prefix="/techniciens", tags=["Techniciens"])


@router.get("", response_model=list[TechnicienRead], summary="Lister les techniciens")
def lister_techniciens(page: Page = Depends(), db: Session = Depends(get_db)):
    stmt = select(Technicien).order_by(Technicien.id_technicien)
    return crud.paginate(db, stmt, page)


@router.get("/{id_technicien}", response_model=TechnicienRead, summary="Détail d'un technicien")
def lire_technicien(id_technicien: int, db: Session = Depends(get_db)):
    return crud.get_or_404(db, Technicien, id_technicien, "Technicien")


@router.post("", response_model=TechnicienRead, status_code=status.HTTP_201_CREATED,
             summary="Créer un technicien")
def creer_technicien(data: TechnicienCreate, db: Session = Depends(get_db)):
    return crud.create(db, Technicien, data)


@router.patch("/{id_technicien}", response_model=TechnicienRead, summary="Modifier un technicien")
def modifier_technicien(id_technicien: int, data: TechnicienUpdate, db: Session = Depends(get_db)):
    technicien = crud.get_or_404(db, Technicien, id_technicien, "Technicien")
    return crud.update(db, technicien, data)


@router.delete("/{id_technicien}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Supprimer un technicien (refusé s'il a des interventions)")
def supprimer_technicien(id_technicien: int, db: Session = Depends(get_db)):
    crud.delete(db, crud.get_or_404(db, Technicien, id_technicien, "Technicien"))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{id_technicien}/interventions", response_model=list[InterventionRead],
            summary="Interventions d'un technicien")
def interventions_du_technicien(
    id_technicien: int, page: Page = Depends(), db: Session = Depends(get_db)
):
    crud.get_or_404(db, Technicien, id_technicien, "Technicien")
    stmt = (
        select(Intervention)
        .where(Intervention.id_technicien == id_technicien)
        .order_by(Intervention.date_debut.desc())
    )
    return crud.paginate(db, stmt, page)
