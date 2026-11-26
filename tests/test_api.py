"""Tests d'intégration : scénario complet sur la vraie base PostgreSQL."""
import uuid

import pytest


def uid() -> str:
    return uuid.uuid4().hex[:8]


@pytest.fixture
def donnees(client):
    """Crée client + véhicule + station + borne, puis nettoie tout (ordre inverse des FK)."""
    s = uid()
    c = client.post("/clients", json={"prenom": "Test", "nom": "Pytest", "email": f"{s}@test.fr",
                                      "ville": "Lyon"}).json()
    v = client.post("/vehicules", json={"id_client": c["id_client"], "immatriculation": f"T-{s}",
                                        "marque": "Tesla", "modele": "Model 3",
                                        "capacite_batterie_kwh": 60}).json()
    st = client.post("/stations", json={"code_station": f"ST-{s}", "nom_station": "Station test",
                                        "ville": "Lyon", "adresse": "1 rue du Test"}).json()
    b = client.post("/bornes", json={"id_station": st["id_station"], "code_borne": f"B-{s}",
                                     "puissance_kw": 22, "connecteur": "Type2"}).json()
    ctx = {"client": c, "vehicule": v, "station": st, "borne": b, "sessions": [], "incidents": [],
           "paiements": [], "autres": []}
    yield ctx

    for p in ctx["paiements"]:
        client.delete(f"/paiements/{p}")
    for i in ctx["incidents"]:
        client.delete(f"/incidents/{i}")
    for se in ctx["sessions"]:
        client.delete(f"/sessions/{se}")
    client.delete(f"/bornes/{b['id_borne']}")
    client.delete(f"/stations/{st['id_station']}")
    client.delete(f"/vehicules/{v['id_vehicule']}")
    client.delete(f"/clients/{c['id_client']}")
    for chemin in ctx["autres"]:
        client.delete(chemin)


def test_health(client):
    assert client.get("/health").json() == {"status": "ok", "database": "ok"}


def test_404_et_validation(client):
    assert client.get("/clients/999999999").status_code == 404
    r = client.post("/clients", json={"prenom": "A", "nom": "B", "email": "pas-un-email"})
    assert r.status_code == 422
    r = client.get("/bornes", params={"etat": "casse"})  # hors du CHECK
    assert r.status_code == 422


def test_unicite_et_cle_etrangere(client, donnees):
    c = donnees["client"]
    # email déjà pris -> 409 (UNIQUE)
    r = client.post("/clients", json={"prenom": "X", "nom": "Y", "email": c["email"]})
    assert r.status_code == 409
    # véhicule d'un client inexistant -> 409 (FOREIGN KEY)
    r = client.post("/vehicules", json={"id_client": 999999999, "immatriculation": f"Z-{uid()}",
                                        "marque": "A", "modele": "B"})
    assert r.status_code == 409
    # supprimer un client qui a un véhicule -> 409
    assert client.delete(f"/clients/{c['id_client']}").status_code == 409


def test_cycle_session_et_paiement(client, donnees):
    b, v = donnees["borne"], donnees["vehicule"]

    r = client.post("/sessions", json={"id_borne": b["id_borne"], "id_vehicule": v["id_vehicule"]})
    assert r.status_code == 201
    sess = r.json()
    donnees["sessions"].append(sess["id_session"])
    assert sess["statut"] == "en_cours"

    # une 2e session sur la même borne est refusée
    r = client.post("/sessions", json={"id_borne": b["id_borne"], "id_vehicule": v["id_vehicule"]})
    assert r.status_code == 409

    r = client.post(f"/sessions/{sess['id_session']}/terminer",
                    json={"energie_kwh": 18.5, "cout_eur": 7.4})
    assert r.status_code == 200 and r.json()["statut"] == "terminee"
    # on ne termine pas deux fois
    assert client.post(f"/sessions/{sess['id_session']}/terminer",
                       json={"energie_kwh": 1}).status_code == 409

    # impayée tant qu'aucun paiement
    impayees = client.get("/stats/sessions/impayees", params={"limit": 500}).json()
    assert sess["id_session"] in [i["id_session"] for i in impayees]

    p = client.post("/paiements", json={"id_session": sess["id_session"], "montant_eur": 7.4,
                                        "mode_paiement": "carte", "statut": "valide"})
    assert p.status_code == 201
    donnees["paiements"].append(p.json()["id_paiement"])
    impayees = client.get("/stats/sessions/impayees", params={"limit": 500}).json()
    assert sess["id_session"] not in [i["id_session"] for i in impayees]

    d = client.get(f"/sessions/{sess['id_session']}/details").json()
    assert d["code_borne"] == b["code_borne"] and d["nom_client"] == "Pytest"
    assert client.get(f"/clients/{donnees['client']['id_client']}/sessions").json()


