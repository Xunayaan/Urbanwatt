from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import crud
from app.crud import Page
from app.database import get_db
from app.models import Intervention
from app.schemas import (
    InterventionCloture,
    InterventionCreate,
    InterventionRead,
    InterventionUpdate,
)

router = APIRouter(prefix="/interventions", tags=["Interventions"])


@router.get("", response_model=list[InterventionRead], summary="Lister les interventions")
def lister_interventions(
    id_incident: int | None = None,
    id_technicien: int | None = None,
    statut: str | None = None,
    en_cours: bool | None = None,
    page: Page = Depends(),
    db: Session = Depends(get_db),
):
    stmt = select(Intervention).order_by(Intervention.date_debut.desc())
    if id_incident is not None:
        stmt = stmt.where(Intervention.id_incident == id_incident)
    if id_technicien is not None:
        stmt = stmt.where(Intervention.id_technicien == id_technicien)
    if statut:
        stmt = stmt.where(Intervention.statut == statut)
    if en_cours is True:
        stmt = stmt.where(Intervention.date_fin.is_(None))
    elif en_cours is False:
        stmt = stmt.where(Intervention.date_fin.is_not(None))
    return crud.paginate(db, stmt, page)


@router.get("/{id_intervention}", response_model=InterventionRead,
            summary="Détail d'une intervention")
def lire_intervention(id_intervention: int, db: Session = Depends(get_db)):
    return crud.get_or_404(db, Intervention, id_intervention, "Intervention")


@router.post("", response_model=InterventionRead, status_code=status.HTTP_201_CREATED,
             summary="Créer une intervention")
def creer_intervention(data: InterventionCreate, db: Session = Depends(get_db)):
    return crud.create(db, Intervention, data)


@router.post("/{id_intervention}/cloturer", response_model=InterventionRead,
             summary="Clôturer une intervention (date de fin = maintenant)")
def cloturer_intervention(
    id_intervention: int, data: InterventionCloture, db: Session = Depends(get_db)
):
    intervention = crud.get_or_404(db, Intervention, id_intervention, "Intervention", for_update=True)
    if intervention.date_fin is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Intervention déjà clôturée")
    intervention.date_fin = datetime.now()
    intervention.statut = "terminee"
    if data.compte_rendu is not None:
        intervention.compte_rendu = data.compte_rendu
    db.commit()
    db.refresh(intervention)
    return intervention


@router.patch("/{id_intervention}", response_model=InterventionRead,
              summary="Modifier une intervention")
def modifier_intervention(
    id_intervention: int, data: InterventionUpdate, db: Session = Depends(get_db)
):
    intervention = crud.get_or_404(db, Intervention, id_intervention, "Intervention")
    return crud.update(db, intervention, data)


@router.delete("/{id_intervention}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Supprimer une intervention")
def supprimer_intervention(id_intervention: int, db: Session = Depends(get_db)):
    crud.delete(db, crud.get_or_404(db, Intervention, id_intervention, "Intervention"))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
