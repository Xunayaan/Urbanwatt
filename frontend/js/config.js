// Configuration de l'interface : le SEUL fichier à modifier selon l'environnement.
window.APP_CONFIG = {
  // Où joindre l'API.
  //  - "/api"                  : via le proxy nginx du conteneur web (cas Docker, même origine, pas de CORS)
  //  - "http://localhost:8000" : appel direct (développement : front servi par `python -m http.server`)
  API_BASE: "/api",
//   API_BASE: "http://localhost:8000",

  // Lien vers le Swagger de l'API (port publié par le conteneur api).
  DOCS_URL: "http://localhost:8000/docs",
};
