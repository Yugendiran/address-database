import json

ROOT = "/Users/yugi/Documents/Projects/address-database/"
data = json.load(open(ROOT + "address-fields.json", encoding="utf-8"))
mapping = json.load(open(ROOT + "field-mapping.json", encoding="utf-8"))["mapping"]

# metadata field.key -> schema (fieldReference) key used by the mapping
TO_SCHEMA = {
    "recipient": "recipient", "organization": "organization",
    "streetAddress": "addressLines", "dependentLocality": "dependentLocality",
    "locality": "locality", "administrativeArea": "administrativeArea",
    "postalCode": "postalCode", "sortingCode": "sortingCode",
    "landmarkDescriptor": "landmark", "landmarkAffix": "landmark", "landmarkName": "landmark",
}

n_select = 0
for c in data["countries"]:
    cc = c["code"]
    cmap = mapping.get(cc, {})
    new_fields = []
    for f in c["fields"]:
        schemaKey = TO_SCHEMA.get(f["key"])
        m = cmap.get(schemaKey) if schemaKey else None
        field_type = "select" if (m and m.get("control") == "select") else "text"
        if field_type == "select":
            n_select += 1
        # rebuild in a stable key order with fieldType after token
        nf = {"key": f["key"], "label": f["label"], "token": f["token"],
              "fieldType": field_type, "required": f["required"], "uppercase": f["uppercase"]}
        new_fields.append(nf)
    c["fields"] = new_fields

json.dump(data, open(ROOT + "address-fields.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
# refresh the browser copy too
with open(ROOT + "data.js", "w", encoding="utf-8") as f:
    f.write("window.ADDRESS_DATA = ")
    json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    f.write(";\n")

print("annotated", len(data["countries"]), "countries;", n_select, "fields set to fieldType=select")
