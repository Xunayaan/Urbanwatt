-- Question 1  Afficher les clients ayant réalisé au moins une session de recharge dans la station ST-LIL
SELECT DISTINCT c.nom, c.prenom FROM client c
JOIN vehicule v ON c.id_client = v.id_client
JOIN session_recharge sr ON v.id_vehicule = sr.id_vehicule
JOIN borne b ON sr.id_borne = b.id_borne
JOIN station s ON b.id_station = s.id_station
WHERE s.code_station = 'ST-LIL';

-- Question 2  Lister toutes les bornes de la station ST-TOU
SELECT b.code_borne, b.puissance_kw, b.connecteur, b.etat FROM borne b
JOIN station s ON b.id_station = s.id_station
WHERE s.code_station = 'ST-TOU'
ORDER BY b.puissance_kw DESC;

-- Question 3 Afficher l’historique des sessions du véhicule ESSAI-0001 
SELECT sr.debut_session, sr.fin_session, b.code_borne, sr.energie_kwh,sr.cout_eur, sr.statut FROM session_recharge sr
JOIN vehicule v ON sr.id_vehicule = v.id_vehicule
JOIN borne b ON sr.id_borne = b.id_borne
WHERE v.immatriculation = 'ESSAI-0001'
ORDER BY sr.debut_session DESC;

-- Question 4  Lister les clients n’ayant jamais eu de session annulée ou interrompue, y compris ceux qui n’ont effectué aucune recharge
SELECT c.nom, c.prenom FROM client c
WHERE NOT EXISTS (
    SELECT 1 --Vérifie qu'au moins une ligne est retournée par la requête
    FROM vehicule v
    JOIN session_recharge sr ON v.id_vehicule = sr.id_vehicule
    WHERE v.id_client = c.id_client
    AND sr.statut IN ('annulee', 'interrompue')
);

-- Question 5  Afficher les sessions terminées dans la station ST-LYO
SELECT sr.id_session,sr.debut_session,sr.fin_session,b.code_borne,sr.energie_kwh,sr.cout_eur,sr.statut FROM session_recharge sr
JOIN borne b ON sr.id_borne = b.id_borne
JOIN station s ON b.id_station = s.id_station
WHERE s.code_station = 'ST-LYO'
AND sr.statut = 'terminee'
ORDER BY sr.energie_kwh DESC;

-- Question 6 Présenter pour le client n°10 toutes ses sessions avec le vehicule concerné
SELECT c.id_client,v.immatriculation,s.nom_station,sr.debut_session,sr.statut FROM client c
JOIN vehicule v ON c.id_client = v.id_client
JOIN session_recharge sr ON v.id_vehicule = sr.id_vehicule
JOIN borne b ON sr.id_borne = b.id_borne
JOIN station s ON b.id_station = s.id_station
WHERE c.id_client = 10
ORDER BY sr.debut_session DESC;

-- Question 7 Lister les incidents de gravité haute avec le code de la borne, la station, la catégorie...
SELECT i.id_incident,b.code_borne,s.nom_station,i.categorie,i.date_signalement,i.statut FROM incident i
JOIN borne b ON i.id_borne = b.id_borne
JOIN station s ON b.id_station = s.id_station
WHERE i.gravite = 'haute';

-- Question 8 Afficher les incidents de la station ST-BOR  classés par date décroissante, en indiquant les interventions éventuelles
SELECT b.code_borne,i.categorie,i.date_signalement,i.statut AS statut_incident,inter.id_intervention,inter.date_debut,inter.date_fin,inter.statut AS statut_intervention,t.nom AS nom_technicien,t.prenom AS prenom_technicien FROM incident i
JOIN borne b ON i.id_borne = b.id_borne
JOIN station s ON b.id_station = s.id_station
LEFT JOIN intervention inter ON i.id_incident = inter.id_incident --Left join permet de conserver des elements non relié à l'autre table, ici tous les incidents qui n'ont pas d'intervention.
LEFT JOIN technicien t ON inter.id_technicien = t.id_technicien
WHERE s.code_station = 'ST-BOR'
ORDER BY i.date_signalement DESC;

--Question 9 Lister les sessions annulées ou interrompues dans ST-NAN, avec le véhicule, la date et le statut.
SELECT sr.id_session,v.immatriculation,sr.debut_session,sr.statut FROM session_recharge sr
JOIN vehicule v ON sr.id_vehicule = v.id_vehicule
JOIN borne b ON sr.id_borne = b.id_borne
JOIN station s ON b.id_station = s.id_station
WHERE s.code_station = 'ST-NAN'
AND sr.statut IN ('annulee', 'interrompue')
ORDER BY sr.debut_session DESC;

-- Question 10 Afficher les clients ayant réalisé au moins une session terminée de plus de 30 kWh, sans doublon
SELECT DISTINCT c.nom, c.prenom FROM client c
JOIN vehicule v ON c.id_client = v.id_client
JOIN session_recharge sr ON v.id_vehicule = sr.id_vehicule
WHERE sr.statut = 'terminee'
AND sr.energie_kwh > 30;

