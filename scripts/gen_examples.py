import json

ROOT = "/Users/yugi/Documents/Projects/address-database/"
meta = json.load(open(ROOT + "address-fields.json"))

# metadata field.key -> storage template key
META_TO_STORE = {
    "recipient": "recipient",
    "organization": "organization",
    "streetAddress": "addressLines",
    "dependentLocality": "dependentLocality",
    "locality": "locality",
    "administrativeArea": "administrativeArea",
    "postalCode": "postalCode",
    "sortingCode": "sortingCode",
    "landmarkDescriptor": "landmark",
    "landmarkAffix": None,
    "landmarkName": None,
}

DEFAULTS = {
    "recipient": "Alex Morgan",
    "organization": "Globex Trading Co.",
    "addressLines": ["221 Example Avenue", "Building 4"],
    "dependentLocality": "Riverside",
    "locality": "Springfield",
    "administrativeArea": "Central",
    "postalCode": "12345",
    "sortingCode": "CEDEX 7",
    "landmark": "Near Central Park",
}

CURATED = {
    "US": {"recipient":"Alex Morgan","organization":"Globex Corp","addressLines":["1600 Amphitheatre Parkway"],"locality":"Mountain View","administrativeArea":"CA","postalCode":"94043"},
    "GB": {"recipient":"Alex Morgan","organization":"Globex Ltd","addressLines":["221B Baker Street"],"locality":"London","postalCode":"NW1 6XE"},
    "CA": {"recipient":"Alex Morgan","organization":"Globex Inc","addressLines":["100 Queen Street West"],"locality":"Toronto","administrativeArea":"ON","postalCode":"M5H 2N2"},
    "AU": {"recipient":"Alex Morgan","organization":"Globex Pty Ltd","addressLines":["1 Macquarie Street"],"locality":"Sydney","administrativeArea":"NSW","postalCode":"2000"},
    "IN": {"recipient":"Alex Morgan","organization":"Globex Pvt Ltd","addressLines":["42 MG Road","Tower B, Flat 7"],"dependentLocality":"Indiranagar","locality":"Bengaluru","administrativeArea":"KA","postalCode":"560038","landmark":"Near City Mall"},
    "JP": {"recipient":"山田 太郎","organization":"グローベックス株式会社","addressLines":["六本木6-10-1"],"locality":"港区","administrativeArea":"東京都","postalCode":"106-6108"},
    "DE": {"recipient":"Alex Morgan","organization":"Globex GmbH","addressLines":["Friedrichstraße 123"],"locality":"Berlin","postalCode":"10117"},
    "FR": {"recipient":"Alex Morgan","organization":"Globex SARL","addressLines":["12 Rue de Rivoli"],"locality":"Paris","postalCode":"75001"},
    "CN": {"recipient":"张 伟","organization":"环球贸易有限公司","addressLines":["建国路88号"],"dependentLocality":"朝阳区","locality":"北京市","administrativeArea":"北京市","postalCode":"100022"},
    "BR": {"recipient":"Alex Morgan","organization":"Globex Ltda","addressLines":["Avenida Paulista 1578"],"dependentLocality":"Bela Vista","locality":"São Paulo","administrativeArea":"SP","postalCode":"01310-200"},
    "AE": {"recipient":"Alex Morgan","organization":"Globex FZE","addressLines":["Sheikh Zayed Road, Villa 12"],"administrativeArea":"Dubai"},
    "IT": {"recipient":"Alex Morgan","organization":"Globex S.r.l.","addressLines":["Via del Corso 100"],"locality":"Roma","administrativeArea":"RM","postalCode":"00186"},
    "ES": {"recipient":"Alex Morgan","organization":"Globex S.L.","addressLines":["Gran Vía 28"],"locality":"Madrid","administrativeArea":"Madrid","postalCode":"28013"},
    "NL": {"recipient":"Alex Morgan","organization":"Globex B.V.","addressLines":["Damrak 70"],"locality":"Amsterdam","postalCode":"1012 LM"},
    "SG": {"recipient":"Alex Morgan","organization":"Globex Pte Ltd","addressLines":["1 Raffles Place","#20-01"],"locality":"Singapore","postalCode":"048616"},
    "MX": {"recipient":"Alex Morgan","organization":"Globex S.A. de C.V.","addressLines":["Paseo de la Reforma 250"],"dependentLocality":"Juárez","locality":"Ciudad de México","administrativeArea":"CDMX","postalCode":"06600"},
    "RU": {"recipient":"Иван Иванов","organization":"ООО Глобэкс","addressLines":["ул. Тверская, д. 7"],"locality":"Москва","postalCode":"125009"},
    "KR": {"recipient":"홍 길동","organization":"글로벡스 주식회사","addressLines":["세종대로 110"],"locality":"중구","administrativeArea":"서울특별시","postalCode":"04524"},
}

FMT_TOKEN_STORE = {
    "N": lambda a: a.get("recipient",""),
    "O": lambda a: a.get("organization",""),
    "A": lambda a: "\n".join(a.get("addressLines",[]) or []),
    "D": lambda a: a.get("dependentLocality",""),
    "C": lambda a: a.get("locality",""),
    "S": lambda a: a.get("administrativeArea",""),
    "Z": lambda a: a.get("postalCode",""),
    "X": lambda a: a.get("sortingCode",""),
    "T": lambda a: a.get("landmark",""),
    "F": lambda a: "",
    "L": lambda a: "",
}

def format_address(rec, country):
    upper = {f["token"].replace("%",""): f["uppercase"] for f in country["fields"]}
    out_lines = []
    for line in country["format"].split("%n"):
        s, filled, i = "", False, 0
        while i < len(line):
            if line[i] == "%":
                t = line[i+1]; i += 2
                get = FMT_TOKEN_STORE.get(t)
                if get is not None:
                    v = get(rec) or ""
                    if v and upper.get(t): v = v.upper()
                    if v: filled = True
                    s += v
                else:
                    s += t
            else:
                s += line[i]; i += 1
        if filled:
            out_lines.append(" ".join(s.split()))
    return "\n".join(out_lines)

examples = []
for c in meta["countries"]:
    code = c["code"]
    src = {**DEFAULTS, **CURATED.get(code, {})}
    rec = {
        "regionCode": code,
        "languageCode": (c.get("languages") or "").split("~")[0],
        "recipient": "", "organization": "", "addressLines": [],
        "dependentLocality": "", "locality": "", "administrativeArea": "",
        "postalCode": "", "sortingCode": "", "landmark": "", "formatted": "",
    }
    for f in c["fields"]:
        store_key = META_TO_STORE.get(f["key"])
        if not store_key:
            continue
        val = src.get(store_key)
        if store_key == "addressLines":
            rec["addressLines"] = list(val) if val else []
        elif rec[store_key] == "":
            rec[store_key] = val if val is not None else ""
    rec["formatted"] = format_address(rec, c)
    examples.append(rec)

out = {
    "$comment": "One example address per country, in the address-schema.json template shape. Only collected fields filled. Curated realistic values for ~18 major countries; synthetic placeholders elsewhere. `formatted` derived from each country's fmt.",
    "count": len(examples),
    "addresses": examples,
}
json.dump(out, open(ROOT + "address-examples.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
with open(ROOT + "examples.js", "w", encoding="utf-8") as f:
    f.write("window.ADDRESS_EXAMPLES = ")
    json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    f.write(";\n")
print("wrote", len(examples), "examples")
