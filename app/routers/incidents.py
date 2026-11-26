from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import crud
from app.crud import Page
from app.database import get_db
from app.models import Borne, Incident, Intervention
from app.schemas import (
    Gravite,
    IncidentCreate,
    IncidentRead,
    IncidentStatut,
    IncidentUpdate,
    InterventionRead,
)

router = APIRouter(prefix="/incidents", tags=["Incidents"])


@router.get("", response_model=list[IncidentRead], summary="Lister les incidents")
def lister_incidents(
    statut: IncidentStatut | None = None,
    gravite: Gravite | None = None,
    categorie: str | None = None,
    id_borne: int | None = None,
    page: Page = Depends(),
    db: Session = Depends(get_db),
):
    stmt = select(Incident).order_by(Incident.date_signalement.desc())
    if statut:
        stmt = stmt.where(Incident.statut == statut)
    if gravite:
        stmt = stmt.where(Incident.gravite == gravite)
    if categorie:
        stmt = stmt.where(func.lower(Incident.categorie) == categorie.lower())
    if id_borne is not None:
        stmt = stmt.where(Incident.id_borne == id_borne)
    return crud.paginate(db, stmt, page)


@router.get("/{id_incident}", response_model=IncidentRead, summary="Détail d'un incident")
def lire_incident(id_incident: int, db: Session = Depends(get_db)):
    return crud.get_or_404(db, Incident, id_incident, "Incident")


@router.post("", response_model=IncidentRead, status_code=status.HTTP_201_CREATED,
             summary="Signaler un incident")
def signaler_incident(data: IncidentCreate, db: Session = Depends(get_db)):
    """Une seule transaction :
    1. verrouille la borne, 2. génère l'id (la table n'a pas d'IDENTITY), 3. insère l'incident,
    4. si gravité = haute (et incident ouvert), passe la borne en `hors_service`.
    Tout est validé par un seul COMMIT : soit tout réussit, soit rien n'est modifié.
    """
    borne = crud.get_or_404(db, Borne, data.id_borne, "Borne", for_update=True)

    valeurs = data.model_dump()
    if valeurs["id_incident"] is None:
        valeurs["id_incident"] = crud.next_id(db, Incident, Incident.id_incident)
    incident = Incident(**valeurs)
    db.add(incident)

    if data.gravite == "haute" and data.statut == "ouvert":
        borne.etat = "hors_service"

    db.commit()
    db.refresh(incident)
    return incident


@router.post("/{id_incident}/resoudre", response_model=IncidentRead,
             summary="Marquer un incident comme résolu")
def resoudre_incident(id_incident: int, db: Session = Depends(get_db)):
    """Passe l'incident à `resolu` ; remet la borne `disponible` s'il ne lui reste
    aucun autre incident ouvert de gravité haute."""
    incident = crud.get_or_404(db, Incident, id_incident, "Incident", for_update=True)
    if incident.statut == "resolu":
        raise HTTPException(status.HTTP_409_CONFLICT, "Incident déjà résolu")

    incident.statut = "resolu"
    incident.date_resolution = datetime.now()
    db.flush()  # envoie l'UPDATE dans la transaction (sans commit) pour que le COUNT ci-dessous le voie

    borne = crud.get_or_404(db, Borne, incident.id_borne, "Borne", for_update=True)
    hauts_ouverts = db.scalar(
        select(func.count())
        .select_from(Incident)
        .where(
            Incident.id_borne == incident.id_borne,
            Incident.statut == "ouvert",
            Incident.gravite == "haute",
        )
    )
    if hauts_ouverts == 0 and borne.etat == "hors_service":
        borne.etat = "disponible"

    db.commit()
    db.refresh(incident)
    return incident


@router.patch("/{id_incident}", response_model=IncidentRead, summary="Modifier un incident")
def modifier_incident(id_incident: int, data: IncidentUpdate, db: Session = Depends(get_db)):
    incident = crud.get_or_404(db, Incident, id_incident, "Incident")
    return crud.update(db, incident, data)


@router.delete("/{id_incident}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Supprimer un incident (refusé s'il a des interventions)")
def supprimer_incident(id_incident: int, db: Session = Depends(get_db)):
    crud.delete(db, crud.get_or_404(db, Incident, id_incident, "Incident"))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{id_incident}/interventions", response_model=list[InterventionRead],
            summary="Interventions liées à un incident")
def interventions_de_l_incident(id_incident: int, db: Session = Depends(get_db)):
    crud.get_or_404(db, Incident, id_incident, "Incident")
    stmt = (
        select(Intervention)
        .where(Intervention.id_incident == id_incident)
        .order_by(Intervention.date_debut)
    )
    return db.scalars(stmt).all()