-- Question 11 Calculer le nombre de bornes disponibles, en maintenance et hors service pour chaque station.
SELECT s.nom_station,
    COUNT(CASE WHEN b.etat = 'disponible' THEN 1 END) AS nb_disponibles,
    COUNT(CASE WHEN b.etat = 'maintenance' THEN 1 END) AS nb_maintenance,
    COUNT(CASE WHEN b.etat = 'hors_service' THEN 1 END) AS nb_hors_service
FROM station s
LEFT JOIN borne b ON s.id_station = b.id_station -- 
GROUP BY s.id_station, s.nom_station
ORDER BY s.nom_station;

--Question 12  Trouver, pour la station ST-LIL, la ou les sessions terminées dont l’énergie délivrée est maximale.
SELECT sr.id_session,MAX(sr.energie_kwh),sr.debut_session,sr.fin_session FROM session_recharge sr
JOIN borne b ON sr.id_borne = b.id_borne
JOIN station s ON b.id_station = s.id_station
WHERE s.code_station = 'ST-LIL'
AND sr.statut = 'terminee'
GROUP BY sr.id_session,sr.debut_session,sr.fin_session;


-- Question 13 Afficher le nombre de véhicules distincts ayant réalisé au moins une session terminée dans chaque station.
 SELECT s.nom_station, COUNT(DISTINCT sr.id_vehicule) AS nb_vehicules FROM station s
JOIN borne b ON s.id_station = b.id_station
JOIN session_recharge sr ON b.id_borne = sr.id_borne
    AND sr.statut = 'terminee'
GROUP BY s.id_station, s.nom_station
ORDER BY s.nom_station;


-- Question 14  Calculer l’énergie moyenne délivrée par véhicule sur ses sessions terminées, en conservant ceux sans recharge.
SELECT v.immatriculation,AVG(sr.energie_kwh) AS energie_moyenne FROM vehicule v
LEFT JOIN session_recharge sr
    ON v.id_vehicule = sr.id_vehicule
    AND sr.statut = 'terminee'
GROUP BY v.id_vehicule, v.immatriculation
ORDER BY v.immatriculation;


-- Question 15  Afficher pour chaque station sa plus grande énergie délivrée en une session terminée et la borne associée
SELECT s.nom_station,b.code_borne,MAX(sr.energie_kwh) FROM station s
JOIN borne b ON s.id_station = b.id_station
JOIN session_recharge sr ON b.id_borne = sr.id_borne
WHERE sr.statut = 'terminee'
GROUP BY s.nom_station,b.code_borne;


-- Question 16 Présenter toutes les sessions de ESSAI-0007 avec la ville, la station, la borne et la date par ordre chronologique.
SELECT v.immatriculation,s.ville,s.nom_station,b.code_borne,sr.debut_session FROM vehicule v
JOIN session_recharge sr ON v.id_vehicule = sr.id_vehicule
JOIN borne b ON sr.id_borne = b.id_borne
JOIN station s ON b.id_station = s.id_station
WHERE v.immatriculation = 'ESSAI-0007'
ORDER BY sr.debut_session ASC;


-- Question 17 Afficher les propriétaires et les véhicules ayant utilisé au moins une fois la borne BR-NAN-01.
SELECT DISTINCT c.nom,c.prenom,v.immatriculation,v.marque,v.modele FROM client c
JOIN vehicule v ON c.id_client = v.id_client
JOIN session_recharge sr ON v.id_vehicule = sr.id_vehicule
JOIN borne b ON sr.id_borne = b.id_borne
WHERE b.code_borne = 'BR-NAN-01';


-- Question 18  Lister les bornes ayant connu au moins deux incidents, avec le nombre d’incidents et la date du plus récent.
SELECT b.code_borne,COUNT(i.id_incident) AS nb_incidents, MAX(i.date_signalement) AS dernier_incident
FROM borne b
JOIN incident i ON b.id_borne = i.id_borne
GROUP BY b.id_borne, b.code_borne  -- On utilise group by pour chaque fonction d'agrégation
HAVING COUNT(i.id_incident) >= 2
ORDER BY dernier_incident DESC;


-- Question 19 Trouver les clients ayant effectué au moins une session terminée dans chacune des stations du réseau.
SELECT c.id_client,c.nom,c.prenom FROM client c
JOIN vehicule v ON c.id_client = v.id_client
JOIN session_recharge sr ON v.id_vehicule = sr.id_vehicule
JOIN borne b ON sr.id_borne = b.id_borne
JOIN station s ON b.id_station = s.id_station
WHERE sr.statut = 'terminee'
GROUP BY c.id_client, c.nom, c.prenom
HAVING COUNT(DISTINCT s.id_station) = (
    SELECT COUNT(*)
    FROM station
);


-- Question 20 Établir le classement des clients selon l'énergie consommée :client, nombre de sessions, énergie et rang.
SELECT c.id_client,c.nom,c.prenom,COUNT(sr.id_session) AS nb_sessions,SUM(sr.energie_kwh) AS energie_totale, RANK() OVER (ORDER BY SUM(sr.energie_kwh) DESC) AS rang FROM client c
JOIN vehicule v ON c.id_client = v.id_client
JOIN session_recharge sr ON v.id_vehicule = sr.id_vehicule
WHERE sr.statut = 'terminee'
GROUP BY c.id_client, c.nom, c.prenom
ORDER BY energie_totale DESC;
