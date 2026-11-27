// Petits utilitaires d'interface : construction du DOM, notifications, fenêtres modales, formats.

// h("div", {class: "x", onclick: fn}, enfant1, enfant2) -> élément DOM.
// On construit le DOM avec textContent (jamais innerHTML) : les données viennent de la base,
// cela empêche toute injection HTML/JS (XSS).
export function h(tag, attrs = {}, ...children) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === undefined || v === null || v === false || k === "value") continue;
    if (k === "class") el.className = v;
    else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else el.setAttribute(k, v === true ? "" : v);
  }
  for (const c of children.flat(Infinity)) {
    if (c === undefined || c === null || c === false) continue;
    el.append(c instanceof Node ? c : document.createTextNode(String(c)));
  }
  // value doit être posée APRÈS la création des <option> d'un <select>
  if (attrs && attrs.value !== undefined && attrs.value !== null) el.value = attrs.value;
  return el;
}

export const errMsg = (e) => (e && e.message) || String(e);

// ---------------------------------------------------------------- notifications
export function toast(message, kind = "info", ms = 5000) {
  const t = h("div", { class: `toast toast-${kind}`, role: "status" }, message);
  document.getElementById("toasts").append(t);
  setTimeout(() => t.remove(), ms);
}

// ---------------------------------------------------------------------- modales
export function openModal({ title, body, wide = false }) {
  const dlg = h(
    "dialog",
    { class: "modal" + (wide ? " wide" : "") },
    h(
      "header",
      {},
      h("h3", {}, title),
      h("button", { class: "icon-btn", type: "button", "aria-label": "Fermer", onclick: () => dlg.close() }, "✕"),
    ),
    h("div", { class: "modal-body" }, body),
  );
  dlg.addEventListener("close", () => dlg.remove());
  document.body.append(dlg);
  dlg.showModal();
  return dlg;
}

export function confirmBox(message, { danger = false, okLabel = "Confirmer" } = {}) {
  return new Promise((resolve) => {
    let answer = false;
    const dlg = openModal({
      title: "Confirmation",
      body: [
        h("p", {}, message),
        h(
          "div",
          { class: "actions" },
          h("button", { class: "btn", type: "button", onclick: () => dlg.close() }, "Annuler"),
          h(
            "button",
            {
              class: "btn " + (danger ? "btn-danger" : "btn-primary"),
              type: "button",
              onclick: () => {
                answer = true;
                dlg.close();
              },
            },
            okLabel,
          ),
        ),
      ],
    });
    dlg.addEventListener("close", () => resolve(answer));
  });
}

// ----------------------------------------------------------------------- dates
const pad = (n) => String(n).padStart(2, "0");
const localParts = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
export const today = () => localParts(new Date());
export const nowLocal = () => {
  const d = new Date();
  return `${localParts(d)}T${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
};
// "2026-01-05T10:00:00" -> valeur acceptée par <input type="datetime-local" step="1">
export const toLocalInput = (v) => (v ? String(v).slice(0, 19) : "");

// Une date SQL "YYYY-MM-DD" interprétée par new Date() serait en UTC (risque de décalage d'un jour).
function parseDate(v) {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(v);
  return m ? new Date(+m[1], +m[2] - 1, +m[3]) : new Date(v);
}

// ---------------------------------------------------------------------- formats
const nf = new Intl.NumberFormat("fr-FR", { maximumFractionDigits: 2 });
const eur = new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR" });

export function fmtValue(value, type) {
  if (value === null || value === undefined || value === "") return h("span", { class: "muted" }, "—");
  switch (type) {
    case "date":
      return parseDate(value).toLocaleDateString("fr-FR");
    case "datetime":
      return new Date(value).toLocaleString("fr-FR", { dateStyle: "short", timeStyle: "short" });
    case "eur":
      return eur.format(value);
    case "kwh":
      return `${nf.format(value)} kWh`;
    case "kw":
      return `${nf.format(value)} kW`;
    case "hours":
      return `${nf.format(value)} h`;
    case "number":
      return nf.format(value);
    case "badge":
      return h("span", { class: `chip chip-${value}` }, String(value).replace("_", " "));
    default:
      return String(value);
  }
}
