import json

SRC = "/Users/yugi/Documents/Projects/libaddressinput/testdata/countryinfo.txt"
ROOT = "/Users/yugi/Documents/Projects/address-database/"

patterns = {}
with open(SRC, encoding="utf-8") as f:
    for line in f:
        if not line.startswith("data/"):
            continue
        path, _, payload = line.partition("=")
        seg = path.split("/")
        if len(seg) != 2:          # country-level line only: data/CC
            continue
        try:
            rec = json.loads(payload)
        except json.JSONDecodeError:
            continue
        cc = seg[1]
        entry = {}
        if rec.get("zip"):
            entry["zip"] = rec["zip"]        # postal-code regex (unanchored)
        if rec.get("zipex"):
            entry["zipex"] = rec["zipex"]    # comma-separated example postcodes
        if entry:
            patterns[cc] = entry

with open(ROOT + "postal-patterns.js", "w", encoding="utf-8") as f:
    f.write("window.POSTAL_PATTERNS=")
    json.dump(patterns, f, ensure_ascii=False, separators=(",", ":"))
    f.write(";\n")
json.dump({"$comment": "Per-country postal-code validation from libaddressinput countryinfo.txt. zip = unanchored regex; zipex = example postcodes.",
           "count": len(patterns), "patterns": patterns},
          open(ROOT + "postal-patterns.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("wrote postal patterns for", len(patterns), "countries")
print("sample US:", patterns.get("US"), "| IN:", patterns.get("IN"), "| GB:", patterns.get("GB"))
