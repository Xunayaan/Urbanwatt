"""Schémas Pydantic : ce que l'API accepte (Create / Update) et renvoie (Read).

Les Literal reprennent les contraintes CHECK ajoutées dans 01_schema.sql :
l'API refuse une valeur invalide (422) avant même d'interroger la base.
"""
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

SessionStatut = Literal["annulee", "terminee", "interrompue", "en_cours"]
IncidentStatut = Literal["ouvert", "resolu"]
BorneEtat = Literal["disponible", "hors_service", "maintenance"]
Gravite = Literal["faible", "moyenne", "haute"]


class ORMModel(BaseModel):
    """Base des schémas de lecture : permet de construire le schéma depuis un objet SQLAlchemy."""

    model_config = ConfigDict(from_attributes=True)


# ------------------------------------------------------------------ CLIENT
class ClientCreate(BaseModel):
    prenom: str = Field(min_length=1, max_length=100)
    nom: str = Field(min_length=1, max_length=100)
    email: EmailStr
    ville: str | None = Field(default=None, max_length=100)
    date_inscription: date = Field(default_factory=date.today)


class ClientUpdate(BaseModel):
    prenom: str | None = Field(default=None, min_length=1, max_length=100)
    nom: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = None
    ville: str | None = Field(default=None, max_length=100)


class ClientRead(ORMModel):
    id_client: int
    prenom: str
    nom: str
    email: str
    ville: str | None
    date_inscription: date


# ---------------------------------------------------------------- VEHICULE
class VehiculeCreate(BaseModel):
    id_client: int
    immatriculation: str = Field(min_length=1, max_length=20)
    marque: str = Field(min_length=1, max_length=50)
    modele: str = Field(min_length=1, max_length=50)
    capacite_batterie_kwh: float | None = Field(default=None, gt=0)


class VehiculeUpdate(BaseModel):
    id_client: int | None = None
    immatriculation: str | None = Field(default=None, min_length=1, max_length=20)
    marque: str | None = Field(default=None, min_length=1, max_length=50)
    modele: str | None = Field(default=None, min_length=1, max_length=50)
    capacite_batterie_kwh: float | None = Field(default=None, gt=0)


class VehiculeRead(ORMModel):
    id_vehicule: int
    id_client: int
    immatriculation: str
    marque: str
    modele: str
    capacite_batterie_kwh: float | None


# ----------------------------------------------------------------- STATION
class StationCreate(BaseModel):
    code_station: str = Field(min_length=1, max_length=20)
    nom_station: str = Field(min_length=1, max_length=150)
    ville: str = Field(min_length=1, max_length=100)
    adresse: str = Field(min_length=1, max_length=255)
    date_ouverture: date | None = None


class StationUpdate(BaseModel):
    code_station: str | None = Field(default=None, min_length=1, max_length=20)
    nom_station: str | None = Field(default=None, min_length=1, max_length=150)
    ville: str | None = Field(default=None, min_length=1, max_length=100)
    adresse: str | None = Field(default=None, min_length=1, max_length=255)
    date_ouverture: date | None = None


class StationRead(ORMModel):
    id_station: int
    code_station: str
    nom_station: str
    ville: str
    adresse: str
    date_ouverture: date | None


# ------------------------------------------------------------------- BORNE
class BorneCreate(BaseModel):
    id_station: int
    code_borne: str = Field(min_length=1, max_length=20)
    puissance_kw: float = Field(gt=0)
    connecteur: str = Field(min_length=1, max_length=30)
    etat: BorneEtat = "disponible"


class BorneUpdate(BaseModel):
    id_station: int | None = None
    code_borne: str | None = Field(default=None, min_length=1, max_length=20)
    puissance_kw: float | None = Field(default=None, gt=0)
    connecteur: str | None = Field(default=None, min_length=1, max_length=30)
    etat: BorneEtat | None = None


class BorneEtatUpdate(BaseModel):
    etat: BorneEtat


class BorneRead(ORMModel):
    id_borne: int
    id_station: int
    code_borne: str
    puissance_kw: float
    connecteur: str
    etat: str


# ----------------------------------------------------------------- SESSION
class SessionCreate(BaseModel):
    id_borne: int
    id_vehicule: int
    debut_session: datetime = Field(default_factory=datetime.now)
    statut: SessionStatut = "en_cours"
    fin_session: datetime | None = None
    energie_kwh: float | None = Field(default=None, ge=0)
    cout_eur: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def fin_apres_debut(self):
        if self.fin_session is not None and self.fin_session < self.debut_session:
            raise ValueError("fin_session doit être postérieure à debut_session")
        return self


class SessionUpdate(BaseModel):
    id_borne: int | None = None
    id_vehicule: int | None = None
    debut_session: datetime | None = None
    fin_session: datetime | None = None
    energie_kwh: float | None = Field(default=None, ge=0)
    cout_eur: float | None = Field(default=None, ge=0)
    statut: SessionStatut | None = None


class SessionTerminer(BaseModel):
    energie_kwh: float = Field(ge=0)
    cout_eur: float | None = Field(default=None, ge=0)
    fin_session: datetime | None = Field(default=None, description="Par défaut : maintenant")


class SessionRead(ORMModel):
    id_session: int
    id_borne: int
    id_vehicule: int
    debut_session: datetime
    fin_session: datetime | None
    energie_kwh: float | None
    cout_eur: float | None
    statut: str


