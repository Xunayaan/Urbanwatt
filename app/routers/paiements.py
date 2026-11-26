from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import crud
from app.crud import Page
from app.database import get_db
from app.models import Paiement
from app.schemas import PaiementCreate, PaiementRead, PaiementUpdate

router = APIRouter(prefix="/paiements", tags=["Paiements"])


@router.get("", response_model=list[PaiementRead], summary="Lister les paiements")
def lister_paiements(
    id_session: int | None = None,
    statut: str | None = None,
    mode_paiement: str | None = None,
    page: Page = Depends(),
    db: Session = Depends(get_db),
):
    stmt = select(Paiement).order_by(Paiement.date_paiement.desc())
    if id_session is not None:
        stmt = stmt.where(Paiement.id_session == id_session)
    if statut:
        stmt = stmt.where(Paiement.statut == statut)
    if mode_paiement:
        stmt = stmt.where(Paiement.mode_paiement == mode_paiement)
    return crud.paginate(db, stmt, page)


@router.get("/{id_paiement}", response_model=PaiementRead, summary="Détail d'un paiement")
def lire_paiement(id_paiement: int, db: Session = Depends(get_db)):
    return crud.get_or_404(db, Paiement, id_paiement, "Paiement")


@router.post("", response_model=PaiementRead, status_code=status.HTTP_201_CREATED,
             summary="Enregistrer un paiement")
def creer_paiement(data: PaiementCreate, db: Session = Depends(get_db)):
    return crud.create(db, Paiement, data)


@router.patch("/{id_paiement}", response_model=PaiementRead, summary="Modifier un paiement")
def modifier_paiement(id_paiement: int, data: PaiementUpdate, db: Session = Depends(get_db)):
    paiement = crud.get_or_404(db, Paiement, id_paiement, "Paiement")
    return crud.update(db, paiement, data)


@router.delete("/{id_paiement}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Supprimer un paiement")
def supprimer_paiement(id_paiement: int, db: Session = Depends(get_db)):
    crud.delete(db, crud.get_or_404(db, Paiement, id_paiement, "Paiement"))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
