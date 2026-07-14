import json

ROOT = "/Users/yugi/Documents/Projects/address-database/"
fields = json.load(open(ROOT + "address-fields.json"))
manifest = json.loads(open(ROOT + "subregions-geonames/manifest.js", encoding="utf-8")
                      .read().split("=", 1)[1].rstrip(";\n"))
levels = json.load(open(ROOT + "admin-levels.json"))["levels"]

# The 3 geographic schema fields that CAN be dropdowns, and the cascade order.
GEO = ["administrativeArea", "locality", "dependentLocality"]

# Per-country tuning:
#   locality  -> level2  only where ADM2 IS a city/municipality (not a county/district)
#   dependentLocality -> level3 only where ADM3 fits a sub-locality
LOCALITY_LEVEL2 = {"BR", "MX", "ID", "PH", "CN", "KR"}   # ADM2 == município / kota / prefecture-city / si-gun
DEPLOC_LEVEL3   = {"CN"}                                  # ADM3 == district (China %D)

def counts(cc):
    return manifest.get(cc, {"l1": 0, "l2": 0, "l3": 0})

mapping = {}
summary = {"select_admin": 0, "select_locality": 0, "select_deploc": 0}

for c in fields["countries"]:
    cc = c["code"]
    collected = {f["key"] for f in c["fields"]}
    lname = levels.get(cc, {})
    cnt = counts(cc)
    entry = {}

    # administrativeArea <- level1  (Strategy: show a state dropdown wherever level1 data
    # exists, even if the postal format omits the state field -> "added": true)
    if cnt["l1"] > 0:
        entry["administrativeArea"] = {"control": "select", "source": "level1",
                                       "levelName": lname.get("l1", "Administrative area"),
                                       "added": "administrativeArea" not in collected}
        summary["select_admin"] += 1
    elif "administrativeArea" in collected:
        entry["administrativeArea"] = {"control": "input", "levelName": lname.get("l1", "Administrative area")}

    admin_is_select = entry.get("administrativeArea", {}).get("control") == "select"

    def fmt_label(key):
        f = next((x for x in c["fields"] if x["key"] == key), None)
        return f["label"] if f else key

    # locality <- level2  (reuse the slot: fill wherever level2 data exists; needs the
    # parent (administrativeArea) to be a select so the cascade can filter). Label = the
    # country's REAL level-2 admin name (District / Prefecture / Municipality…).
    if cnt["l2"] > 0 and admin_is_select:
        entry["locality"] = {"control": "select", "source": "level2",
                             "levelName": lname.get("l2", "District"),
                             "added": "locality" not in collected,
                             "slotLabel": fmt_label("locality") if "locality" in collected else None}
        summary["select_locality"] += 1
    elif "locality" in collected:
        entry["locality"] = {"control": "input", "levelName": fmt_label("locality")}

    loc_is_select = entry.get("locality", {}).get("control") == "select"

    # dependentLocality <- level3  (needs the locality select as cascade parent)
    if cnt["l3"] > 0 and loc_is_select:
        entry["dependentLocality"] = {"control": "select", "source": "level3",
                                      "levelName": lname.get("l3", "Sub-district"),
                                      "added": "dependentLocality" not in collected,
                                      "slotLabel": fmt_label("dependentLocality") if "dependentLocality" in collected else None}
        summary["select_deploc"] += 1
    elif "dependentLocality" in collected:
        entry["dependentLocality"] = {"control": "input", "levelName": fmt_label("dependentLocality")}

    mapping[cc] = entry

payload = {
    "$comment": "Per-country field mapping: which fieldReference geographic field renders as a <select> and which GeoNames sub-region level feeds it. control=select|input; source=level1|2|3 (only when select). Dropdowns store the chosen region NAME into the schema field. Only fields the country's format collects appear.",
    "storesValue": "name",
    "mapping": mapping,
}
json.dump(payload, open(ROOT + "field-mapping.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
with open(ROOT + "field-mapping.js", "w", encoding="utf-8") as f:
    f.write("window.FIELD_MAPPING=")
    json.dump(mapping, f, ensure_ascii=False, separators=(",", ":"))
    f.write(";\n")

print("countries mapped:", len(mapping))
print("selects -> administrativeArea:%d  locality:%d  dependentLocality:%d" %
      (summary["select_admin"], summary["select_locality"], summary["select_deploc"]))
print()
for cc in ["US", "IN", "JP", "CN", "BR", "MX", "ID", "GB", "DE", "AE", "AO"]:
    m = mapping.get(cc, {})
    parts = []
    for k in GEO:
        if k in m:
            v = m[k]
            parts.append("%s=%s%s" % (k, v["control"], "(" + v["source"] + ")" if v.get("source") else ""))
    print("%-4s %s" % (cc, "  ".join(parts) if parts else "(no geographic fields)"))
