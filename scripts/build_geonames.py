import json, os, collections

SRC = "/private/tmp/claude-502/-Users-yugi-Documents-Projects-address-database/06d5b2ad-6ed7-4680-8762-be0e7950bb0d/scratchpad/adm.tsv"
OUT = "/Users/yugi/Documents/Projects/address-database/subregions-geonames"
os.makedirs(OUT, exist_ok=True)

L = {1: collections.defaultdict(list), 2: collections.defaultdict(list), 3: collections.defaultdict(list)}

with open(SRC, encoding="utf-8") as f:
    for line in f:
        p = line.rstrip("\n").split("\t")
        if len(p) < 8:
            continue
        cc, feat, a1, a2, a3, name, aname, gid = p
        if feat == "ADM1":
            lvl, key = 1, a1
        elif feat == "ADM2":
            lvl, key = 2, a2
        elif feat == "ADM3":
            lvl, key = 3, a3
        else:
            continue
        e = {"key": key, "name": name, "geonameid": int(gid)}
        if aname and aname != name:
            e["lname"] = aname
        if lvl >= 2:
            e["level1"] = a1
        if lvl == 3:
            e["level2"] = a2
        L[lvl][cc].append(e)

index = {}
for lvl in (1, 2, 3):
    data = {cc: L[lvl][cc] for cc in sorted(L[lvl])}
    with open(os.path.join(OUT, f"level{lvl}.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    for cc, rows in data.items():
        index.setdefault(cc, {"level1": 0, "level2": 0, "level3": 0})[f"level{lvl}"] = len(rows)

with open(os.path.join(OUT, "index.json"), "w", encoding="utf-8") as f:
    json.dump({
        "$comment": "Administrative hierarchy from GeoNames (CC-BY 4.0). country > level1 (ADM1, state/province) > level2 (ADM2, district/county) > level3 (ADM3, sub-district). key = GeoNames admin code; parents given as level1/level2 codes. name = local, lname = Latin (when different).",
        "source": "https://download.geonames.org/export/dump/allCountries.zip",
        "countries": len(index),
        "counts": dict(sorted(index.items())),
    }, f, ensure_ascii=False, indent=1)

print("countries:", len(index))
tot = {lvl: sum(len(v) for v in L[lvl].values()) for lvl in (1, 2, 3)}
print("totals L1=%d L2=%d L3=%d" % (tot[1], tot[2], tot[3]))

# coverage check for the 39 libaddressinput countries
Q39 = "AD AM AR AU BR BS CA CH CL CN CV EG ES HK ID IE IN IT JM JP KN KR KY MX MY NG NI NR PH SO SR SV TH TV TW US UY VE VN".split()
missing = [c for c in Q39 if c not in index]
print("of the 39 -> present:", len([c for c in Q39 if c in index]), "| missing:", missing)
