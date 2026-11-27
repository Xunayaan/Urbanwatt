// Écran générique « liste + filtres + formulaire + actions » piloté par entities.js
import { api } from "./api.js";
import { ENTITIES } from "./entities.js";
import { confirmBox, errMsg, fmtValue, h, nowLocal, openModal, toast, today, toLocalInput } from "./ui.js";

const PAGE_SIZE = 15;

// ------------------------------------------------------------- formulaires
function defaultValue(f) {
  if (f.def === "now") return nowLocal();
  if (f.def === "today") return today();
  return f.def ?? "";
}

function buildControl(f, value) {
  const common = { name: f.name, id: `f_${f.name}`, required: !!f.req };
  switch (f.type) {
    case "textarea":
      return h("textarea", { ...common, rows: 3 }, value ?? "");
    case "select":
      return h(
        "select",
        { ...common, value: value ?? "" },
        !f.req && h("option", { value: "" }, "—"),
        f.options.map((o) => h("option", { value: o }, o.replace("_", " "))),
      );
    case "fk":
      return h("select", { ...common }, h("option", { value: "" }, "Chargement…"));
    case "datetime":
      return h("input", { ...common, type: "datetime-local", step: 1, value: toLocalInput(value) });
    case "date":
      return h("input", { ...common, type: "date", value: value ?? "" });
    case "number":
      return h("input", { ...common, type: "number", step: f.step ?? "any", min: f.min, value: value ?? "" });
    default:
      return h("input", {
        ...common,
        type: f.type === "email" ? "email" : "text",
        maxlength: f.max,
        list: f.suggest ? `dl_${f.name}` : null,
        value: value ?? "",
      });
  }
}

// Remplit une liste déroulante de clé étrangère avec les lignes de la table référencée.
async function fillForeignKey(select, f, current) {
  const target = ENTITIES[f.fk];
  try {
    const rows = await api.get(target.path, { limit: 200 });
    select.replaceChildren(h("option", { value: "" }, "— choisir —"));
    for (const r of rows) {
      select.append(h("option", { value: r[target.idField] }, `#${r[target.idField]} · ${target.label(r)}`));
    }
    // la valeur actuelle peut ne pas figurer dans les 200 premières lignes
    if (current && !rows.some((r) => String(r[target.idField]) === String(current))) {
      select.append(h("option", { value: current }, `#${current}`));
    }
    select.value = current ?? "";
  } catch (e) {
    select.replaceChildren(h("option", { value: "" }, `Erreur : ${errMsg(e)}`));
  }
}

// Lit le formulaire et construit le JSON envoyé à l'API.
//  - création : les champs vides sont omis (l'API applique ses valeurs par défaut)
//  - modification (PATCH) : un champ optionnel vidé est envoyé à null
function collect(form, fields, isEdit) {
  const body = {};
  for (const f of fields) {
    const raw = form.elements[f.name].value.trim();
    if (raw === "") {
      if (isEdit && !f.req) body[f.name] = null;
      continue;
    }
    body[f.name] = f.type === "number" || f.type === "fk" ? Number(raw) : raw;
  }
  return body;
}

// Ouvre une fenêtre contenant un formulaire. onSubmit(body) doit appeler l'API (et lever en cas d'erreur).
function openFormModal({ title, fields, values = {}, isEdit = false, submitLabel = "Enregistrer", onSubmit, intro }) {
  const error = h("div", { class: "form-error", role: "alert", hidden: true });
  const form = h("form", { class: "form" });
  const datalists = [];

  for (const f of fields) {
    const initial = isEdit || values[f.name] !== undefined ? values[f.name] : defaultValue(f);
    const control = buildControl(f, initial);
    if (f.suggest) datalists.push(h("datalist", { id: `dl_${f.name}` }, f.suggest.map((s) => h("option", { value: s }))));
    form.append(
      h("label", { class: "field" + (f.type === "textarea" ? " field-wide" : ""), for: `f_${f.name}` },
        h("span", {}, f.label, f.req ? h("em", { class: "req", title: "obligatoire" }, " *") : null),
        control),
    );
    if (f.type === "fk") fillForeignKey(control, f, initial);
  }

  const submit = h("button", { class: "btn btn-primary", type: "submit" }, submitLabel);
  form.append(
    ...datalists,
    error,
    h("div", { class: "actions" }, h("button", { class: "btn", type: "button", onclick: () => dlg.close() }, "Annuler"), submit),
  );

  form.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    submit.disabled = true;
    error.hidden = true;
    try {
      await onSubmit(collect(form, fields, isEdit));
      dlg.close();
    } catch (e) {
      error.textContent = errMsg(e);
      error.hidden = false;
      submit.disabled = false;
    }
  });

  const dlg = openModal({ title, body: [intro ? h("p", { class: "muted" }, intro) : null, form] });
  return dlg;
}