class SessionDetail(BaseModel):
    """Session + informations des 4 tables liées (obtenu par jointures)."""

    id_session: int
    debut_session: datetime
    fin_session: datetime | None
    energie_kwh: float | None
    cout_eur: float | None
    statut: str
    code_borne: str
    puissance_kw: float
    connecteur: str
    id_station: int
    nom_station: str
    ville_station: str
    id_vehicule: int
    immatriculation: str
    marque: str
    modele: str
    id_client: int
    prenom_client: str
    nom_client: str


#--------------------------------------------------------------- PAIEMENT
class PaiementCreate(BaseModel):
    id_session: int
    date_paiement: datetime = Field(default_factory=datetime.now)
    montant_eur: float = Field(ge=0)
    mode_paiement: str = Field(min_length=1, max_length=30, examples=["carte"])
    statut: str = Field(min_length=1, max_length=30, examples=["valide"])


class PaiementUpdate(BaseModel):
    id_session: int | None = None
    date_paiement: datetime | None = None
    montant_eur: float | None = Field(default=None, ge=0)
    mode_paiement: str | None = Field(default=None, min_length=1, max_length=30)
    statut: str | None = Field(default=None, min_length=1, max_length=30)


class PaiementRead(ORMModel):
    id_paiement: int
    id_session: int
    date_paiement: datetime
    montant_eur: float
    mode_paiement: str
    statut: str


# --------------------------------------------------------------- INCIDENT A MODIFIER POUR L'ID ??
class IncidentCreate(BaseModel):
    id_incident: int | None = Field(
        default=None, description="Optionnel : généré automatiquement (max+1) si absent"
    )
    id_borne: int
    date_signalement: datetime = Field(default_factory=datetime.now)
    categorie: str = Field(min_length=1, max_length=50)
    gravite: Gravite
    statut: IncidentStatut = "ouvert"
    description: str | None = None


class IncidentUpdate(BaseModel):
    id_borne: int | None = None
    date_signalement: datetime | None = None
    date_resolution: datetime | None = None
    categorie: str | None = Field(default=None, min_length=1, max_length=50)
    gravite: Gravite | None = None
    statut: IncidentStatut | None = None
    description: str | None = None


class IncidentRead(ORMModel):
    id_incident: int
    id_borne: int
    date_signalement: datetime
    date_resolution: datetime | None
    categorie: str
    gravite: str
    statut: str
    description: str | None


# ------------------------------------------------------------- TECHNICIEN
class TechnicienCreate(BaseModel):
    prenom: str = Field(min_length=1, max_length=100)
    nom: str = Field(min_length=1, max_length=100)
    email: EmailStr


class TechnicienUpdate(BaseModel):
    prenom: str | None = Field(default=None, min_length=1, max_length=100)
    nom: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = None


class TechnicienRead(ORMModel):
    id_technicien: int
    prenom: str
    nom: str
    email: str


# ----------------------------------------------------------- INTERVENTION
class InterventionCreate(BaseModel):
    id_incident: int
    id_technicien: int
    date_debut: datetime = Field(default_factory=datetime.now)
    date_fin: datetime | None = None
    statut: str = Field(default="planifiee", min_length=1, max_length=30)
    compte_rendu: str | None = None

    @model_validator(mode="after")
    def fin_apres_debut(self):
        if self.date_fin is not None and self.date_fin < self.date_debut:
            raise ValueError("date_fin doit être postérieure à date_debut")
        return self


class InterventionUpdate(BaseModel):
    id_incident: int | None = None
    id_technicien: int | None = None
    date_debut: datetime | None = None
    date_fin: datetime | None = None
    statut: str | None = Field(default=None, min_length=1, max_length=30)
    compte_rendu: str | None = None


class InterventionCloture(BaseModel):
    compte_rendu: str | None = None


class InterventionRead(ORMModel):
    id_intervention: int
    id_incident: int
    id_technicien: int
    date_debut: datetime
    date_fin: datetime | None
    statut: str
    compte_rendu: str | None


# ------------------------------------------------------------------ STATS
class Resume(BaseModel):
    nb_clients: int
    nb_vehicules: int
    nb_stations: int
    nb_bornes: int
    nb_bornes_disponibles: int
    nb_sessions_en_cours: int
    nb_incidents_ouverts: int
    chiffre_affaires_eur: float


class StationRevenus(BaseModel):
    id_station: int
    nom_station: str
    ville: str
    nb_bornes: int
    nb_sessions: int
    energie_kwh: float
    chiffre_affaires_eur: float


class ClientTop(BaseModel):
    id_client: int
    prenom: str
    nom: str
    nb_sessions: int
    energie_kwh: float
    depense_eur: float


class BorneClassement(BaseModel):
    id_borne: int
    code_borne: str
    nom_station: str
    puissance_kw: float
    nb_sessions: int
    energie_kwh: float
    rang_dans_station: int


class IncidentCategorie(BaseModel):
    categorie: str
    gravite: str
    nb_incidents: int
    nb_ouverts: int
    duree_moy_resolution_h: float | None


class BorneProblematique(BaseModel):
    id_borne: int
    code_borne: str
    nom_station: str
    nb_incidents: int
    dernier_incident: datetime


class SessionsMois(BaseModel):
    mois: str
    nb_sessions: int
    energie_kwh: float
    chiffre_affaires_eur: float
    ca_cumule_eur: float


class SessionImpayee(BaseModel):
    id_session: int
    id_client: int
    prenom: str
    nom: str
    fin_session: datetime | None
    cout_eur: float


class TechnicienCharge(BaseModel):
    id_technicien: int
    prenom: str
    nom: str
    nb_interventions: int
    nb_en_cours: int
    duree_moy_h: float | None
