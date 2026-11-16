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
SELECT c.prenom, c.nom, c.id_client, v.marque FROM client c
JOIN vehicule v ON v.id_client = c.id_client
WHERE v.marque = 'Peugeot';

-- Liaison entre table vehicule, borne et station
SELECT v.id_vehicule, v.modele, s.cout_eur, b.id_borne FROM session_recharge s
JOIN vehicule v ON v.id_vehicule = s.id_vehicule
JOIN borne b ON s.id_borne = b.id_borne 
WHERE b.id_borne = 3