import json

ROOT = "/Users/yugi/Documents/Projects/address-database/"
data = json.load(open(ROOT + "address-fields.json", encoding="utf-8"))
mapping = json.load(open(ROOT + "field-mapping.json", encoding="utf-8"))["mapping"]

TO_SCHEMA = {
    "recipient": "recipient", "organization": "organization",
    "streetAddress": "addressLines", "dependentLocality": "dependentLocality",
    "locality": "locality", "administrativeArea": "administrativeArea",
    "postalCode": "postalCode", "sortingCode": "sortingCode",
    "landmarkDescriptor": "landmark", "landmarkAffix": "landmark", "landmarkName": "landmark",
}
GEO = ["administrativeArea", "locality", "dependentLocality"]     # schema keys
GEO_TOKEN = {"administrativeArea": "%S", "locality": "%C", "dependentLocality": "%D"}
LEVEL = {"level1": 1, "level2": 2, "level3": 3}

def field_obj(key, label, token, ftype, required, upper, source=None, added=False):
    o = {"key": key, "label": label, "token": token, "fieldType": ftype,
         "required": required, "uppercase": upper}
    if source:
        o["source"] = source
    if added:
        o["added"] = True
    return o

n_added = 0
for c in data["countries"]:
    cc = c["code"]
    cmap = mapping.get(cc, {})

    # rebuild existing fields with fieldType (+ source on geographic selects).
    # Dedup by schema slot so there is ONE field per fieldReference slot
    # (collapses the 3 landmark tokens %T/%F/%L into a single `landmark` field).
    present_schema = set()
    new_fields = []
    for f in c["fields"]:
        schemaKey = TO_SCHEMA.get(f["key"])
        if schemaKey in present_schema:
            continue
        present_schema.add(schemaKey)
        m = cmap.get(schemaKey) if schemaKey else None
        ftype = "select" if (m and m.get("control") == "select") else "text"
        source = m.get("source") if (m and ftype == "select") else None
        new_fields.append(field_obj(f["key"], f["label"], f["token"], ftype,
                                     f["required"], f["uppercase"], source))

    # inject geographic dropdown slots the format doesn't collect but data supports
    insert_at = next((i for i, f in enumerate(new_fields)
                      if TO_SCHEMA.get(f["key"]) == "postalCode"), len(new_fields))
    for slot in GEO:
        m = cmap.get(slot)
        if not m or m.get("control") != "select" or slot in present_schema:
            continue
        # only injected (added) ones reach here
        label = m.get("levelName") or slot
        new_fields.insert(insert_at, field_obj(slot, label, GEO_TOKEN[slot], "select",
                                                False, False, source=m.get("source"), added=True))
        insert_at += 1
        n_added += 1

    c["fields"] = new_fields

data["note"] = (data.get("note", "").split(" fieldType:")[0] +
                " fieldType: text|select per field. Geographic selects carry `source` (level1/2/3). "
                "`added:true` = dropdown injected from sub-region data, not in the country's postal format.")

json.dump(data, open(ROOT + "address-fields.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
with open(ROOT + "data.js", "w", encoding="utf-8") as f:
    f.write("window.ADDRESS_DATA = ")
    json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    f.write(";\n")

print("injected", n_added, "added dropdown fields across", len(data["countries"]), "countries")
