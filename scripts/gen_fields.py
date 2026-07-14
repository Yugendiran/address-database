import json, re, sys

JAVA = "/Users/yugi/Documents/Projects/libaddressinput/common/src/main/java/com/google/i18n/addressinput/common/RegionDataConstants.java"

src = open(JAVA, encoding="utf-8").read()

# Grab everything inside each map.put( ... );
blocks = re.findall(r'map\.put\((.*?)\);', src, re.DOTALL)

def java_literals(block):
    lits = re.findall(r'"((?:[^"\\]|\\.)*)"', block)
    out = []
    for l in lits:
        l = l.replace('\\"', '"').replace('\\\\', '\\')
        out.append(l)
    return out

raw = {}
for b in blocks:
    lits = java_literals(b)
    if not lits:
        continue
    code = lits[0]
    payload = "".join(lits[1:])
    raw[code] = json.loads(payload)

ZZ = raw["ZZ"]
DEFAULT_FMT = ZZ["fmt"]          # %N%n%O%n%A%n%C
DEFAULT_REQUIRE = ZZ["require"]  # AC

# token -> canonical field key + base label
TOKEN = {
    "N": ("recipient",         "Name"),
    "O": ("organization",      "Organization"),
    "A": ("streetAddress",     "Street address"),
    "D": ("dependentLocality", "Suburb"),
    "C": ("locality",          "City"),
    "S": ("administrativeArea","Province"),
    "Z": ("postalCode",        "Postal code"),
    "X": ("sortingCode",       "Sorting code"),
    "T": ("landmarkDescriptor","Landmark"),
    "F": ("landmarkAffix",     "Landmark affix"),
    "L": ("landmarkName",      "Landmark name"),
}

# name_type value -> human label
NAME_TYPE_LABEL = {
    "area": "Area", "county": "County", "department": "Department",
    "district": "District", "do_si": "Do/Si", "emirate": "Emirate",
    "island": "Island", "oblast": "Oblast", "parish": "Parish",
    "prefecture": "Prefecture", "state": "State", "province": "Province",
    "region": "Region", "state_or_province": "State/Province",
    "city": "City", "post_town": "Post town", "suburb": "Suburb",
    "townland": "Townland", "neighborhood": "Neighborhood",
    "village_township": "Village/Township",
    "postal": "Postal code", "zip": "ZIP code", "pin": "PIN code",
    "eircode": "Eircode",
}

def label_for(token, meta):
    key, base = TOKEN[token]
    nt = None
    if token == "S":
        nt = meta.get("state_name_type") or ZZ.get("state_name_type")
    elif token == "C":
        nt = meta.get("locality_name_type") or ZZ.get("locality_name_type")
    elif token == "Z":
        nt = meta.get("zip_name_type") or ZZ.get("zip_name_type")
    elif token == "D":
        nt = meta.get("sublocality_name_type") or ZZ.get("sublocality_name_type")
    if nt:
        return NAME_TYPE_LABEL.get(nt, nt.replace("_", " ").title())
    return base

names = {c["code"]: c["name"]
         for c in json.load(open("/Users/yugi/Documents/Projects/address-database/countries.json"))["countries"]}

result = []
for code in sorted(k for k in raw if k != "ZZ"):
    meta = raw[code]
    fmt = meta.get("fmt", DEFAULT_FMT)
    require = meta.get("require", DEFAULT_REQUIRE)
    upper = meta.get("upper", "")

    seen, order = set(), []
    for tok in re.findall(r"%(.)", fmt):
        if tok == "n":
            continue
        if tok in TOKEN and tok not in seen:
            seen.add(tok)
            order.append(tok)

    fields = []
    for tok in order:
        key, _ = TOKEN[tok]
        fields.append({
            "key": key,
            "label": label_for(tok, meta),
            "token": "%" + tok,
            "required": tok in require,
            "uppercase": tok in upper,
        })

    result.append({
        "code": code,
        "name": names.get(code, meta.get("name", "").title()),
        "languages": meta.get("languages"),
        "format": fmt,
        "requiredKeys": [TOKEN[t][0] for t in require if t in TOKEN],
        "fields": fields,
    })

out = {
    "source": "google/libaddressinput RegionDataConstants.java",
    "note": "Fields each country collects in a postal address, in display order. Tokens: %N name, %O org, %A street, %D dependent locality, %C locality, %S admin area, %Z postal code, %X sorting code, %T/%F/%L landmark.",
    "count": len(result),
    "countries": result,
}
json.dump(out, open("/Users/yugi/Documents/Projects/address-database/address-fields.json", "w", encoding="utf-8"),
          indent=2, ensure_ascii=False)
print("wrote", len(result), "countries")
