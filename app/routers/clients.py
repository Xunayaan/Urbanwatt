from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app import crud
from app.crud import Page
from app.database import get_db
from app.models import Client, SessionRecharge, Vehicule
from app.schemas import (
    ClientCreate,
    ClientRead,
    ClientUpdate,
    SessionRead,
    VehiculeRead,
)

router = APIRouter(prefix="/clients", tags=["Clients"])


@router.get("", response_model=list[ClientRead], summary="Lister les clients")
def lister_clients(
    ville: str | None = Query(None, description="Filtre exact (insensible à la casse)"),
    recherche: str | None = Query(None, description="Cherche dans nom, prénom et email"),
    page: Page = Depends(),
    db: Session = Depends(get_db),
):
    stmt = select(Client).order_by(Client.id_client)
    if ville:
        stmt = stmt.where(func.lower(Client.ville) == ville.lower())
    if recherche:
        motif = f"%{recherche}%"
        stmt = stmt.where(
            or_(Client.nom.ilike(motif), Client.prenom.ilike(motif), Client.email.ilike(motif))
        )
    return crud.paginate(db, stmt, page)


@router.get("/{id_client}", response_model=ClientRead, summary="Détail d'un client")
def lire_client(id_client: int, db: Session = Depends(get_db)):
    return crud.get_or_404(db, Client, id_client, "Client")


@router.post("", response_model=ClientRead, status_code=status.HTTP_201_CREATED,
             summary="Créer un client")
def creer_client(data: ClientCreate, db: Session = Depends(get_db)):
    return crud.create(db, Client, data)


@router.patch("/{id_client}", response_model=ClientRead, summary="Modifier un client (partiel)")
def modifier_client(id_client: int, data: ClientUpdate, db: Session = Depends(get_db)):
    client = crud.get_or_404(db, Client, id_client, "Client")
    return crud.update(db, client, data)


@router.delete("/{id_client}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Supprimer un client (refusé s'il possède des véhicules)")
def supprimer_client(id_client: int, db: Session = Depends(get_db)):
    crud.delete(db, crud.get_or_404(db, Client, id_client, "Client"))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{id_client}/vehicules", response_model=list[VehiculeRead],
            summary="Véhicules d'un client")
def vehicules_du_client(id_client: int, db: Session = Depends(get_db)):
    crud.get_or_404(db, Client, id_client, "Client")
    stmt = select(Vehicule).where(Vehicule.id_client == id_client).order_by(Vehicule.id_vehicule)
    return db.scalars(stmt).all()


@router.get("/{id_client}/sessions", response_model=list[SessionRead],
            summary="Historique de recharge d'un client (jointure vehicule -> session)")
def sessions_du_client(id_client: int, page: Page = Depends(), db: Session = Depends(get_db)):
    crud.get_or_404(db, Client, id_client, "Client")
    stmt = (
        select(SessionRecharge)
        .join(Vehicule, Vehicule.id_vehicule == SessionRecharge.id_vehicule)
        .where(Vehicule.id_client == id_client)
        .order_by(SessionRecharge.debut_session.desc())
    )
    return crud.paginate(db, stmt, page)
