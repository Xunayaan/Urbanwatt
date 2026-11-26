"""Modèles ORM : reflètent EXACTEMENT les tables déjà créées par 01_schema.sql.
On ne fait jamais Base.metadata.create_all() : le schéma appartient à la base,
l'API ne fait que le lire / écrire.
"""
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Client(Base):
    __tablename__ = "client"

    id_client: Mapped[int] = mapped_column(primary_key=True)
    prenom: Mapped[str] = mapped_column(String(100))
    nom: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    ville: Mapped[str | None] = mapped_column(String(100))
    date_inscription: Mapped[date]

class Vehicule(Base):
    __tablename__ = "vehicule"
    id_vehicule: Mapped[int] = mapped_column(primary_key=True)
    id_client: Mapped[int] = mapped_column(ForeignKey("client.id_client"))
    immatriculation: Mapped[str] = mapped_column(String(20), unique=True)
    marque: Mapped[str] = mapped_column(String(50))
    modele: Mapped[str] = mapped_column(String(50))
    capacite_batterie_kwh: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))

class Station(Base):
    __tablename__ = "station"
    id_station: Mapped[int] = mapped_column(primary_key=True)
    code_station: Mapped[str] = mapped_column(String(20), unique=True)
    nom_station: Mapped[str] = mapped_column(String(150))
    ville: Mapped[str] = mapped_column(String(100))
    adresse: Mapped[str] = mapped_column(String(255))
    date_ouverture: Mapped[date | None]

class Borne(Base):
    __tablename__ = "borne"
    id_borne: Mapped[int] = mapped_column(primary_key=True)
    id_station: Mapped[int] = mapped_column(ForeignKey("station.id_station"))
    code_borne: Mapped[str] = mapped_column(String(20), unique=True)
    puissance_kw: Mapped[Decimal] = mapped_column(Numeric(6, 1))
    connecteur: Mapped[str] = mapped_column(String(30))
    etat: Mapped[str] = mapped_column(String(30))

class SessionRecharge(Base):
    __tablename__ = "session_recharge"
    id_session: Mapped[int] = mapped_column(primary_key=True)
    id_borne: Mapped[int] = mapped_column(ForeignKey("borne.id_borne"))    
    id_vehicule: Mapped[int] = mapped_column(ForeignKey("vehicule.id_vehicule"))
    debut_session: Mapped[datetime]
    fin_session: Mapped[datetime | None]
    energie_kwh: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    cout_eur: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    statut: Mapped[str] = mapped_column(String(30))

class Paiement(Base):
    __tablename__ = "paiement"
    id_paiement: Mapped[int] = mapped_column(primary_key=True)
    id_session: Mapped[int] = mapped_column(ForeignKey("session_recharge.id_session"))
    date_paiement: Mapped[datetime]
    montant_eur: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    mode_paiement: Mapped[str] = mapped_column(String(30))
    statut: Mapped[str] = mapped_column(String(30))

class Incident(Base):
    __tablename__ = "incident"
    id_incident: Mapped[int] = mapped_column(primary_key=True)
    id_borne: Mapped[int] = mapped_column(ForeignKey("borne.id_borne"))
    date_signalement: Mapped[datetime]
    date_resolution: Mapped[datetime | None]
    categorie: Mapped[str] = mapped_column(String(50))
    gravite: Mapped[str] = mapped_column(String(20))
    statut: Mapped[str] = mapped_column(String(30))
    description: Mapped[str | None] = mapped_column(Text)

class Technicien(Base):
    __tablename__ = "technicien"
    id_technicien: Mapped[int] = mapped_column(primary_key=True)
    prenom: Mapped[str] = mapped_column(String(100))
    nom: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True)

class Intervention(Base):
    __tablename__ = "intervention"
    id_intervention: Mapped[int] = mapped_column(primary_key=True)
    id_incident: Mapped[int] = mapped_column(ForeignKey("incident.id_incident"))
    id_technicien: Mapped[int] = mapped_column(ForeignKey("technicien.id_technicien"))
    date_debut: Mapped[datetime]
    date_fin: Mapped[datetime | None]
    statut: Mapped[str] = mapped_column(String(30))
    compte_rendu: Mapped[str | None] = mapped_column(Text)

