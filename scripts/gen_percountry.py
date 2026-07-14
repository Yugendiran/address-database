import json, os

BASE = "/Users/yugi/Documents/Projects/address-database/subregions-geonames"
OUTJS = os.path.join(BASE, "js")
os.makedirs(OUTJS, exist_ok=True)

L1 = json.load(open(BASE + "/level1.json", encoding="utf-8"))
L2 = json.load(open(BASE + "/level2.json", encoding="utf-8"))
L3 = json.load(open(BASE + "/level3.json", encoding="utf-8"))

codes = sorted(set(L1) | set(L2) | set(L3))
for cc in codes:
    payload = {"l1": L1.get(cc, []), "l2": L2.get(cc, []), "l3": L3.get(cc, [])}
    with open(os.path.join(OUTJS, cc + ".js"), "w", encoding="utf-8") as f:
        f.write("registerSubregions(" + json.dumps(cc) + ",")
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
        f.write(");\n")

# tiny manifest of which countries have a data file + counts
manifest = {cc: {"l1": len(L1.get(cc, [])), "l2": len(L2.get(cc, [])), "l3": len(L3.get(cc, []))}
            for cc in codes}
with open(os.path.join(BASE, "manifest.js"), "w", encoding="utf-8") as f:
    f.write("window.SUBREG_MANIFEST=")
    json.dump(manifest, f, ensure_ascii=False, separators=(",", ":"))
    f.write(";\n")

print("wrote", len(codes), "per-country js files")
import subprocess
print("js dir size:", subprocess.run(["du","-sh",OUTJS],capture_output=True,text=True).stdout.strip())
