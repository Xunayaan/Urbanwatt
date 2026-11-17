SELECT * FROM borne;

SELECT * FROM client;

SELECT * FROM incident;

SELECT * FROM intervention;

SELECT * FROM paiement;

SELECT * FROM session_recharge;

SELECT * FROM station;

SELECT * FROM technicien;

SELECT * FROM vehicule;

-- Liaison entre table client et vehicule 
-- Liste tous les clients possédant un véhicule de marque "Peugeot"
SELECT c.prenom, c.nom, c.id_client, v.marque FROM client c
JOIN vehicule v ON v.id_client = c.id_client
WHERE v.marque = 'Peugeot';

-- Liasion entre session_recharge, paiement et vehicule
-- Liste toutes les sessions de recharge effectuées par un véhicule spécifique, avec le montant payé 
SELECT p.montant_eur, p.date_paiement, s.id_session, v.marque, v.modele FROM paiement p
JOIN session_recharge s ON p.id_session = s.id_session
JOIN vehicule v ON s.id_vehicule = v.id_vehicule
WHERE v.marque = 'BMW'

-- Liaison entre table vehicule, borne et station
-- Liste toutes les recharges effectuées par un véhicule sur une borne spécifique, avec le coût de la recharge et le modèle du véhicule
SELECT v.id_vehicule, v.modele, s.cout_eur, b.id_borne FROM session_recharge s
JOIN vehicule v ON v.id_vehicule = s.id_vehicule
JOIN borne b ON s.id_borne = b.id_borne 
WHERE b.id_borne = 3

-- Liaison entre table station, borne et incident 
-- Liste tous les incidents ouvert en listant les informations sur la station et la borne associée à chaque incident
SELECT i.date_signalement, i.statut, b.code_borne, s.nom_station, s.ville FROM incident i
JOIN borne b ON i.id_borne = b.id_borne
JOIN station s ON b.id_station = s.id_station 
WHERE i.statut = 'ouvert'

-- Liaison entre table technicien , incident et intervention
-- Liste tous les techniciens ayant résolu un incident, en affichant le compte rendu de l'intervention et la gravité de l'incident
SELECT t.prenom, t.nom, i.compte_rendu, n.gravite, n.statut FROM technicien t
JOIN intervention i ON t.id_technicien = i.id_technicien
JOIN incident n ON i.id_incident = n.id_incident
WHERE n.statut = 'resolu'