// ------------------------------------------------------- actions métier
const ACTIONS = {
  async detailsSession(row) {
    try {
      const d = await api.get(`/sessions/${row.id_session}/details`);
      const rows = [
        ["Session", `#${d.id_session}`, "text"],
        ["Statut", d.statut, "badge"],
        ["Début", d.debut_session, "datetime"],
        ["Fin", d.fin_session, "datetime"],
        ["Énergie", d.energie_kwh, "kwh"],
        ["Coût", d.cout_eur, "eur"],
        ["Borne", `${d.code_borne} — ${d.puissance_kw} kW, ${d.connecteur}`, "text"],
        ["Station", `${d.nom_station} (${d.ville_station})`, "text"],
        ["Véhicule", `${d.immatriculation} — ${d.marque} ${d.modele}`, "text"],
        ["Client", `${d.prenom_client} ${d.nom_client}`, "text"],
      ];
      openModal({
        title: `Session #${d.id_session} — vue détaillée`,
        body: [
          h("p", { class: "muted" }, "Données issues d'une seule requête avec jointures sur 5 tables."),
          h("dl", { class: "kv" }, rows.map(([k, v, t]) => [h("dt", {}, k), h("dd", {}, fmtValue(v, t))])),
        ],
      });
    } catch (e) {
      toast(errMsg(e), "error");
    }
  },

  terminerSession(row, reload) {
    openFormModal({
      title: `Terminer la session #${row.id_session}`,
      intro: "Enregistre la fin de la recharge. Si la fin est antérieure au début, PostgreSQL refuse (contrainte CHECK).",
      submitLabel: "Terminer la session",
      fields: [
        { name: "energie_kwh", label: "Énergie délivrée (kWh)", type: "number", req: true, min: 0 },
        { name: "cout_eur", label: "Coût (€)", type: "number", min: 0, step: 0.01 },
        { name: "fin_session", label: "Heure de fin (vide = maintenant)", type: "datetime" },
      ],
      onSubmit: async (body) => {
        await api.post(`/sessions/${row.id_session}/terminer`, { body });
        toast("Session terminée", "ok");
        reload();
      },
    });
  },

  async annulerSession(row, reload) {
    if (!(await confirmBox(`Annuler la session #${row.id_session} ?`, { danger: true, okLabel: "Annuler la session" }))) return;
    try {
      await api.post(`/sessions/${row.id_session}/annuler`);
      toast("Session annulée", "ok");
      reload();
    } catch (e) {
      toast(errMsg(e), "error");
    }
  },

  async resoudreIncident(row, reload) {
    if (!(await confirmBox(`Marquer l'incident #${row.id_incident} comme résolu ?`, { okLabel: "Résoudre" }))) return;
    try {
      await api.post(`/incidents/${row.id_incident}/resoudre`);
      toast("Incident résolu (la borne est remise en service s'il n'y a plus d'incident haute gravité ouvert)", "ok");
      reload();
    } catch (e) {
      toast(errMsg(e), "error");
    }
  },

  cloturerIntervention(row, reload) {
    openFormModal({
      title: `Clôturer l'intervention #${row.id_intervention}`,
      submitLabel: "Clôturer",
      values: { compte_rendu: row.compte_rendu ?? "" },
      fields: [{ name: "compte_rendu", label: "Compte rendu", type: "textarea" }],
      onSubmit: async (body) => {
        await api.post(`/interventions/${row.id_intervention}/cloturer`, { body });
        toast("Intervention clôturée", "ok");
        reload();
      },
    });
  },
};

