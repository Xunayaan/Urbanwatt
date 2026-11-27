// Point d'entrée : menu, routage par hash (#/clients?id_client=3) et indicateur d'état de l'API.
import { api } from "./api.js";
import { renderConsole } from "./console.js";
import { renderEntity } from "./crud.js";
import { renderDashboard } from "./dashboard.js";
import { ENTITIES, NAV } from "./entities.js";
import { h } from "./ui.js";

const view = document.getElementById("view");

// ------------------------------------------------------------------ menu
const nav = document.getElementById("nav");
for (const g of NAV) {
  nav.append(
    h("div", { class: "nav-group" }, g.group),
    ...g.items.map((it) => {
      const key = typeof it === "string" ? it : it.key;
      const title = typeof it === "string" ? ENTITIES[it].title : it.title;
      return h("a", {
        class: "nav-link", href: `#/${key}`, "data-key": key,
        // cliquer sur la page déjà ouverte ne change pas le hash : on force le rechargement (filtres remis à zéro)
        onclick: () => { if (location.hash === `#/${key}`) route(); },
      }, title);
    }),
  );
}

// ---------------------------------------------------------------- routage
function parseHash() {
  const raw = location.hash.replace(/^#\/?/, "") || "dashboard";
  const [key, query = ""] = raw.split("?");
  return { key, filters: Object.fromEntries(new URLSearchParams(query)) };
}

function route() {
  const { key, filters } = parseHash();
  document.querySelectorAll(".nav-link").forEach((a) => a.classList.toggle("active", a.dataset.key === key));
  if (key === "dashboard") renderDashboard(view);
  else if (key === "console") renderConsole(view);
  else if (ENTITIES[key]) renderEntity(view, key, filters);
  else view.replaceChildren(h("div", { class: "empty error" }, `Page « ${key} » introuvable.`));
  document.title = `${ENTITIES[key]?.title ?? (key === "console" ? "Console API" : "Tableau de bord")} — Bornes de recharge`;
  window.scrollTo(0, 0);
}
window.addEventListener("hashchange", route);

// ----------------------------------------------- indicateur d'état de l'API
const pill = document.getElementById("apiStatus");
function setPill(kind, text) {
  pill.className = `pill pill-${kind}`;
  pill.textContent = text;
}
async function checkHealth() {
  try {
    await api.get("/health");
    setPill("ok", "API · base connectée");
  } catch (e) {
    if (e.status === 0) setPill("down", "API injoignable");
    else if (e.status === 503) setPill("warn", "API ok · base injoignable");
    else setPill("warn", `API · erreur ${e.status}`);
  }
}
checkHealth();
setInterval(checkHealth, 15000);

const docs = document.getElementById("docsLink");
docs.href = window.APP_CONFIG?.DOCS_URL || "#";

route();
