// Tableau de bord : une carte par route /stats de l'API (chaque panneau se charge indépendamment).
import { api } from "./api.js";
import { errMsg, fmtValue, h } from "./ui.js";

function dataTable(columns, rows) {
  if (!rows.length) return h("div", { class: "empty" }, "Aucune donnée.");
  return h("div", { class: "table-wrap" },
    h("table", { class: "grid compact" },
      h("thead", {}, h("tr", {}, columns.map(([, l]) => h("th", {}, l)))),
      h("tbody", {}, rows.map((r) => h("tr", {}, columns.map(([f, , t]) => h("td", {}, fmtValue(r[f], t))))))));
}

// Barres horizontales en CSS pur (aucune bibliothèque de graphiques)
function bars(rows, labelKey, valueKey, type) {
  if (!rows.length) return h("div", { class: "empty" }, "Aucune donnée.");
  const max = Math.max(...rows.map((r) => Number(r[valueKey])), 1);
  return h("div", { class: "bars" }, rows.map((r) =>
    h("div", { class: "bar-row" },
      h("span", { class: "bar-label", title: r[labelKey] }, r[labelKey]),
      h("span", { class: "bar-track" }, h("span", { class: "bar-fill", style: `width:${(Number(r[valueKey]) / max) * 100}%` })),
      h("span", { class: "bar-value" }, fmtValue(r[valueKey], type)))));
}

function panel(title, hint, loader, wide = false) {
  const body = h("div", { class: "panel-body" }, h("div", { class: "empty" }, "Chargement…"));
  loader().then((n) => body.replaceChildren(n)).catch((e) => body.replaceChildren(h("div", { class: "empty error" }, errMsg(e))));
  return h("section", { class: "panel" + (wide ? " panel-wide" : "") },
    h("header", {}, h("h3", {}, title), hint ? h("span", { class: "hint" }, hint) : null), body);
}

function card(label, value, sub) {
  return h("div", { class: "kpi" }, h("span", { class: "kpi-label" }, label), h("strong", {}, value), sub ? h("small", {}, sub) : null);
}

export function renderDashboard(root) {
  const kpis = h("div", { class: "kpis" }, h("div", { class: "empty" }, "Chargement…"));
  api.get("/stats/resume").then((s) =>
    kpis.replaceChildren(
      card("Clients", fmtValue(s.nb_clients, "number")),
      card("Véhicules", fmtValue(s.nb_vehicules, "number")),
      card("Stations", fmtValue(s.nb_stations, "number")),
      card("Bornes", fmtValue(s.nb_bornes, "number"), `${s.nb_bornes_disponibles} disponible(s)`),
      card("Sessions en cours", fmtValue(s.nb_sessions_en_cours, "number")),
      card("Incidents ouverts", fmtValue(s.nb_incidents_ouverts, "number")),
      card("Chiffre d'affaires", fmtValue(s.chiffre_affaires_eur, "eur"), "sessions terminées"),
    ),
  ).catch((e) => kpis.replaceChildren(h("div", { class: "empty error" }, errMsg(e))));

  const refresh = h("button", { class: "btn", type: "button", onclick: () => renderDashboard(root) }, "↻ Actualiser");

  root.replaceChildren(
    h("div", { class: "page-head" }, h("div", {}, h("h1", {}, "Tableau de bord"),
      h("p", { class: "muted" }, "Chaque panneau affiche le résultat d'une requête SQL analytique exécutée par l'API (/stats).")), refresh),
    kpis,
    h("div", { class: "panels" },
      panel("Chiffre d'affaires par station", "LEFT JOIN · GROUP BY", async () =>
        bars(await api.get("/stats/stations/revenus"), "nom_station", "chiffre_affaires_eur", "eur")),
      panel("Évolution mensuelle", "CTE · date_trunc · SUM() OVER", async () => {
        const rows = await api.get("/stats/sessions/mensuel");
        return h("div", {}, bars(rows, "mois", "chiffre_affaires_eur", "eur"), dataTable([
          ["mois", "Mois"], ["nb_sessions", "Sessions", "number"], ["energie_kwh", "Énergie", "kwh"], ["ca_cumule_eur", "CA cumulé", "eur"],
        ], rows));
      }),
      panel("Stations — détail", "COUNT(DISTINCT) · LEFT JOIN", async () =>
        dataTable([["nom_station", "Station"], ["ville", "Ville"], ["nb_bornes", "Bornes", "number"], ["nb_sessions", "Sessions", "number"],
          ["energie_kwh", "Énergie", "kwh"], ["chiffre_affaires_eur", "CA", "eur"]], await api.get("/stats/stations/revenus")), true),
      panel("Meilleurs clients", "jointures client → véhicule → session", async () =>
        dataTable([["prenom", "Prénom"], ["nom", "Nom"], ["nb_sessions", "Sessions", "number"], ["energie_kwh", "Énergie", "kwh"], ["depense_eur", "Dépense", "eur"]],
          await api.get("/stats/clients/top", { limit: 8 }))),
      panel("Classement des bornes par station", "RANK() OVER (PARTITION BY …)", async () =>
        dataTable([["nom_station", "Station"], ["code_borne", "Borne"], ["puissance_kw", "Puissance", "kw"], ["nb_sessions", "Sessions", "number"],
          ["energie_kwh", "Énergie", "kwh"], ["rang_dans_station", "Rang", "number"]], await api.get("/stats/bornes/classement")), true),
      panel("Incidents par catégorie et gravité", "FILTER · EXTRACT(EPOCH …) · CASE", async () =>
        dataTable([["categorie", "Catégorie"], ["gravite", "Gravité", "badge"], ["nb_incidents", "Incidents", "number"], ["nb_ouverts", "Ouverts", "number"],
          ["duree_moy_resolution_h", "Résolution moy.", "hours"]], await api.get("/stats/incidents/par-categorie"))),
      panel("Bornes à problèmes (≥ 2 incidents)", "GROUP BY … HAVING", async () =>
        dataTable([["code_borne", "Borne"], ["nom_station", "Station"], ["nb_incidents", "Incidents", "number"], ["dernier_incident", "Dernier", "datetime"]],
          await api.get("/stats/bornes/problematiques", { min_incidents: 2 }))),
      panel("Sessions terminées sans paiement", "NOT EXISTS (sous-requête corrélée)", async () =>
        dataTable([["id_session", "Session n°"], ["prenom", "Prénom"], ["nom", "Nom"], ["fin_session", "Fin", "datetime"], ["cout_eur", "À payer", "eur"]],
          await api.get("/stats/sessions/impayees", { limit: 10 }))),
      panel("Charge des techniciens", "LEFT JOIN · FILTER · AVG", async () =>
        dataTable([["prenom", "Prénom"], ["nom", "Nom"], ["nb_interventions", "Interventions", "number"], ["nb_en_cours", "En cours", "number"], ["duree_moy_h", "Durée moy.", "hours"]],
          await api.get("/stats/techniciens/charge"))),
    ),
  );
}