// --------------------------------------------------------------- écran
export function renderEntity(root, key, presetFilters = {}) {
  const ent = ENTITIES[key];
  const state = { skip: 0, filters: { ...presetFilters } };
  let seq = 0; // ignore les réponses obsolètes si l'utilisateur change vite de filtre

  const tableWrap = h("div", { class: "table-wrap" });
  const pager = h("div", { class: "pager" });

  const reload = () => load();

  async function load() {
    const mine = ++seq;
    tableWrap.replaceChildren(h("div", { class: "empty" }, "Chargement…"));
    try {
      const rows = await api.get(ent.path, { ...state.filters, skip: state.skip, limit: PAGE_SIZE });
      if (mine !== seq) return;
      drawTable(rows);
      drawPager(rows.length);
    } catch (e) {
      if (mine !== seq) return;
      tableWrap.replaceChildren(h("div", { class: "empty error" }, errMsg(e)));
      pager.replaceChildren();
    }
  }

  function rowActions(row) {
    const id = row[ent.idField];
    const buttons = [];
    for (const l of ent.links || []) {
      buttons.push(h("a", { class: "btn btn-sm btn-link", href: l.to(row) }, l.label));
    }
    for (const a of ent.actions || []) {
      if (a.show && !a.show(row)) continue;
      buttons.push(h("button", { class: "btn btn-sm", type: "button", onclick: () => ACTIONS[a.run](row, reload) }, a.label));
    }
    buttons.push(
      h("button", {
        class: "btn btn-sm", type: "button",
        onclick: () =>
          openFormModal({
            title: `Modifier ${ent.singular} #${id}`,
            fields: ent.fields.filter((f) => !f.createOnly),
            values: row,
            isEdit: true,
            onSubmit: async (body) => {
              await api.patch(`${ent.path}/${id}`, { body });
              toast("Modifications enregistrées", "ok");
              reload();
            },
          }),
      }, "Modifier"),
      h("button", {
        class: "btn btn-sm btn-danger-ghost", type: "button",
        onclick: async () => {
          if (!(await confirmBox(`Supprimer ${ent.singular} #${id} ?`, { danger: true, okLabel: "Supprimer" }))) return;
          try {
            await api.del(`${ent.path}/${id}`);
            toast("Supprimé", "ok");
            if (state.skip > 0 && tableWrap.querySelectorAll("tbody tr").length === 1) state.skip -= PAGE_SIZE;
            reload();
          } catch (e) {
            toast(errMsg(e), "error", 8000); // ex. 409 : la ligne est encore référencée par une clé étrangère
          }
        },
      }, "Supprimer"),
    );
    return h("td", { class: "row-actions" }, h("div", {}, buttons));
  }

  function drawTable(rows) {
    if (!rows.length) {
      tableWrap.replaceChildren(h("div", { class: "empty" }, "Aucun résultat."));
      return;
    }
    tableWrap.replaceChildren(
      h("table", { class: "grid" },
        h("thead", {}, h("tr", {}, ent.columns.map(([, label]) => h("th", {}, label)), h("th", {}, ""))),
        h("tbody", {}, rows.map((row) =>
          h("tr", {},
            ent.columns.map(([field, , type]) => {
              const t = type || (["statut", "etat", "gravite"].includes(field) ? "badge" : "text");
              return h("td", { class: field === "compte_rendu" ? "truncate" : null, "data-label": field }, fmtValue(row[field], t));
            }),
            rowActions(row)))),
      ),
    );
  }

  function drawPager(count) {
    const page = state.skip / PAGE_SIZE + 1;
    pager.replaceChildren(
      h("button", { class: "btn btn-sm", type: "button", disabled: state.skip === 0, onclick: () => { state.skip -= PAGE_SIZE; load(); } }, "← Précédent"),
      h("span", { class: "muted" }, `Page ${page}`),
      h("button", { class: "btn btn-sm", type: "button", disabled: count < PAGE_SIZE, onclick: () => { state.skip += PAGE_SIZE; load(); } }, "Suivant →"),
    );
  }

  function filterBar() {
    if (!ent.filters.length) return null;
    const inputs = ent.filters.map((f) => {
      const value = state.filters[f.name] ?? "";
      const onchange = (ev) => {
        const v = ev.target.value.trim();
        if (v) state.filters[f.name] = v;
        else delete state.filters[f.name];
        state.skip = 0;
        load();
      };
      const control = f.options
        ? h("select", { onchange, value }, h("option", { value: "" }, "Tous"),
            f.options.map((o) => (Array.isArray(o) ? h("option", { value: o[0] }, o[1]) : h("option", { value: o }, o.replace("_", " ")))))
        : h("input", { type: f.type === "number" ? "number" : "search", min: f.type === "number" ? 0 : null, onchange, value });
      return h("label", { class: "filter" }, h("span", {}, f.label), control);
    });
    return h("div", { class: "filters" }, inputs,
      h("button", {
        class: "btn btn-sm btn-link", type: "button",
        onclick: () => {
          history.replaceState(null, "", `#/${key}`); // nettoie l'URL (?id_client=3...) sans relancer le routage
          renderEntity(root, key, {});
        },
      }, "Réinitialiser"));
  }

  root.replaceChildren(
    h("div", { class: "page-head" },
      h("div", {}, h("h1", {}, ent.title), ent.note ? h("p", { class: "muted" }, ent.note) : null),
      h("button", {
        class: "btn btn-primary", type: "button",
        onclick: () =>
          openFormModal({
            title: `Nouveau — ${ent.title}`,
            fields: ent.fields.filter((f) => !f.editOnly),
            submitLabel: "Créer",
            onSubmit: async (body) => {
              await api.post(ent.path, { body });
              toast("Créé avec succès", "ok");
              state.skip = 0;
              reload();
            },
          }),
      }, "+ Nouveau")),
    filterBar(),
    tableWrap,
    pager,
  );
  load();
}
