/* viewer.js — convert a stored address (template shape) into the country-labeled
   display view, using the country metadata. Pure functions + UI wiring. */
(function () {
  "use strict";

  const META = {};
  ((window.ADDRESS_DATA || {}).countries || []).forEach(c => (META[c.code] = c));
  const EXAMPLES = {};
  ((window.ADDRESS_EXAMPLES || {}).addresses || []).forEach(a => (EXAMPLES[a.regionCode] = a));

  const CODES = Object.keys(EXAMPLES).sort((a, b) =>
    (META[a] ? META[a].name : a).localeCompare(META[b] ? META[b].name : b));

  // ---- pure conversion layer (same contract as render.js) ----

  // metadata field.key -> how to read the value from a stored template record
  const VALUE_ACCESSOR = {
    recipient:          a => a.recipient,
    organization:       a => a.organization,
    streetAddress:      a => (a.addressLines || []).join("\n"),
    dependentLocality:  a => a.dependentLocality,
    locality:           a => a.locality,
    administrativeArea: a => a.administrativeArea,
    postalCode:         a => a.postalCode,
    sortingCode:        a => a.sortingCode,
    landmarkDescriptor: a => a.landmark,   // storage collapses %T/%F/%L
    landmarkAffix:      a => null,
    landmarkName:       a => null,
  };

  // metadata field.key -> which template key it maps to (for the "keymap" hint)
  const STORE_KEY = {
    recipient: "recipient", organization: "organization", streetAddress: "addressLines",
    dependentLocality: "dependentLocality", locality: "locality",
    administrativeArea: "administrativeArea", postalCode: "postalCode",
    sortingCode: "sortingCode", landmarkDescriptor: "landmark",
    landmarkAffix: "landmark", landmarkName: "landmark",
  };

  // Convert stored record -> ordered labeled fields.
  function toLabeledFields(address) {
    const meta = META[address.regionCode];
    if (!meta) throw new Error("Unknown regionCode " + address.regionCode);
    return meta.fields.map(f => {
      const read = VALUE_ACCESSOR[f.key] || (() => "");
      let value = read(address);
      if (value == null) value = "";
      if (f.uppercase && value) value = String(value).toUpperCase();
      return {
        key: f.key, storeKey: STORE_KEY[f.key], label: f.label,
        token: f.token, value, required: !!f.required, uppercase: !!f.uppercase,
      };
    });
  }

  const FMT_VALUE = {
    N: a => a.recipient, O: a => a.organization,
    A: a => (a.addressLines || []).join("\n"),
    D: a => a.dependentLocality, C: a => a.locality,
    S: a => a.administrativeArea, Z: a => a.postalCode, X: a => a.sortingCode,
    T: a => a.landmark, F: () => null, L: () => null,
  };

  function formatAddress(address) {
    const meta = META[address.regionCode];
    if (!meta) return "";
    const upper = new Set();
    meta.fields.forEach(f => { if (f.uppercase) upper.add(f.token.replace("%", "")); });
    return meta.format.split("%n").map(line => {
      let out = "", filled = false;
      for (let i = 0; i < line.length; i++) {
        if (line[i] === "%") {
          const t = line[++i], get = FMT_VALUE[t];
          if (get) {
            let v = get(address); if (v == null) v = "";
            if (v && upper.has(t)) v = String(v).toUpperCase();
            if (v) filled = true; out += v;
          } else out += t;
        } else out += line[i];
      }
      return filled ? out.replace(/\s+/g, " ").trim() : null;
    }).filter(l => l !== null).join("\n");
  }

  // ---- view helpers ----
  const R = 0x1F1E6 - 65;
  const flag = c => /^[A-Z]{2}$/.test(c)
    ? String.fromCodePoint(R + c.charCodeAt(0), R + c.charCodeAt(1)) : "🏳️";
  const esc = s => String(s).replace(/[&<>]/g, m => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[m]));

  // pretty JSON with empty fields dimmed
  function jsonHTML(obj) {
    const lines = ["{"];
    const keys = Object.keys(obj);
    keys.forEach((k, i) => {
      const v = obj[k];
      const comma = i < keys.length - 1 ? "," : "";
      const isEmpty = v === "" || (Array.isArray(v) && v.length === 0);
      let val;
      if (Array.isArray(v)) {
        val = v.length ? "[" + v.map(x => `<span class="s">${esc(JSON.stringify(x))}</span>`).join(", ") + "]"
                       : `<span class="empty">[]</span>`;
      } else if (v === "") {
        val = `<span class="empty">""</span>`;
      } else {
        const shown = k === "formatted" ? JSON.stringify(v) : JSON.stringify(v);
        val = `<span class="s">${esc(shown)}</span>`;
      }
      lines.push(`  <span class="k">"${esc(k)}"</span>: ${val}${comma}`);
    });
    lines.push("}");
    return lines.join("\n");
  }

  // ---- render ----
  const el = id => document.getElementById(id);
  const sel = el("country");
  CODES.forEach(code => {
    const o = document.createElement("option");
    o.value = code;
    o.textContent = (META[code] ? META[code].name : code) + "  (" + code + ")";
    sel.appendChild(o);
  });

  function render(code) {
    const rec = EXAMPLES[code], meta = META[code];
    if (!rec || !meta) return;
    document.title = (meta.name) + " · Template → Labeled";
    el("pflag").textContent = flag(code);
    el("bigflag").textContent = flag(code);
    el("cname").textContent = meta.name;
    el("csub").textContent =
      `${code} · ${meta.fields.length} fields · format: ${meta.format}`;
    el("rc").textContent = code;
    sel.value = code;

    el("jsonView").innerHTML = jsonHTML(rec);

    const fields = toLabeledFields(rec);
    el("fields").innerHTML = fields.map(f => {
      const blank = f.value === "";
      const tag = f.uppercase ? `<span class="tag">UPPER</span>` : "";
      return `<div class="fld">
        <div class="lab">${esc(f.label)}${f.required ? '<span class="star">*</span>' : ""}${tag}
          <div class="keymap">${esc(f.token)} · ${esc(f.storeKey)}</div></div>
        <div class="val ${f.uppercase ? "up" : ""} ${blank ? "blank" : ""}">${blank ? "— not collected —" : esc(f.value)}</div>
      </div>`;
    }).join("");

    el("addr").textContent = formatAddress(rec) || "(empty)";

    const filled = fields.filter(f => f.value !== "").length;
    el("note").textContent =
      `${filled} of ${fields.length} fields populated · labels & order come entirely from the country metadata (regionCode = ${code}).`;

    if (window.AdminControl)
      AdminControl.build(code, document.getElementById("adminMount"));

    if (location.hash.slice(1) !== code) history.replaceState(null, "", "#" + code);
  }

  function step(dir) {
    const i = CODES.indexOf(sel.value);
    const j = Math.min(CODES.length - 1, Math.max(0, i + dir));
    render(CODES[j]);
  }

  sel.addEventListener("change", () => render(sel.value));
  el("prev").addEventListener("click", () => step(-1));
  el("next").addEventListener("click", () => step(1));
  document.addEventListener("keydown", e => {
    if (e.target.tagName === "SELECT") return;
    if (e.key === "ArrowLeft") step(-1);
    if (e.key === "ArrowRight") step(1);
  });
  window.addEventListener("hashchange", () => {
    const c = location.hash.slice(1); if (EXAMPLES[c]) render(c);
  });

  const initial = location.hash.slice(1);
  render(EXAMPLES[initial] ? initial : (EXAMPLES.US ? "US" : CODES[0]));
})();
