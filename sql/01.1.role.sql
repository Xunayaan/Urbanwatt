CREATE ROLE api_user
    LOGIN
    PASSWORD 'UserUrb4nw4tt'
    NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION;


REVOKE CONNECT ON DATABASE projet_urbanwatt FROM PUBLIC;
GRANT CONNECT ON DATABASE projet_urbanwatt TO api_user;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO api_user;

GRANT SELECT ON station, borne, vehicule TO api_user;
GRANT SELECT (id_client, prenom, nom, ville, date_inscription) ON client TO api_user;
GRANT SELECT, INSERT ON session_recharge TO api_user;
GRANT UPDATE (fin_session, energie_kwh, cout_eur, statut) ON session_recharge TO api_user;
GRANT SELECT, INSERT ON paiement TO api_user;
GRANT SELECT, INSERT ON incident TO api_user;