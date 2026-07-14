/* field-control.js — decide dropdown vs text input for level 1/2/3, and
   load cascading options. Framework-agnostic.

   Inputs you load once:
     COUNTS  = subregions-geonames/index.json  -> .counts   { CC: {level1,level2,level3} }
     L1/L2/L3 = subregions-geonames/level{1,2,3}.json       { CC: [ {key,name,level1,level2} ] }
     FIELDS  = address-fields.json (optional) -> to know if the country even collects the field
*/

// Which control to render for a given country + level.
// Returns "select" when we have options, otherwise "input".
function controlFor(counts, regionCode, level) {
  const c = counts[regionCode];
  return c && c["level" + level] > 0 ? "select" : "input";
}

// Options for level 1 (no parent).
function level1Options(L1, regionCode) {
  return L1[regionCode] || [];
}

// Options for level 2, filtered to the chosen level-1 key. Empty until parent picked.
function level2Options(L2, regionCode, level1Key) {
  if (!level1Key) return [];
  return (L2[regionCode] || []).filter(x => x.level1 === level1Key);
}

// Options for level 3, filtered to the chosen level-1 + level-2 keys.
function level3Options(L3, regionCode, level1Key, level2Key) {
  if (!level1Key || !level2Key) return [];
  return (L3[regionCode] || []).filter(x => x.level1 === level1Key && x.level2 === level2Key);
}

/* Full plan for a country's 3 admin levels:
   - render:  does the address FORMAT collect this field at all? (needs address-fields.json)
   - control: "select" | "input"
   You map level 1/2/3 onto your form fields (administrativeArea / locality / dependentLocality).
*/
function adminPlan(counts, fields, regionCode) {
  // which form fields this country's format actually has
  const has = new Set((fields && fields[regionCode] ? fields[regionCode].fields : []).map(f => f.key));
  const FORM_FIELD = { 1: "administrativeArea", 2: "locality", 3: "dependentLocality" };
  return [1, 2, 3].map(level => {
    const formKey = FORM_FIELD[level];
    return {
      level,
      formField: formKey,
      render: fields ? has.has(formKey) : true,          // if no fields map given, assume render
      control: controlFor(counts, regionCode, level),    // select vs input
      cascades: level > 1,                               // depends on the level above
    };
  });
}

if (typeof module !== "undefined") {
  module.exports = { controlFor, level1Options, level2Options, level3Options, adminPlan };
}