def test_incident_haute_met_borne_hors_service(client, donnees):
    b = donnees["borne"]
    r = client.post("/incidents", json={"id_borne": b["id_borne"], "categorie": "connecteur",
                                        "gravite": "haute", "description": "câble arraché"})
    assert r.status_code == 201
    inc = r.json()
    donnees["incidents"].append(inc["id_incident"])

    assert client.get(f"/bornes/{b['id_borne']}").json()["etat"] == "hors_service"
    # borne hors service -> impossible de démarrer une session
    r = client.post("/sessions", json={"id_borne": b["id_borne"],
                                       "id_vehicule": donnees["vehicule"]["id_vehicule"]})
    assert r.status_code == 409

    r = client.post(f"/incidents/{inc['id_incident']}/resoudre")
    assert r.status_code == 200 and r.json()["statut"] == "resolu"
    assert client.get(f"/bornes/{b['id_borne']}").json()["etat"] == "disponible"
    assert client.post(f"/incidents/{inc['id_incident']}/resoudre").status_code == 409


def test_ids_incident_uniques(client, donnees):
    b = donnees["borne"]
    ids = []
    for _ in range(3):
        r = client.post("/incidents", json={"id_borne": b["id_borne"], "categorie": "ecran",
                                            "gravite": "faible"})
        assert r.status_code == 201
        ids.append(r.json()["id_incident"])
    donnees["incidents"].extend(ids)
    assert len(set(ids)) == 3


def test_intervention(client, donnees):
    b = donnees["borne"]
    inc = client.post("/incidents", json={"id_borne": b["id_borne"], "categorie": "reseau",
                                          "gravite": "moyenne"}).json()
    donnees["incidents"].append(inc["id_incident"])
    t = client.post("/techniciens", json={"prenom": "Tech", "nom": "Nicien",
                                          "email": f"{uid()}@tech.fr"}).json()
    donnees["autres"].insert(0, f"/techniciens/{t['id_technicien']}")
    i = client.post("/interventions", json={"id_incident": inc["id_incident"],
                                            "id_technicien": t["id_technicien"]}).json()
    donnees["autres"].insert(0, f"/interventions/{i['id_intervention']}")
    # les interventions doivent être supprimées AVANT l'incident : on les nettoie ici
    r = client.post(f"/interventions/{i['id_intervention']}/cloturer",
                    json={"compte_rendu": "Câble remplacé"})
    assert r.status_code == 200 and r.json()["date_fin"] is not None
    assert client.get(f"/incidents/{inc['id_incident']}/interventions").json()
    client.delete(f"/interventions/{i['id_intervention']}")


@pytest.mark.parametrize("chemin", [
    "/stats/resume", "/stats/stations/revenus", "/stats/clients/top", "/stats/bornes/classement",
    "/stats/bornes/problematiques", "/stats/incidents/par-categorie", "/stats/sessions/mensuel",
    "/stats/sessions/impayees", "/stats/techniciens/charge",
])
def test_stats_repondent(client, chemin):
    r = client.get(chemin)
    assert r.status_code == 200, r.text
    assert isinstance(r.json(), (list, dict))
