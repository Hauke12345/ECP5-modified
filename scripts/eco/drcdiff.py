import json, sys
from collections import Counter
base = json.load(open("/home/claude/route/k9/drc_orig.json")); d = json.load(open(sys.argv[1]))
key = lambda v: (v["type"], tuple(sorted(i["description"].split(" on ")[0] for i in v["items"])))
bk = {key(v) for v in base["violations"] if v["severity"] == "error"}
new = []; seen = set()
for v in d["violations"]:
    if v["severity"] != "error": continue
    k = key(v)
    if k not in bk and k not in seen: new.append(v); seen.add(k)
print("errors total", sum(1 for v in d["violations"] if v["severity"] == "error"), "| new vs original:", dict(Counter(v["type"] for v in new)))
for v in new[:15]: print("  ", v["type"], "|", v["description"][:75], "|", " || ".join(i["description"][:60] for i in v["items"]))
print("unconnected", len(d["unconnected_items"]))
