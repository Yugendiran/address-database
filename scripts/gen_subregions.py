import json, os, re

SRC = "/Users/yugi/Documents/Projects/libaddressinput/testdata/countryinfo.txt"
OUT = "/Users/yugi/Documents/Projects/address-database/subregions"

def field(rec, *keys):
    for k in keys:
        if rec.get(k): return rec[k]
    return None

# parse into buckets by level, keyed by country
levels = {1: {}, 2: {}, 3: {}}   # level -> { CC: [entries] }
countries = set()

with open(SRC, encoding="utf-8") as f:
    for line in f:
        line = line.rstrip("\n")
        if not line.startswith("data/"):
            continue
        path, _, payload = line.partition("=")
        try:
            rec = json.loads(payload)
        except json.JSONDecodeError:
            continue
        seg = path.split("/")        # e.g. ['data','CN','上海市','宝山区']
        depth = len(seg) - 1         # 1=country, 2=level1, 3=level2, 4=level3
        cc = seg[1]
        if depth < 2:
            continue                 # country line itself -> skip (fields already elsewhere)
        countries.add(cc)
        lvl = depth - 1              # level1/2/3

        entry = {"key": seg[-1]}
        name = field(rec, "name")
        lname = field(rec, "lname")   # latin/English name when local script differs
        if name:  entry["name"] = name
        if lname: entry["lname"] = lname
        for k in ("isoid", "zip", "zipex", "lang"):
            v = field(rec, k)
            if v: entry[k] = v

        # parent chain (level keys above this one, excluding 'data' and country)
        parents = seg[2:-1]
        if lvl == 2: entry["level1"] = parents[0]                       # its province/state
        if lvl == 3: entry["level1"] = parents[0]; entry["level2"] = parents[1]  # province, then city

        levels[lvl].setdefault(cc, []).append(entry)

# ---- write one JSON file per level, keyed by country ----
os.makedirs(OUT, exist_ok=True)
index = {}
for lvl in (1, 2, 3):
    by_country = {cc: entries for cc, entries in sorted(levels[lvl].items())}
    with open(os.path.join(OUT, f"level{lvl}.json"), "w", encoding="utf-8") as f:
        json.dump(by_country, f, ensure_ascii=False, indent=2)
    for cc, entries in by_country.items():
        index.setdefault(cc, {"level1": 0, "level2": 0, "level3": 0})[f"level{lvl}"] = len(entries)

with open(os.path.join(OUT, "index.json"), "w", encoding="utf-8") as f:
    json.dump({
        "$comment": "Sub-region hierarchy for countries that have it, extracted from libaddressinput testdata/countryinfo.txt. Country > level1 > level2 > level3. Each level is a folder; files are per-country (ISO code). level2/level3 entries carry parent keys.",
        "countries": len(index),
        "counts": dict(sorted(index.items())),
    }, f, ensure_ascii=False, indent=2)

print("countries with sub-regions:", len(countries))
tot = {lvl: sum(len(v) for v in levels[lvl].values()) for lvl in (1,2,3)}
print("total entries: level1=%d level2=%d level3=%d" % (tot[1], tot[2], tot[3]))
print("level2 countries:", sorted(levels[2]))
print("level3 countries:", sorted(levels[3]))
