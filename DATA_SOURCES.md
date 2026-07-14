# Data Sources & Generation Pipeline

This document records **every source** the datasets in this project came from, **how**
each was scraped/extracted, and **how** each JSON was formatted and generated. Written
so the whole pipeline can be reproduced or audited.

Last generated: 2026-07-14.

---

## 1. Sources at a glance

| # | Source | What it gave us | Access method | License |
|---|--------|-----------------|---------------|---------|
| A | **Google/Chromium address metadata service** — `https://chromium-i18n.appspot.com/ssl-address/data` | Canonical list of country/region codes | HTTP GET (`curl`) | Google, public endpoint |
| B | **libaddressinput repo** (local checkout at `/Users/yugi/Documents/Projects/libaddressinput`) — `common/.../RegionDataConstants.java` + `AddressField.java` | Per-country address **format** (fields, order, required, uppercase, labels) | Parsed local source files | Apache-2.0 |
| C | **libaddressinput** — `testdata/countryinfo.txt` | Sub-region lists for 39 countries (states, some cities/districts) + postal regexes | Parsed local test file | Apache-2.0 |
| D | **GeoNames** — `https://download.geonames.org/export/dump/allCountries.zip` | Full admin hierarchy (ADM1→ADM2→ADM3) for 228 countries | HTTP download + stream-filter | **CC-BY 4.0** (attribution required) |
| E | **Authored by Claude** (not scraped) | English country names; example address values | Written from knowledge | n/a |

> **Attribution note (GeoNames CC-BY 4.0):** any product shipping the `subregions-geonames/`
> data must credit GeoNames (e.g. "Geographic data © GeoNames, CC-BY 4.0").

---

## 2. Per-file provenance

### `countries.json` — 252 country codes + names
- **Codes** from **Source A**. The endpoint returns
  `{"countries":"AC~AD~AE~..."}`; split on `~`.
  ```bash
  curl -s "https://chromium-i18n.appspot.com/ssl-address/data"
  ```
- **Names**: **Source E** — mapped from ISO-3166 alpha-2 to canonical English
  short names by Claude (the endpoint has no names). *Not a scraped feed.*
- Shape: `{ source, count, countries:[{code,name}] }`.

### `address-fields.json` — what each of the 252 countries collects
- From **Source B**. Parsed `RegionDataConstants.java`, which embeds one JSON
  blob per country in `map.put("US","{...}")` lines (Java string concatenation
  reassembled, `\"` unescaped).
- Token meaning from `AddressField.java`: `%N`=recipient, `%O`=organization,
  `%A`=street, `%D`=dependent locality, `%C`=locality, `%S`=admin area,
  `%Z`=postal, `%X`=sorting code, `%T/%F/%L`=India landmark fields, `%n`=newline.
- Defaults (`fmt=%N%n%O%n%A%n%C`, `require=AC`) come from that file's `ZZ` fallback entry.
- For each country we derive the ordered field list from `fmt`, apply the
  country's `*_name_type` overrides to produce correct labels (PIN code / Emirate /
  Prefecture…), and flag `required` (from `require`) and `uppercase` (from `upper`).
- Shape: `{ source, count, countries:[{code,name,languages,format,requiredKeys,fields:[{key,label,token,required,uppercase}]}] }`.

### `address-schema.json` — the generic storage template
- **Authored** design artifact (not scraped). Based on `google.type.PostalAddress`.
- Defines the single flat record used to store any country's address
  (`regionCode`, `languageCode`, `recipient`, `organization`, `addressLines[]`,
  `dependentLocality`, `locality`, `administrativeArea`, `postalCode`,
  `sortingCode`, `landmark`, `formatted`) plus a field reference and worked examples.

