import json

ROOT = "/Users/yugi/Documents/Projects/address-database/"
fields = json.load(open(ROOT + "address-fields.json"))
idx = json.load(open(ROOT + "subregions-geonames/index.json"))["counts"]

# Level-1 label from libaddressinput (the administrativeArea field label), when the
# country's postal format actually collects a state/province field.
l1_from_format = {}
for c in fields["countries"]:
    f = next((x for x in c["fields"] if x["key"] == "administrativeArea"), None)
    if f:
        l1_from_format[c["code"]] = f["label"]

# Curated real administrative terms for ADM1 / ADM2 / ADM3 (GeoNames levels).
# l1 here overrides/fills where the postal format has no state field (DE, FR, GB…).
CURATED = {
    "US": {"l1": "State", "l2": "County", "l3": "County subdivision"},
    "CA": {"l1": "Province / Territory", "l2": "Census division", "l3": "Municipality"},
    "GB": {"l1": "Nation", "l2": "County / Council area", "l3": "District"},
    "IE": {"l1": "Province", "l2": "County", "l3": "Electoral division"},
    "IN": {"l1": "State", "l2": "District", "l3": "Sub-district (Taluk)"},
    "JP": {"l1": "Prefecture", "l2": "Municipality", "l3": "Ward / Town"},
    "CN": {"l1": "Province", "l2": "Prefecture", "l3": "County / District"},
    "KR": {"l1": "Province", "l2": "Municipality", "l3": "District (Gu)"},
    "ID": {"l1": "Province", "l2": "Regency / City", "l3": "District (Kecamatan)"},
    "TH": {"l1": "Province", "l2": "District (Amphoe)", "l3": "Subdistrict (Tambon)"},
    "VN": {"l1": "Province", "l2": "District", "l3": "Commune"},
    "PH": {"l1": "Province", "l2": "Municipality / City", "l3": "Barangay"},
    "MY": {"l1": "State", "l2": "District", "l3": "Mukim"},
    "DE": {"l1": "State (Land)", "l2": "District (Kreis)", "l3": "Municipality (Gemeinde)"},
    "FR": {"l1": "Region", "l2": "Department", "l3": "Arrondissement / Commune"},
    "IT": {"l1": "Region", "l2": "Province", "l3": "Comune"},
    "ES": {"l1": "Autonomous community", "l2": "Province", "l3": "Comarca / Municipality"},
    "PT": {"l1": "District", "l2": "Municipality", "l3": "Parish (Freguesia)"},
    "NL": {"l1": "Province", "l2": "Municipality", "l3": "Locality"},
    "BE": {"l1": "Region", "l2": "Province", "l3": "Municipality"},
    "CH": {"l1": "Canton", "l2": "District", "l3": "Municipality"},
    "AT": {"l1": "State (Land)", "l2": "District (Bezirk)", "l3": "Municipality"},
    "PL": {"l1": "Voivodeship", "l2": "County (Powiat)", "l3": "Commune (Gmina)"},
    "RU": {"l1": "Federal subject", "l2": "District (Raion)", "l3": "Settlement"},
    "UA": {"l1": "Oblast", "l2": "Raion", "l3": "Hromada"},
    "TR": {"l1": "Province (Il)", "l2": "District (Ilce)", "l3": "Locality"},
    "GR": {"l1": "Region", "l2": "Regional unit", "l3": "Municipality"},
    "SE": {"l1": "County (Lan)", "l2": "Municipality", "l3": "District"},
    "NO": {"l1": "County (Fylke)", "l2": "Municipality", "l3": "District"},
    "FI": {"l1": "Region", "l2": "Sub-region", "l3": "Municipality"},
    "DK": {"l1": "Region", "l2": "Municipality", "l3": "Parish"},
    "BR": {"l1": "State", "l2": "Municipality", "l3": "District"},
    "MX": {"l1": "State", "l2": "Municipality", "l3": "Locality"},
    "AR": {"l1": "Province", "l2": "Department", "l3": "Municipality"},
    "CL": {"l1": "Region", "l2": "Province", "l3": "Commune"},
    "CO": {"l1": "Department", "l2": "Municipality", "l3": "Locality"},
    "PE": {"l1": "Region", "l2": "Province", "l3": "District"},
    "AU": {"l1": "State / Territory", "l2": "Local government area", "l3": "Locality"},
    "NZ": {"l1": "Region", "l2": "District", "l3": "Locality"},
    "ZA": {"l1": "Province", "l2": "District municipality", "l3": "Local municipality"},
    "NG": {"l1": "State", "l2": "Local government area", "l3": "Ward"},
    "EG": {"l1": "Governorate", "l2": "Region", "l3": "District"},
    "SA": {"l1": "Region", "l2": "Governorate", "l3": "District"},
    "AE": {"l1": "Emirate", "l2": "Region", "l3": "District"},
    "IL": {"l1": "District", "l2": "Sub-district", "l3": "Locality"},
    "MA": {"l1": "Region", "l2": "Province / Prefecture", "l3": "Municipality"},
    "KE": {"l1": "County", "l2": "Sub-county", "l3": "Ward"},
    "PK": {"l1": "Province", "l2": "Division", "l3": "District"},
    "BD": {"l1": "Division", "l2": "District", "l3": "Upazila"},
    "TW": {"l1": "County / City", "l2": "Township / District", "l3": "Village"},
    "HK": {"l1": "Region", "l2": "District", "l3": "Area"},
}

DEFAULT = {"l1": "Administrative area", "l2": "District", "l3": "Sub-district"}

out = {}
for cc in sorted(set(idx) | set(l1_from_format)):
    cur = CURATED.get(cc, {})
    l1 = cur.get("l1") or l1_from_format.get(cc) or DEFAULT["l1"]
    l2 = cur.get("l2") or DEFAULT["l2"]
    l3 = cur.get("l3") or DEFAULT["l3"]
    out[cc] = {"l1": l1, "l2": l2, "l3": l3, "curated": cc in CURATED}

payload = {
    "$comment": "What ADM level 1/2/3 mean per country. l1 = libaddressinput state_name_type or curated; l2/l3 = curated real administrative terms, else generic District/Sub-district. `curated`=true means human-verified names; false means generic fallback.",
    "levels": out,
}
json.dump(payload, open(ROOT + "admin-levels.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
with open(ROOT + "admin-levels.js", "w", encoding="utf-8") as f:
    f.write("window.ADMIN_LEVELS=")
    json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    f.write(";\n")
print("wrote admin-levels for", len(out), "countries;", sum(1 for v in out.values() if v["curated"]), "curated")
