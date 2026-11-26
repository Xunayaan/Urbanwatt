from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app import crud
from app.crud import Page
from app.database import get_db
from app.models import Borne, Client, Paiement, SessionRecharge, Station, Vehicule
from app.schemas import (
    PaiementRead,
    SessionCreate,
    SessionDetail,
    SessionRead,
    SessionStatut,
    SessionTerminer,
    SessionUpdate,
)

router = APIRouter(prefix="/sessions", tags=["Sessions de recharge"])


@router.get("", response_model=list[SessionRead], summary="Lister les sessions (avec filtres)")
def lister_sessions(
    statut: SessionStatut | None = None,
    id_borne: int | None = None,
    id_vehicule: int | None = None,
    depuis: datetime | None = None,
    jusqua: datetime | None = None,
    page: Page = Depends(),
    db: Session = Depends(get_db),
):
    stmt = select(SessionRecharge).order_by(SessionRecharge.debut_session.desc())
    if statut:
        stmt = stmt.where(SessionRecharge.statut == statut)
    if id_borne is not None:
        stmt = stmt.where(SessionRecharge.id_borne == id_borne)
    if id_vehicule is not None:
        stmt = stmt.where(SessionRecharge.id_vehicule == id_vehicule)
    if depuis:
        stmt = stmt.where(SessionRecharge.debut_session >= depuis)
    if jusqua:
        stmt = stmt.where(SessionRecharge.debut_session <= jusqua)
    return crud.paginate(db, stmt, page)


@router.get("/{id_session}", response_model=SessionRead, summary="Détail d'une session")
def lire_session(id_session: int, db: Session = Depends(get_db)):
    return crud.get_or_404(db, SessionRecharge, id_session, "Session")


@router.get("/{id_session}/details", response_model=SessionDetail,
            summary="Session + borne + station + véhicule + client (5 tables jointes)")
def details_session(id_session: int, db: Session = Depends(get_db)):
    stmt = (
        select(
            SessionRecharge.id_session,
            SessionRecharge.debut_session,
            SessionRecharge.fin_session,
            SessionRecharge.energie_kwh,
            SessionRecharge.cout_eur,
            SessionRecharge.statut,
            Borne.code_borne,
            Borne.puissance_kw,
            Borne.connecteur,
            Station.id_station,
            Station.nom_station,
            Station.ville.label("ville_station"),
            Vehicule.id_vehicule,
            Vehicule.immatriculation,
            Vehicule.marque,
            Vehicule.modele,
            Client.id_client,
            Client.prenom.label("prenom_client"),
            Client.nom.label("nom_client"),
        )
        .join(Borne, Borne.id_borne == SessionRecharge.id_borne)
        .join(Station, Station.id_station == Borne.id_station)
        .join(Vehicule, Vehicule.id_vehicule == SessionRecharge.id_vehicule)
        .join(Client, Client.id_client == Vehicule.id_client)
        .where(SessionRecharge.id_session == id_session)
    )
    ligne = db.execute(stmt).mappings().first()
    if ligne is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Session {id_session} introuvable")
    return ligne


@router.post("", response_model=SessionRead, status_code=status.HTTP_201_CREATED,
             summary="Démarrer (ou enregistrer) une session de recharge")
def creer_session(data: SessionCreate, db: Session = Depends(get_db)):
    """Règles métier appliquées quand la session démarre (statut = en_cours) :
    - la borne doit être `disponible`
    - la borne ne doit pas déjà avoir une session en cours
    - le véhicule ne doit pas déjà être en train de charger
    """
    if data.statut == "en_cours":
        # FOR UPDATE sur la borne : deux démarrages simultanés sur la même borne sont sérialisés
        borne = crud.get_or_404(db, Borne, data.id_borne, "Borne", for_update=True)
        crud.get_or_404(db, Vehicule, data.id_vehicule, "Véhicule")

        if borne.etat != "disponible":
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                f"Borne {borne.code_borne} indisponible (état : {borne.etat})",
            )
        en_cours = db.execute(
            select(SessionRecharge.id_borne, SessionRecharge.id_vehicule).where(
                SessionRecharge.statut == "en_cours",
                or_(
                    SessionRecharge.id_borne == data.id_borne,
                    SessionRecharge.id_vehicule == data.id_vehicule,
                ),
            )
        ).first()
        if en_cours is not None:
            cause = "La borne" if en_cours.id_borne == data.id_borne else "Le véhicule"
            raise HTTPException(status.HTTP_409_CONFLICT, f"{cause} a déjà une session en cours")

    return crud.create(db, SessionRecharge, data)


@router.post("/{id_session}/terminer", response_model=SessionRead,
             summary="Terminer une session en cours (énergie, coût, heure de fin)")
def terminer_session(id_session: int, data: SessionTerminer, db: Session = Depends(get_db)):
    session = crud.get_or_404(db, SessionRecharge, id_session, "Session", for_update=True)
    if session.statut != "en_cours":
        raise HTTPException(
            status.HTTP_409_CONFLICT, f"Session non terminable (statut : {session.statut})"
        )
    session.fin_session = data.fin_session or datetime.now()
    session.energie_kwh = data.energie_kwh
    session.cout_eur = data.cout_eur
    session.statut = "terminee"
    db.commit()  # CHECK fin >= debut vérifié par PostgreSQL -> 422 sinon
    db.refresh(session)
    return session


@router.post("/{id_session}/annuler", response_model=SessionRead,
             summary="Annuler une session en cours")
def annuler_session(id_session: int, db: Session = Depends(get_db)):
    session = crud.get_or_404(db, SessionRecharge, id_session, "Session", for_update=True)
    if session.statut != "en_cours":
        raise HTTPException(
            status.HTTP_409_CONFLICT, f"Session non annulable (statut : {session.statut})"
        )
    session.statut = "annulee"
    session.fin_session = datetime.now()
    db.commit()
    db.refresh(session)
    return session


@router.patch("/{id_session}", response_model=SessionRead,
              summary="Modifier une session (correction manuelle)")
def modifier_session(id_session: int, data: SessionUpdate, db: Session = Depends(get_db)):
    session = crud.get_or_404(db, SessionRecharge, id_session, "Session")
    return crud.update(db, session, data)


@router.delete("/{id_session}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Supprimer une session (refusé si elle a des paiements)")
def supprimer_session(id_session: int, db: Session = Depends(get_db)):
    crud.delete(db, crud.get_or_404(db, SessionRecharge, id_session, "Session"))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{id_session}/paiements", response_model=list[PaiementRead],
            summary="Paiements d'une session")
def paiements_de_la_session(id_session: int, db: Session = Depends(get_db)):
    crud.get_or_404(db, SessionRecharge, id_session, "Session")
    stmt = select(Paiement).where(Paiement.id_session == id_session).order_by(Paiement.date_paiement)
    return db.scalars(stmt).all()
