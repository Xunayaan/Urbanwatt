// Description DÉCLARATIVE des 9 ressources de l'API.
// L'écran de liste, les filtres, les formulaires et les boutons d'action sont tous générés
// à partir de ces objets : ajouter une ressource = ajouter un objet ici, sans écrire de HTML.
//
//  columns : [champ, libellé, type d'affichage]
//  filters : paramètres de requête acceptés par la route de liste de l'API
//  fields  : champs du formulaire. req = NOT NULL en base ; def = valeur par défaut ("now", "today" ou littéral)
//            type "fk" = liste déroulante alimentée par l'API (clé étrangère)
//  links   : boutons qui ouvrent une autre ressource filtrée (navigation entre tables liées)

const nom = (r) => `${r.prenom} ${r.nom}`;

export const ETATS_BORNE = ["disponible", "hors_service", "maintenance"];
export const STATUTS_SESSION = ["en_cours", "terminee", "interrompue", "annulee"];
export const STATUTS_INCIDENT = ["ouvert", "resolu"];
export const GRAVITES = ["faible", "moyenne", "haute"];

export const ENTITIES = {
  clients: {
    path: "/clients",
    idField: "id_client",
    title: "Clients",
    singular: "le client",
    label: nom,
    columns: [
      ["id_client", "#"],
      ["prenom", "Prénom"],
      ["nom", "Nom"],
      ["email", "Email"],
      ["ville", "Ville"],
      ["date_inscription", "Inscrit le", "date"],
    ],
    filters: [
      { name: "ville", label: "Ville" },
      { name: "recherche", label: "Recherche (nom, prénom, email)" },
    ],
    fields: [
      { name: "prenom", label: "Prénom", type: "text", req: true, max: 100 },
      { name: "nom", label: "Nom", type: "text", req: true, max: 100 },
      { name: "email", label: "Email", type: "email", req: true, max: 255 },
      { name: "ville", label: "Ville", type: "text", max: 100 },
      { name: "date_inscription", label: "Date d'inscription", type: "date", req: true, def: "today", createOnly: true },
    ],
    links: [{ label: "Véhicules", to: (r) => `#/vehicules?id_client=${r.id_client}` }],
  },

  vehicules: {
    path: "/vehicules",
    idField: "id_vehicule",
    title: "Véhicules",
    singular: "le véhicule",
    label: (r) => `${r.immatriculation} (${r.marque} ${r.modele})`,
    columns: [
      ["id_vehicule", "#"],
      ["id_client", "Client n°"],
      ["immatriculation", "Immatriculation"],
      ["marque", "Marque"],
      ["modele", "Modèle"],
      ["capacite_batterie_kwh", "Batterie", "kwh"],
    ],
    filters: [
      { name: "id_client", label: "Client n°", type: "number" },
      { name: "marque", label: "Marque" },
    ],
    fields: [
      { name: "id_client", label: "Client", type: "fk", fk: "clients", req: true },
      { name: "immatriculation", label: "Immatriculation", type: "text", req: true, max: 20 },
      { name: "marque", label: "Marque", type: "text", req: true, max: 50 },
      { name: "modele", label: "Modèle", type: "text", req: true, max: 50 },
      { name: "capacite_batterie_kwh", label: "Capacité batterie (kWh)", type: "number", min: 0.01 },
    ],
    links: [{ label: "Sessions", to: (r) => `#/sessions?id_vehicule=${r.id_vehicule}` }],
  },

  stations: {
    path: "/stations",
    idField: "id_station",
    title: "Stations",
    singular: "la station",
    label: (r) => `${r.nom_station} — ${r.ville}`,
    columns: [
      ["id_station", "#"],
      ["code_station", "Code"],
      ["nom_station", "Nom"],
      ["ville", "Ville"],
      ["adresse", "Adresse"],
      ["date_ouverture", "Ouverture", "date"],
    ],
    filters: [{ name: "ville", label: "Ville" }],
    fields: [
      { name: "code_station", label: "Code station", type: "text", req: true, max: 20 },
      { name: "nom_station", label: "Nom", type: "text", req: true, max: 150 },
      { name: "ville", label: "Ville", type: "text", req: true, max: 100 },
      { name: "adresse", label: "Adresse", type: "text", req: true, max: 255 },
      { name: "date_ouverture", label: "Date d'ouverture", type: "date" },
    ],
    links: [{ label: "Bornes", to: (r) => `#/bornes?id_station=${r.id_station}` }],
  },

  bornes: {
    path: "/bornes",
    idField: "id_borne",
    title: "Bornes",
    singular: "la borne",
    label: (r) => `${r.code_borne} · ${r.puissance_kw} kW`,
    columns: [
      ["id_borne", "#"],
      ["id_station", "Station n°"],
      ["code_borne", "Code"],
      ["puissance_kw", "Puissance", "kw"],
      ["connecteur", "Connecteur"],
      ["etat", "État", "badge"],
    ],
    filters: [
      { name: "id_station", label: "Station n°", type: "number" },
      { name: "etat", label: "État", options: ETATS_BORNE },
      { name: "connecteur", label: "Connecteur" },
      { name: "puissance_min", label: "Puissance min (kW)", type: "number" },
    ],
    fields: [
      { name: "id_station", label: "Station", type: "fk", fk: "stations", req: true },
      { name: "code_borne", label: "Code borne", type: "text", req: true, max: 20 },
      { name: "puissance_kw", label: "Puissance (kW)", type: "number", req: true, min: 0.1, step: 0.1 },
      { name: "connecteur", label: "Connecteur", type: "text", req: true, max: 30, suggest: ["Type2", "CCS", "CHAdeMO"] },
      { name: "etat", label: "État", type: "select", options: ETATS_BORNE, req: true, def: "disponible" },
    ],
    links: [
      { label: "Sessions", to: (r) => `#/sessions?id_borne=${r.id_borne}` },
      { label: "Incidents", to: (r) => `#/incidents?id_borne=${r.id_borne}` },
    ],
  },

  sessions: {
    path: "/sessions",
    idField: "id_session",
    title: "Sessions de recharge",
    singular: "la session",
    label: (r) => `Session ${r.id_session}`,
    columns: [
      ["id_session", "#"],
      ["id_borne", "Borne n°"],
      ["id_vehicule", "Véhicule n°"],
      ["debut_session", "Début", "datetime"],
      ["fin_session", "Fin", "datetime"],
      ["energie_kwh", "Énergie", "kwh"],
      ["cout_eur", "Coût", "eur"],
      ["statut", "Statut", "badge"],
    ],
    filters: [
      { name: "statut", label: "Statut", options: STATUTS_SESSION },
      { name: "id_borne", label: "Borne n°", type: "number" },
      { name: "id_vehicule", label: "Véhicule n°", type: "number" },
    ],
    fields: [
      { name: "id_borne", label: "Borne", type: "fk", fk: "bornes", req: true },
      { name: "id_vehicule", label: "Véhicule", type: "fk", fk: "vehicules", req: true },
      { name: "debut_session", label: "Début", type: "datetime", req: true, def: "now" },
      { name: "statut", label: "Statut", type: "select", options: STATUTS_SESSION, req: true, def: "en_cours" },
      { name: "fin_session", label: "Fin", type: "datetime" },
      { name: "energie_kwh", label: "Énergie (kWh)", type: "number", min: 0 },
      { name: "cout_eur", label: "Coût (€)", type: "number", min: 0 },
    ],
    links: [{ label: "Paiements", to: (r) => `#/paiements?id_session=${r.id_session}` }],
    // Actions métier (appellent des routes dédiées de l'API, pas un simple PATCH)
    actions: [
      {
        label: "Détails",
        run: "detailsSession",
      },
      {
        label: "Terminer",
        show: (r) => r.statut === "en_cours",
        run: "terminerSession",
      },
      {
        label: "Annuler",
        show: (r) => r.statut === "en_cours",
        run: "annulerSession",
      },
    ],
  },

  paiements: {
    path: "/paiements",
    idField: "id_paiement",
    title: "Paiements",
    singular: "le paiement",
    label: (r) => `Paiement ${r.id_paiement}`,
    columns: [
      ["id_paiement", "#"],
      ["id_session", "Session n°"],
      ["date_paiement", "Date", "datetime"],
      ["montant_eur", "Montant", "eur"],
      ["mode_paiement", "Mode"],
      ["statut", "Statut", "badge"],
    ],
    filters: [
      { name: "id_session", label: "Session n°", type: "number" },
      { name: "statut", label: "Statut" },
      { name: "mode_paiement", label: "Mode de paiement" },
    ],
    fields: [
      { name: "id_session", label: "Session", type: "fk", fk: "sessions", req: true },
      { name: "date_paiement", label: "Date", type: "datetime", req: true, def: "now" },
      { name: "montant_eur", label: "Montant (€)", type: "number", req: true, min: 0, step: 0.01 },
      { name: "mode_paiement", label: "Mode de paiement", type: "text", req: true, max: 30, suggest: ["carte", "especes", "virement"] },
      { name: "statut", label: "Statut", type: "text", req: true, max: 30, suggest: ["valide", "en_attente", "refuse"] },
    ],
    links: [],
  },

  incidents: {
    path: "/incidents",
    idField: "id_incident",
    title: "Incidents",
    singular: "l'incident",
    label: (r) => `${r.categorie} (${r.gravite})`,
    columns: [
      ["id_incident", "#"],
      ["id_borne", "Borne n°"],
      ["date_signalement", "Signalé le", "datetime"],
      ["date_resolution", "Résolu le", "datetime"],
      ["categorie", "Catégorie"],
      ["gravite", "Gravité", "badge"],
      ["statut", "Statut", "badge"],
    ],
    filters: [
      { name: "statut", label: "Statut", options: STATUTS_INCIDENT },
      { name: "gravite", label: "Gravité", options: GRAVITES },
      { name: "categorie", label: "Catégorie" },
      { name: "id_borne", label: "Borne n°", type: "number" },
    ],
    fields: [
      { name: "id_incident", label: "N° d'incident (vide = automatique)", type: "number", min: 1, step: 1, createOnly: true },
      { name: "id_borne", label: "Borne", type: "fk", fk: "bornes", req: true },
      { name: "categorie", label: "Catégorie", type: "text", req: true, max: 50, suggest: ["connecteur", "ecran", "reseau", "paiement"] },
      { name: "gravite", label: "Gravité", type: "select", options: GRAVITES, req: true, def: "moyenne" },
      { name: "date_signalement", label: "Signalé le", type: "datetime", req: true, def: "now" },
      { name: "statut", label: "Statut", type: "select", options: STATUTS_INCIDENT, req: true, def: "ouvert" },
      { name: "date_resolution", label: "Résolu le", type: "datetime", editOnly: true },
      { name: "description", label: "Description", type: "textarea" },
    ],
    links: [{ label: "Interventions", to: (r) => `#/interventions?id_incident=${r.id_incident}` }],
    actions: [
      {
        label: "Résoudre",
        show: (r) => r.statut === "ouvert",
        run: "resoudreIncident",
      },
    ],
    note: "Un incident de gravité « haute » met automatiquement la borne hors service ; sa résolution la remet disponible.",
  },

  techniciens: {
    path: "/techniciens",
    idField: "id_technicien",
    title: "Techniciens",
    singular: "le technicien",
    label: nom,
    columns: [
      ["id_technicien", "#"],
      ["prenom", "Prénom"],
      ["nom", "Nom"],
      ["email", "Email"],
    ],
    filters: [],
    fields: [
      { name: "prenom", label: "Prénom", type: "text", req: true, max: 100 },
      { name: "nom", label: "Nom", type: "text", req: true, max: 100 },
      { name: "email", label: "Email", type: "email", req: true, max: 255 },
    ],
    links: [{ label: "Interventions", to: (r) => `#/interventions?id_technicien=${r.id_technicien}` }],
  },

  interventions: {
    path: "/interventions",
    idField: "id_intervention",
    title: "Interventions",
    singular: "l'intervention",
    label: (r) => `Intervention ${r.id_intervention}`,
    columns: [
      ["id_intervention", "#"],
      ["id_incident", "Incident n°"],
      ["id_technicien", "Technicien n°"],
      ["date_debut", "Début", "datetime"],
      ["date_fin", "Fin", "datetime"],
      ["statut", "Statut", "badge"],
      ["compte_rendu", "Compte rendu"],
    ],
    filters: [
      { name: "id_incident", label: "Incident n°", type: "number" },
      { name: "id_technicien", label: "Technicien n°", type: "number" },
      { name: "en_cours", label: "En cours ?", options: [["true", "Oui (sans date de fin)"], ["false", "Non (terminées)"]] },
    ],
    fields: [
      { name: "id_incident", label: "Incident", type: "fk", fk: "incidents", req: true },
      { name: "id_technicien", label: "Technicien", type: "fk", fk: "techniciens", req: true },
      { name: "date_debut", label: "Début", type: "datetime", req: true, def: "now" },
      { name: "date_fin", label: "Fin", type: "datetime" },
      { name: "statut", label: "Statut", type: "text", req: true, max: 30, def: "planifiee", suggest: ["planifiee", "en_cours", "terminee"] },
      { name: "compte_rendu", label: "Compte rendu", type: "textarea" },
    ],
    links: [],
    actions: [
      {
        label: "Clôturer",
        show: (r) => !r.date_fin,
        run: "cloturerIntervention",
      },
    ],
  },
};

// Menu latéral
export const NAV = [
  { group: "Vue d'ensemble", items: [{ key: "dashboard", title: "Tableau de bord" }] },
  { group: "Réseau", items: ["stations", "bornes"] },
  { group: "Clientèle", items: ["clients", "vehicules"] },
  { group: "Recharge", items: ["sessions", "paiements"] },
  { group: "Maintenance", items: ["incidents", "interventions", "techniciens"] },
  { group: "Outils", items: [{ key: "console", title: "Console API" }] },
];