### `address-examples.json` — one example address per country (252), in template shape
- **Structure** derived from `address-fields.json` (only the fields a country
  collects are populated; `formatted` rendered through that country's `fmt`).
- **Values**: **Source E** — synthetic placeholders authored by Claude. ~18 major
  countries have realistic curated values (US/JP/CN/KR/RU localized); the rest use
  clean generic placeholders. *These are sample data, not real deliverable addresses.*

### `subregions/` — sub-regions from libaddressinput (LEGACY / shallow)
- From **Source C** (`testdata/countryinfo.txt`). Parsed `data/CC/...=<json>` lines;
  path depth → level (country/level1/level2/level3). Kept `key`, `name`, `lname`,
  `isoid`, `zip`, `zipex`, `lang`.
- Coverage: **only 39 countries**, most just level-1 (states). Only 6 go deeper
  (CN, BR, KR, TW, CL, HK). India = states only, no districts. **Superseded by
  `subregions-geonames/`** but retained because it carries postal-code regexes.
- Files: `level1.json`, `level2.json`, `level3.json`, `index.json` (keyed by country;
  L2/L3 entries carry `level1`/`level2` parent codes).

### `subregions-geonames/` — full admin hierarchy (PRIMARY)
- From **Source D** (GeoNames). Coverage: **228 of 252 countries**; the 24 missing
  are uninhabited or single-unit territories with no sub-divisions (Antarctica,
  Vatican, Singapore, small islands…).
- Levels: `level1`=ADM1 (state/province, 3,865), `level2`=ADM2 (district/county,
  47,549), `level3`=ADM3 (sub-district, 169,804).
- Entry shape: `{ key, name, lname?, geonameid, level1?, level2? }` where `key` is the
  GeoNames admin code and `level1`/`level2` are the parent codes. `name`=local script,
  `lname`=Latin (only when different).
- Files: `level1.json`, `level2.json`, `level3.json` (keyed by country), `index.json`
  (per-country counts), `manifest.js` (tiny counts-only file for the UI), and
  `js/<CC>.js` (228 per-country option bundles, lazy-loaded by the web UI).

### Derived / UI files (no external data)
- `data.js` = `address-fields.json` as a `window.ADDRESS_DATA` script (browser/`file://`).
- `examples.js` = `address-examples.json` as `window.ADDRESS_EXAMPLES`.
- `render.js`, `field-control.js`, `admin-control.js` = pure logic (join, label,
  select-vs-input decision, cascading).
- `index.html`, `viewer.html`, `viewer.js` = the two web UIs.

---

## 3. Generation pipeline (reproduce)

All generator scripts live in the session scratchpad. Order:

```
# A. countries.json
curl -s "https://chromium-i18n.appspot.com/ssl-address/data"   # split "countries" on ~; add English names

# B. address-fields.json   (parse libaddressinput Java)
python3 gen_fields.py
#   reads: libaddressinput/common/.../RegionDataConstants.java  (+ AddressField.java, ZZ defaults)
#   token+name_type -> ordered fields with labels/required/uppercase

# address-examples.json + examples.js   (uses address-fields.json)
python3 gen_examples.py
#   fills only collected fields; renders `formatted` via each country's fmt

# C. subregions/  (parse libaddressinput testdata)
python3 gen_subregions.py
#   reads: libaddressinput/testdata/countryinfo.txt ; depth -> level ; parent codes

# D. subregions-geonames/  (GeoNames full hierarchy)
curl -s -o allCountries.zip https://download.geonames.org/export/dump/allCountries.zip
unzip -p allCountries.zip allCountries.txt \
  | awk -F'\t' '$8=="ADM1"||$8=="ADM2"||$8=="ADM3"{print $9"\t"$8"\t"$11"\t"$12"\t"$13"\t"$2"\t"$3"\t"$1}' > adm.tsv
python3 build_geonames.py       # -> level1/2/3.json + index.json (keyed by country, parent codes)
python3 gen_percountry.py       # -> js/<CC>.js (228 lazy-load bundles) + manifest.js
```

**GeoNames dump schema** (tab-separated, the columns we used):
`2`=name, `3`=asciiname, `1`=geonameid, `8`=feature_code (ADM1/2/3),
`9`=country_code, `11`=admin1_code, `12`=admin2_code, `13`=admin3_code.

---

## 4. Known caveats

- **`address-examples.json` values are synthetic** (Source E), not real addresses.
- **Country names in `countries.json` are authored** (Source E), not from a live feed.
- **`subregions/` (libaddressinput) is stale test-snapshot data** and shallow; prefer
  `subregions-geonames/`.
- **GeoNames `key` values are internal admin codes**, not ISO 3166-2. Joins use the
  `level1`/`level2` code references, which are internally consistent.
- **"Level 2/3" is not uniform across countries** — it is ADM2/ADM3, which maps to
  district / county / municipality / sub-district depending on the country.
- **24 countries have no GeoNames admin data** (uninhabited or single-unit territories).
- **libaddressinput bundled data can lag the live endpoint**; for guaranteed-current
  field or sub-region data, re-pull from `chromium-i18n.appspot.com/ssl-address/data/<CC>`.
