// Render a stored address (address-schema.json shape) back into labeled fields
// and a formatted block, using the country metadata (address-fields.json).
//
// Works in Node or the browser. In the browser, pass the metadata in;
// in Node it loads address-fields.json from disk.

// metadata field.key  ->  how to read the value out of a stored address record
const VALUE_ACCESSOR = {
  recipient:          a => a.recipient,
  organization:       a => a.organization,
  streetAddress:      a => (a.addressLines || []).join('\n'),
  dependentLocality:  a => a.dependentLocality,
  locality:           a => a.locality,
  administrativeArea: a => a.administrativeArea,
  postalCode:         a => a.postalCode,
  sortingCode:        a => a.sortingCode,
  landmarkDescriptor: a => a.landmark,   // storage collapses %T/%F/%L into one field...
  landmarkAffix:      a => null,         // ...so only show it once
  landmarkName:       a => null,
};

function loadMetadata() {
  // Node-only convenience; in the browser pass metadata into the functions instead.
  const data = require('./address-fields.json');
  const byCode = {};
  for (const c of data.countries) byCode[c.code] = c;
  return byCode;
}

// 1) Labeled fields, in the country's display order.
//    Returns [{ key, label, value, required, uppercase }]
//    Great for a read view or for re-populating an edit form.
function toLabeledFields(address, metaByCode) {
  const meta = metaByCode[address.regionCode];
  if (!meta) throw new Error('Unknown regionCode: ' + address.regionCode);
  return meta.fields.map(f => {
    const read = VALUE_ACCESSOR[f.key] || (() => undefined);
    let value = read(address);
    if (value == null) value = '';
    if (f.uppercase && value) value = String(value).toUpperCase();
    return { key: f.key, label: f.label, value, required: f.required, uppercase: f.uppercase };
  }).filter(f => f.value !== '' || f.required); // keep required fields even if empty; drop empty optionals
}

// 2) A formatted, multi-line address block using the country's fmt string.
//    Postal code position, separators, prefixes (e.g. Japan's 〒) all come from fmt.
const FMT_VALUE = {
  N: a => a.recipient,
  O: a => a.organization,
  A: a => (a.addressLines || []).join('\n'),
  D: a => a.dependentLocality,
  C: a => a.locality,
  S: a => a.administrativeArea,
  Z: a => a.postalCode,
  X: a => a.sortingCode,
  T: a => a.landmark,
  F: a => null,
  L: a => null,
};

function formatAddress(address, metaByCode) {
  const meta = metaByCode[address.regionCode];
  if (!meta) throw new Error('Unknown regionCode: ' + address.regionCode);
  const upper = new Set(); // which tokens to uppercase, derived from metadata fields
  for (const f of meta.fields) if (f.uppercase) upper.add(f.token.replace('%', ''));

  return meta.format.split('%n').map(line => {
    let out = '', filled = false;
    for (let i = 0; i < line.length; i++) {
      if (line[i] === '%') {
        const t = line[++i];
        const get = FMT_VALUE[t];
        if (get) {
          let v = get(address);
          if (v == null) v = '';
          if (v && upper.has(t)) v = String(v).toUpperCase();
          if (v) filled = true;
          out += v;
        } else {
          out += t; // unknown token -> literal
        }
      } else {
        out += line[i];
      }
    }
    return filled ? out.replace(/\s+/g, ' ').trim() : null; // drop empty lines, tidy separators
  }).filter(l => l !== null).join('\n');
}

module.exports = { toLabeledFields, formatAddress, loadMetadata, VALUE_ACCESSOR };

// ---- demo when run directly: node render.js ----
if (require.main === module) {
  const meta = loadMetadata();
  const examples = require('./address-schema.json').examples;
  for (const addr of examples) {
    console.log('\n===== ' + addr.regionCode + ' =====');
    console.log('Labeled fields:');
    for (const f of toLabeledFields(addr, meta)) {
      console.log('   ' + (f.label + (f.required ? ' *' : '')).padEnd(20) + ' : ' + f.value.replace(/\n/g, ' / '));
    }
    console.log('Formatted:');
    console.log(formatAddress(addr, meta).split('\n').map(l => '   ' + l).join('\n'));
  }
}
