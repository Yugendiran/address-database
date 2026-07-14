/* form.js — dynamic, validated, schema-mapped address form.
   - country list from ADDRESS_DATA
   - fields rendered from address-fields.json (order, labels, required)
   - select vs input from FIELD_MAPPING; cascading options lazy-loaded per country
   - output conforms to address-schema.json fieldReference
*/
(function () {
  "use strict";

  const META = {};
  ((window.ADDRESS_DATA || {}).countries || []).forEach(c => (META[c.code] = c));
  const EXAMPLES = {};
  ((window.ADDRESS_EXAMPLES || {}).addresses || []).forEach(a => (EXAMPLES[a.regionCode] = a));
  const MAN = window.SUBREG_MANIFEST || {};
  const MAPPING = window.FIELD_MAPPING || {};
  const POSTAL = window.POSTAL_PATTERNS || {};

  // metadata field.key -> schema (fieldReference) key
  const TO_SCHEMA = {
    recipient: "recipient", organization: "organization",
    streetAddress: "addressLines", dependentLocality: "dependentLocality",
    locality: "locality", administrativeArea: "administrativeArea",
    postalCode: "postalCode", sortingCode: "sortingCode",
    landmarkDescriptor: "landmark", landmarkAffix: "landmark", landmarkName: "landmark",
  };
  // fixed source level for each geographic schema field (matches FIELD_MAPPING sources)
  const LEVEL_OF = { administrativeArea: "l1", locality: "l2", dependentLocality: "l3" };
  const PARENT_KEY = { locality: "administrativeArea", dependentLocality: "locality" };

  const SCHEMA_ORDER = ["regionCode", "languageCode", "recipient", "organization",
    "addressLines", "dependentLocality", "locality", "administrativeArea",
    "postalCode", "sortingCode", "landmark", "formatted"];

  // ---- lazy sub-region loader ----
  const cache = {}, pending = {}, injected = {};
  window.registerSubregions = function (cc, data) {
    cache[cc] = data; (pending[cc] || []).forEach(fn => fn(data)); pending[cc] = [];
  };
  function loadCountry(cc) {
    return new Promise(res => {
      if (cache[cc]) return res(cache[cc]);
      if (!MAN[cc]) return res(null);
      (pending[cc] = pending[cc] || []).push(res);
      if (!injected[cc]) {
        injected[cc] = true;
        const s = document.createElement("script");
        s.src = "subregions-geonames/js/" + cc + ".js";
        s.onerror = () => res(null);
        document.head.appendChild(s);
      }
    });
  }

  // ---- helpers ----
  const R = 0x1F1E6 - 65;
  const flag = c => /^[A-Z]{2}$/.test(c) ? String.fromCodePoint(R + c.charCodeAt(0), R + c.charCodeAt(1)) : "🏳️";
  const esc = s => String(s).replace(/[&<>"]/g, m => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[m]));
  const el = id => document.getElementById(id);

  // ---- state ----
  let cc = null;               // current country
  const model = {};            // schema record being built
  const selKey = {};           // chosen option KEYS for cascade filtering (by schema field)
  const controls = {};         // schema field -> DOM control
  const fieldMeta = {};        // schema field -> metadata field (label/required/uppercase)

  // ---- build the form for a country ----
  function renderForm(code) {
    cc = code;
    const meta = META[cc];
    Object.keys(model).forEach(k => delete model[k]);
    Object.keys(selKey).forEach(k => delete selKey[k]);
    Object.keys(controls).forEach(k => delete controls[k]);
    Object.keys(fieldMeta).forEach(k => delete fieldMeta[k]);

    model.regionCode = cc;
    model.languageCode = (meta.languages || "").split("~")[0] || "";

    el("flag").textContent = flag(cc);
    el("formSub").textContent = meta.name + " · fmt " + meta.format;
    el("country").value = cc;
    el("status").textContent = "";

    el("metaRow").innerHTML =
      `<span class="pill"><b>${cc}</b> regionCode</span>` +
      `<span class="pill">lang <b>${model.languageCode || "—"}</b></span>` +
      `<span class="pill"><b>${meta.fields.length}</b> fields</span>` +
      (POSTAL[cc] ? `<span class="pill">postal check <b>on</b></span>` : `<span class="pill">postal check <b>off</b></span>`);

    const form = el("form");
    form.innerHTML = "";
    const seen = new Set();
    const GEO = ["administrativeArea", "locality", "dependentLocality"];
    const GEO_TOKEN = { administrativeArea: "%S", locality: "%C", dependentLocality: "%D" };
    const cmap = MAPPING[cc] || {};

    // non-geographic fields, in format order (dedup the 3 landmark keys)
    const renderList = [];
    meta.fields.forEach(f => {
      const schemaKey = TO_SCHEMA[f.key];
      if (!schemaKey || seen.has(schemaKey)) return;
      seen.add(schemaKey);
      if (GEO.includes(schemaKey)) return;   // geographic slots handled as a group below
      renderList.push({ schemaKey, f });
    });

    // geographic slots as one cascade group, in level order, each labeled with the
    // country's real admin-level name (State / District / Sub-district…).
    const geoGroup = [];
    GEO.forEach(slot => {
      const m = cmap[slot];
      if (!m) return;
      const formF = meta.fields.find(x => TO_SCHEMA[x.key] === slot);
      const isSelect = m.control === "select";
      const label = isSelect && m.levelName ? m.levelName : (formF ? formF.label : (m.levelName || slot));
      geoGroup.push({
        schemaKey: slot,
        f: {
          key: slot, label,
          token: formF ? formF.token : GEO_TOKEN[slot],
          required: formF ? formF.required : false,
          uppercase: formF ? formF.uppercase : false,
          added: !!m.added,
          slotLabel: m.slotLabel || null,   // original postal label if the slot was reused
        },
      });
    });
    // place the geo group before postalCode (keeps parent→child cascade order)
    let gpos = renderList.findIndex(x => x.schemaKey === "postalCode");
    if (gpos < 0) gpos = renderList.length;
    renderList.splice(gpos, 0, ...geoGroup);

    renderList.forEach(({ schemaKey, f }) => {
      fieldMeta[schemaKey] = f;
      const map = cmap[schemaKey];
      const isSelect = map && map.control === "select";
      const wrap = document.createElement("div");
      wrap.className = "field";
      wrap.dataset.key = schemaKey;

      const kind = isSelect ? "select" : "input";
      const reused = f.slotLabel && f.slotLabel !== f.label;
      wrap.innerHTML =
        `<label>${esc(f.label)}${f.required ? '<span class="star">*</span>' : ""}` +
        (f.added ? '<span class="kind select">added</span>'
                 : `<span class="kind ${kind}">${isSelect ? "dropdown" : "text"}</span>`) +
        `<span class="schemakey">${schemaKey}${map && map.source ? " ← " + map.source : ""}</span></label>` +
        controlHTML(schemaKey, f, isSelect) +
        `<div class="err"></div>` +
        (schemaKey === "postalCode" && POSTAL[cc] && POSTAL[cc].zipex
          ? `<div class="hint">e.g. ${esc(POSTAL[cc].zipex.split(",")[0])}</div>` : "") +
        (f.added ? `<div class="hint">Not in ${esc(meta.name)}'s postal format — captured but not shown in the formatted block.</div>` : "") +
        (reused ? `<div class="hint">Reusing the “${esc(f.slotLabel)}” slot for this admin level.</div>` : "");
      form.appendChild(wrap);

      const ctrl = wrap.querySelector(".ctrl");
      controls[schemaKey] = ctrl;
      wireControl(schemaKey, ctrl, isSelect);
    });

    // populate any selects (lazy-load the country's sub-region data)
    loadCountry(cc).then(data => {
      if (!data) return;
      if (controls.administrativeArea && controls.administrativeArea.tagName === "SELECT")
        fillSelect(controls.administrativeArea, data.l1);
      // locality / dependentLocality start empty until their parent is chosen
    });

    update();
  }

  function controlHTML(schemaKey, f, isSelect) {
    if (schemaKey === "addressLines")
      return `<textarea class="ctrl" rows="2" placeholder="Street address (one line each)"></textarea>`;
    if (isSelect)
      return `<select class="ctrl"${PARENT_KEY[schemaKey] ? " disabled" : ""}><option value="">— select —</option></select>`;
    return `<input class="ctrl ${f.uppercase ? "up" : ""}" type="text" placeholder="${esc(f.label)}">`;
  }

  function fillSelect(sel, options) {
    sel.innerHTML = '<option value="">— select —</option>' +
      options.map(o => `<option value="${esc(o.key)}" data-name="${esc(o.name)}">${esc(o.name)}</option>`).join("");
    sel.disabled = options.length === 0;
  }

  function wireControl(schemaKey, ctrl, isSelect) {
    if (isSelect) {
      ctrl.addEventListener("change", () => {
        const opt = ctrl.selectedOptions[0];
        const name = opt ? opt.getAttribute("data-name") || "" : "";
        model[schemaKey] = name;              // STORE THE NAME
        selKey[schemaKey] = ctrl.value;       // keep KEY for cascade filtering
        cascadeFrom(schemaKey);
        clearError(schemaKey);
        update();
      });
    } else if (schemaKey === "addressLines") {
      ctrl.addEventListener("input", () => {
        model.addressLines = ctrl.value.split("\n").map(s => s.trim()).filter(Boolean);
        clearError(schemaKey); update();
      });
    } else {
      ctrl.addEventListener("input", () => {
        model[schemaKey] = ctrl.value;
        clearError(schemaKey); update();
      });
    }
  }

  // repopulate child selects when a parent selection changes
  function cascadeFrom(parentKey) {
    const data = cache[cc]; if (!data) return;
    const child = parentKey === "administrativeArea" ? "locality"
                : parentKey === "locality" ? "dependentLocality" : null;
    if (!child || !controls[child] || controls[child].tagName !== "SELECT") return;

    let opts = [];
    if (child === "locality")
      opts = data.l2.filter(x => x.level1 === selKey.administrativeArea);
    else if (child === "dependentLocality")
      opts = data.l3.filter(x => x.level1 === selKey.administrativeArea && x.level2 === selKey.locality);

    fillSelect(controls[child], opts);
    model[child] = ""; delete selKey[child];
    cascadeFrom(child); // clear grandchildren
  }

  // ---- validation ----
  function validate() {
    let ok = true;
    Object.keys(fieldMeta).forEach(schemaKey => {
      const f = fieldMeta[schemaKey];
      const wrap = document.querySelector(`.field[data-key="${schemaKey}"]`);
      const errEl = wrap.querySelector(".err");
      let msg = "";
      const val = schemaKey === "addressLines" ? (model.addressLines || []).join("") : (model[schemaKey] || "");

      if (f.required && !val) msg = (f.label) + " is required";
      else if (schemaKey === "postalCode" && val && POSTAL[cc] && POSTAL[cc].zip) {
        let re;
        try { re = new RegExp("^(?:" + POSTAL[cc].zip + ")$", "i"); } catch (e) { re = null; }
        if (re && !re.test(val)) msg = "Invalid postal code format";
      }
      if (msg) { wrap.classList.add("invalid"); errEl.textContent = msg; ok = false; }
      else wrap.classList.remove("invalid");
    });
    return ok;
  }
  function clearError(schemaKey) {
    const wrap = document.querySelector(`.field[data-key="${schemaKey}"]`);
    if (wrap) wrap.classList.remove("invalid");
  }

  // ---- output ----
  function buildRecord() {
    const rec = {};
    SCHEMA_ORDER.forEach(k => {
      if (k === "addressLines") rec[k] = model.addressLines || [];
      else if (k === "formatted") rec[k] = formatAddress();
      else rec[k] = model[k] || "";
    });
    return rec;
  }

  const FMT = {
    N: () => model.recipient, O: () => model.organization,
    A: () => (model.addressLines || []).join("\n"),
    D: () => model.dependentLocality, C: () => model.locality,
    S: () => model.administrativeArea, Z: () => model.postalCode,
    X: () => model.sortingCode, T: () => model.landmark, F: () => null, L: () => null,
  };
  function formatAddress() {
    const meta = META[cc]; if (!meta) return "";
    const upper = new Set(); meta.fields.forEach(f => { if (f.uppercase) upper.add(f.token.replace("%", "")); });
    return meta.format.split("%n").map(line => {
      let out = "", filled = false;
      for (let i = 0; i < line.length; i++) {
        if (line[i] === "%") {
          const t = line[++i], g = FMT[t];
          if (g) { let v = g() || ""; if (v && upper.has(t)) v = v.toUpperCase(); if (v) filled = true; out += v; }
          else out += t;
        } else out += line[i];
      }
      return filled ? out.replace(/\s+/g, " ").trim() : null;
    }).filter(x => x !== null).join("\n");
  }

  function jsonHTML(rec) {
    const keys = Object.keys(rec);
    return "{\n" + keys.map((k, i) => {
      const v = rec[k], comma = i < keys.length - 1 ? "," : "";
      let val;
      if (Array.isArray(v)) val = v.length ? "[" + v.map(x => `<span class="s">${esc(JSON.stringify(x))}</span>`).join(", ") + "]" : `<span class="empty">[]</span>`;
      else if (v === "") val = `<span class="empty">""</span>`;
      else val = `<span class="s">${esc(JSON.stringify(v))}</span>`;
      return `  <span class="k">"${k}"</span>: ${val}${comma}`;
    }).join("\n") + "\n}";
  }

  function update() {
    const rec = buildRecord();
    el("json").innerHTML = jsonHTML(rec);
    el("addr").textContent = rec.formatted || "(empty)";
  }

  // ---- fill sample (from address-examples.json) ----
  function fillSample() {
    const ex = EXAMPLES[cc]; if (!ex) return;
    Object.keys(controls).forEach(schemaKey => {
      const ctrl = controls[schemaKey];
      if (ctrl.tagName === "SELECT") return; // skip selects (need cascade)
      if (schemaKey === "addressLines") {
        ctrl.value = (ex.addressLines || []).join("\n");
        model.addressLines = (ex.addressLines || []).slice();
      } else {
        ctrl.value = ex[schemaKey] || "";
        model[schemaKey] = ex[schemaKey] || "";
      }
    });
    update();
  }

  // ---- init ----
  const sel = el("country");
  Object.values(META).sort((a, b) => a.name.localeCompare(b.name)).forEach(c => {
    const o = document.createElement("option");
    o.value = c.code; o.textContent = c.name + "  (" + c.code + ")";
    sel.appendChild(o);
  });
  sel.addEventListener("change", () => { location.hash = sel.value; renderForm(sel.value); });
  el("save").addEventListener("click", () => {
    const ok = validate();
    el("status").className = "status " + (ok ? "ok" : "bad");
    el("status").textContent = ok ? "✓ Valid — record ready to store" : "✗ Please fix the highlighted fields";
  });
  el("fill").addEventListener("click", fillSample);
  window.addEventListener("hashchange", () => { const c = location.hash.slice(1); if (META[c]) renderForm(c); });

  const initial = location.hash.slice(1);
  renderForm(META[initial] ? initial : (META.US ? "US" : Object.keys(META)[0]));
})();
