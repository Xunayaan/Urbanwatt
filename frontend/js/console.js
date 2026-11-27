// Console API : envoyer n'importe quelle requête à l'API et voir la réponse brute (utile pour la démonstration).
import { API_BASE, rawFetch } from "./api.js";
import { h } from "./ui.js";

const PRESETS = [
  ["GET", "/health", ""],
  ["GET", "/stats/resume", ""],
  ["GET", "/clients?limit=5", ""],
  ["GET", "/sessions?statut=en_cours", ""],
  ["GET", "/stats/bornes/classement", ""],
  ["POST", "/clients", JSON.stringify({ prenom: "Ada", nom: "Lovelace", email: "ada@example.org", ville: "Paris" }, null, 2)],
  ["POST", "/clients", JSON.stringify({ prenom: "Doublon", nom: "Test", email: "ada@example.org" }, null, 2)],
  ["GET", "/clients/999999", ""],
];

export function renderConsole(root) {
  const method = h("select", { id: "c_method" }, ["GET", "POST", "PATCH", "DELETE"].map((m) => h("option", { value: m }, m)));
  const path = h("input", { id: "c_path", type: "text", value: "/health", spellcheck: "false", "aria-label": "Chemin" });
  const body = h("textarea", { id: "c_body", rows: 7, spellcheck: "false", placeholder: "Corps JSON (POST / PATCH)" });
  const status = h("span", { class: "chip" }, "—");
  const timing = h("span", { class: "muted" });
  const out = h("pre", { class: "code-out" }, "La réponse s'affichera ici.");

  const preset = h("select", {
    "aria-label": "Exemples",
    onchange: (ev) => {
      const p = PRESETS[ev.target.value];
      if (!p) return;
      [method.value, path.value, body.value] = p;
    },
  }, h("option", { value: "" }, "Exemples de requêtes…"),
    PRESETS.map((p, i) => h("option", { value: i }, `${p[0]} ${p[1]}${p[0] === "POST" && p[2].includes("Doublon") ? "  (provoque un 409)" : ""}`)));

  async function send() {
    status.className = "chip";
    status.textContent = "…";
    const res = await rawFetch(method.value, path.value.trim(), body.value.trim());
    let pretty = res.text;
    try { pretty = JSON.stringify(JSON.parse(res.text), null, 2); } catch { /* texte brut */ }
    status.textContent = res.status === 0 ? "ERREUR" : String(res.status);
    status.className = `chip ${res.status >= 200 && res.status < 300 ? "chip-terminee" : res.status >= 400 || res.status === 0 ? "chip-haute" : "chip-en_cours"}`;
    timing.textContent = `${res.ms} ms`;
    out.textContent = pretty || "(réponse vide)";
  }

  root.replaceChildren(
    h("div", { class: "page-head" }, h("div", {}, h("h1", {}, "Console API"),
      h("p", { class: "muted" }, "Base de l'API utilisée par cette interface : ", h("code", {}, API_BASE)))),
    h("div", { class: "panel" }, h("div", { class: "panel-body" },
      h("div", { class: "console-bar" }, preset, method, path, h("button", { class: "btn btn-primary", type: "button", onclick: send }, "Envoyer")),
      body,
      h("div", { class: "console-status" }, "Réponse : ", status, timing),
      out)),
  );
}
