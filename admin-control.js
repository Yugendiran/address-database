/* admin-control.js — shared by index.html and viewer.html.
   Strategy B: render a cascading <select> for any admin level that HAS data,
   a text <input> where the country's format collects the mapped field but we
   have no options, and nothing where neither applies.

   Needs, loaded before this file:
     window.SUBREG_MANIFEST   (subregions-geonames/manifest.js)  -> { CC:{l1,l2,l3} }
     window.ADDRESS_DATA      (data.js)                          -> for field labels
   Per-country option data is lazy-loaded from subregions-geonames/js/<CC>.js
   which calls registerSubregions(CC, {l1,l2,l3}).
*/
(function () {
  const MAN = window.SUBREG_MANIFEST || {};
  const META = {};
  ((window.ADDRESS_DATA || {}).countries || []).forEach(c => (META[c.code] = c));

  const cache = {}, pending = {}, injected = {};
  window.registerSubregions = function (cc, data) {
    cache[cc] = data;
    (pending[cc] || []).forEach(fn => fn(data));
    pending[cc] = [];
  };
  function loadCountry(cc) {
    return new Promise(resolve => {
      if (cache[cc]) return resolve(cache[cc]);
      if (!MAN[cc]) return resolve(null);
      (pending[cc] = pending[cc] || []).push(resolve);
      if (!injected[cc]) {
        injected[cc] = true;
        const s = document.createElement("script");
        s.src = "subregions-geonames/js/" + cc + ".js";
        s.onerror = () => resolve(null);
        document.head.appendChild(s);
      }
    });
  }

  // level -> the address-format field it lines up with, + a fallback label
  const MAP = {
    1: { formKey: "administrativeArea", fallback: "Admin area" },
    2: { formKey: "locality",           fallback: "District"   },
    3: { formKey: "dependentLocality",  fallback: "Sub-district" },
  };

  function labelFor(cc, level) {
    const m = META[cc];
    const f = m && m.fields.find(x => x.key === MAP[level].formKey);
    return "Level " + level + " · " + (f ? f.label : MAP[level].fallback);
  }

  // Decide what to render for each level. Returns [{level,control,label}]
  function plan(cc) {
    const man = MAN[cc] || { l1: 0, l2: 0, l3: 0 };
    const has = new Set((META[cc] ? META[cc].fields : []).map(f => f.key));
    const out = [];
    for (const level of [1, 2, 3]) {
      const count = man["l" + level];
      const formPresent = has.has(MAP[level].formKey);
      let control = null;
      if (count > 0) control = "select";          // Strategy B: data exists -> dropdown
      else if (formPresent) control = "input";     // collected but no options -> text
      if (control) out.push({ level, control, label: labelFor(cc, level), count });
    }
    return out;
  }

  // Build the controls into `mount`. Optional onChange(values) callback.
  function build(cc, mount, onChange) {
    mount.innerHTML = "";
    const spec = plan(cc);
    if (!spec.length) {
      mount.innerHTML = '<div class="ac-empty">No administrative divisions for this country — free text only.</div>';
      return;
    }
    const els = {};
    spec.forEach(s => {
      const wrap = document.createElement("div");
      wrap.className = "ac-field";
      const lab = document.createElement("label");
      lab.textContent = s.label;
      const badge = document.createElement("span");
      badge.className = "ac-badge " + s.control;
      badge.textContent = s.control === "select" ? "dropdown · " + s.count : "text input";
      lab.appendChild(badge);
      let ctrl;
      if (s.control === "select") {
        ctrl = document.createElement("select");
        ctrl.innerHTML = '<option value="">— select —</option>';
        if (s.level > 1) ctrl.disabled = true; // enabled once parent chosen
      } else {
        ctrl = document.createElement("input");
        ctrl.type = "text";
        ctrl.placeholder = "Enter " + s.label.split("· ")[1].toLowerCase();
      }
      ctrl.className = "ac-input";
      wrap.appendChild(lab);
      wrap.appendChild(ctrl);
      mount.appendChild(wrap);
      els[s.level] = ctrl;
    });

    function fill(sel, options) {
      sel.innerHTML = '<option value="">— select —</option>' +
        options.map(o => `<option value="${o.key}">${o.name.replace(/</g, "&lt;")}</option>`).join("");
      sel.disabled = options.length === 0;
    }
    function values() {
      const v = {};
      Object.keys(els).forEach(l => (v["level" + l] = els[l].value));
      return v;
    }

    // populate selects (lazy-load the country's data)
    loadCountry(cc).then(data => {
      if (!data) return;
      if (els[1] && els[1].tagName === "SELECT") fill(els[1], data.l1);
      const relabel = () => onChange && onChange(values());

      if (els[1]) els[1].addEventListener("change", () => {
        const k1 = els[1].value;
        if (els[2] && els[2].tagName === "SELECT")
          fill(els[2], data.l2.filter(x => x.level1 === k1));
        if (els[3] && els[3].tagName === "SELECT") fill(els[3], []);
        relabel();
      });
      if (els[2]) els[2].addEventListener("change", () => {
        const k1 = els[1] ? els[1].value : "", k2 = els[2].value;
        if (els[3] && els[3].tagName === "SELECT")
          fill(els[3], data.l3.filter(x => x.level1 === k1 && x.level2 === k2));
        relabel();
      });
      if (els[3]) els[3].addEventListener("change", relabel);
    });
  }

  window.AdminControl = { build, plan, loadCountry };
})();
