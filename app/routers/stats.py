"""Statistiques : requêtes SQL analytiques écrites à la main (text()).

C'est ici qu'on exploite vraiment PostgreSQL : jointures multiples, GROUP BY / HAVING,
agrégats FILTER, fonctions de fenêtrage (RANK, SUM OVER), CTE, NOT EXISTS, date_trunc...
Tous les paramètres passent par des variables liées (:limit...) : pas d'injection SQL possible.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    BorneClassement,
    BorneProblematique,
    ClientTop,
    IncidentCategorie,
    Resume,
    SessionImpayee,
    SessionsMois,
    StationRevenus,
    TechnicienCharge,
)

router = APIRouter(prefix="/stats", tags=["Statistiques"])


@router.get("/resume", response_model=Resume, summary="Chiffres clés du réseau")
def resume(db: Session = Depends(get_db)):
    sql = text("""
        SELECT
            (SELECT COUNT(*) FROM client)                                   AS nb_clients,
            (SELECT COUNT(*) FROM vehicule)                                 AS nb_vehicules,
            (SELECT COUNT(*) FROM station)                                  AS nb_stations,
            (SELECT COUNT(*) FROM borne)                                    AS nb_bornes,
            (SELECT COUNT(*) FROM borne WHERE etat = 'disponible')          AS nb_bornes_disponibles,
            (SELECT COUNT(*) FROM session_recharge WHERE statut = 'en_cours') AS nb_sessions_en_cours,
            (SELECT COUNT(*) FROM incident WHERE statut = 'ouvert')         AS nb_incidents_ouverts,
            (SELECT COALESCE(SUM(cout_eur), 0)
               FROM session_recharge WHERE statut = 'terminee')             AS chiffre_affaires_eur
    """)
    return db.execute(sql).mappings().one()


@router.get("/stations/revenus", response_model=list[StationRevenus],
            summary="Chiffre d'affaires et énergie par station")
def revenus_par_station(db: Session = Depends(get_db)):
    # LEFT JOIN : une station sans borne ou sans session apparaît quand même (avec des 0)
    sql = text("""
        SELECT s.id_station, s.nom_station, s.ville,
               COUNT(DISTINCT b.id_borne)            AS nb_bornes,
               COUNT(sr.id_session)                  AS nb_sessions,
               COALESCE(SUM(sr.energie_kwh), 0)      AS energie_kwh,
               COALESCE(SUM(sr.cout_eur), 0)         AS chiffre_affaires_eur
        FROM station s
        LEFT JOIN borne b ON b.id_station = s.id_station
        LEFT JOIN session_recharge sr
               ON sr.id_borne = b.id_borne AND sr.statut = 'terminee'
        GROUP BY s.id_station, s.nom_station, s.ville
        ORDER BY chiffre_affaires_eur DESC, s.id_station
    """)
    return db.execute(sql).mappings().all()


@router.get("/clients/top", response_model=list[ClientTop],
            summary="Clients qui dépensent le plus")
def top_clients(limit: int = Query(10, ge=1, le=100), db: Session = Depends(get_db)):
    sql = text("""
        SELECT c.id_client, c.prenom, c.nom,
               COUNT(sr.id_session)                AS nb_sessions,
               COALESCE(SUM(sr.energie_kwh), 0)    AS energie_kwh,
               COALESCE(SUM(sr.cout_eur), 0)       AS depense_eur
        FROM client c
        JOIN vehicule v          ON v.id_client = c.id_client
        JOIN session_recharge sr ON sr.id_vehicule = v.id_vehicule
        WHERE sr.statut = 'terminee'
        GROUP BY c.id_client, c.prenom, c.nom
        ORDER BY depense_eur DESC, c.id_client
        LIMIT :limit
    """)
    return db.execute(sql, {"limit": limit}).mappings().all()


@router.get("/bornes/classement", response_model=list[BorneClassement],
            summary="Classement des bornes par énergie délivrée, au sein de chaque station")
def classement_bornes(db: Session = Depends(get_db)):
    # RANK() OVER (PARTITION BY ...) : fonction de fenêtrage, un classement par station
    sql = text("""
        SELECT b.id_borne, b.code_borne, s.nom_station, b.puissance_kw,
               COUNT(sr.id_session)                 AS nb_sessions,
               COALESCE(SUM(sr.energie_kwh), 0)     AS energie_kwh,
               RANK() OVER (
                   PARTITION BY s.id_station
                   ORDER BY COALESCE(SUM(sr.energie_kwh), 0) DESC
               )                                    AS rang_dans_station
        FROM borne b
        JOIN station s ON s.id_station = b.id_station
        LEFT JOIN session_recharge sr
               ON sr.id_borne = b.id_borne AND sr.statut = 'terminee'
        GROUP BY s.id_station, s.nom_station, b.id_borne, b.code_borne, b.puissance_kw
        ORDER BY s.nom_station, rang_dans_station, b.code_borne
    """)
    return db.execute(sql).mappings().all()


@router.get("/bornes/problematiques", response_model=list[BorneProblematique],
            summary="Bornes ayant au moins N incidents")
def bornes_problematiques(
    min_incidents: int = Query(2, ge=1), db: Session = Depends(get_db)
):
    # HAVING filtre APRÈS l'agrégation (WHERE filtre avant)
    sql = text("""
        SELECT b.id_borne, b.code_borne, s.nom_station,
               COUNT(i.id_incident)      AS nb_incidents,
               MAX(i.date_signalement)   AS dernier_incident
        FROM borne b
        JOIN station s  ON s.id_station = b.id_station
        JOIN incident i ON i.id_borne = b.id_borne
        GROUP BY b.id_borne, b.code_borne, s.nom_station
        HAVING COUNT(i.id_incident) >= :min_incidents
        ORDER BY nb_incidents DESC, b.id_borne
    """)
    return db.execute(sql, {"min_incidents": min_incidents}).mappings().all()


@router.get("/incidents/par-categorie", response_model=list[IncidentCategorie],
            summary="Incidents par catégorie et gravité, avec durée moyenne de résolution")
def incidents_par_categorie(db: Session = Depends(get_db)):
    sql = text("""
        SELECT categorie, gravite,
               COUNT(*)                                   AS nb_incidents,
               COUNT(*) FILTER (WHERE statut = 'ouvert')  AS nb_ouverts,
               ROUND(AVG(EXTRACT(EPOCH FROM (date_resolution - date_signalement)) / 3600)::numeric, 2)
                                                          AS duree_moy_resolution_h
        FROM incident
        GROUP BY categorie, gravite
        ORDER BY categorie,
                 CASE gravite WHEN 'haute' THEN 1 WHEN 'moyenne' THEN 2 ELSE 3 END
    """)
    return db.execute(sql).mappings().all()


@router.get("/sessions/mensuel", response_model=list[SessionsMois],
            summary="Évolution mensuelle (sessions, énergie, CA) avec CA cumulé")
def sessions_mensuelles(db: Session = Depends(get_db)):
    # CTE (WITH) pour agréger par mois, puis SUM() OVER (ORDER BY ...) pour le cumul
    sql = text("""
        WITH mensuel AS (
            SELECT date_trunc('month', debut_session) AS mois_debut,
                   COUNT(*)                           AS nb_sessions,
                   COALESCE(SUM(energie_kwh), 0)      AS energie_kwh,
                   COALESCE(SUM(cout_eur), 0)         AS chiffre_affaires_eur
            FROM session_recharge
            WHERE statut = 'terminee'
            GROUP BY date_trunc('month', debut_session)
        )
        SELECT to_char(mois_debut, 'YYYY-MM')                         AS mois,
               nb_sessions, energie_kwh, chiffre_affaires_eur,
               SUM(chiffre_affaires_eur) OVER (ORDER BY mois_debut)   AS ca_cumule_eur
        FROM mensuel
        ORDER BY mois_debut
    """)
    return db.execute(sql).mappings().all()


@router.get("/sessions/impayees", response_model=list[SessionImpayee],
            summary="Sessions terminées et facturées mais sans aucun paiement")
def sessions_impayees(limit: int = Query(50, ge=1, le=500), db: Session = Depends(get_db)):
    sql = text("""
        SELECT sr.id_session, c.id_client, c.prenom, c.nom, sr.fin_session, sr.cout_eur
        FROM session_recharge sr
        JOIN vehicule v ON v.id_vehicule = sr.id_vehicule
        JOIN client c   ON c.id_client = v.id_client
        WHERE sr.statut = 'terminee'
          AND COALESCE(sr.cout_eur, 0) > 0
          AND NOT EXISTS (SELECT 1 FROM paiement p WHERE p.id_session = sr.id_session)
        ORDER BY sr.fin_session DESC NULLS LAST
        LIMIT :limit
    """)
    return db.execute(sql, {"limit": limit}).mappings().all()


@router.get("/techniciens/charge", response_model=list[TechnicienCharge],
            summary="Charge de travail des techniciens")
def charge_techniciens(db: Session = Depends(get_db)):
    sql = text("""
        SELECT t.id_technicien, t.prenom, t.nom,
               COUNT(it.id_intervention)                                  AS nb_interventions,
               COUNT(it.id_intervention) FILTER (WHERE it.date_fin IS NULL) AS nb_en_cours,
               ROUND(AVG(EXTRACT(EPOCH FROM (it.date_fin - it.date_debut)) / 3600)::numeric, 2)
                                                                          AS duree_moy_h
        FROM technicien t
        LEFT JOIN intervention it ON it.id_technicien = t.id_technicien
        GROUP BY t.id_technicien, t.prenom, t.nom
        ORDER BY nb_interventions DESC, t.id_technicien
    """)
    return db.execute(sql).mappings().all()
