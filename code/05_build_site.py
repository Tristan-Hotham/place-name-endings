"""Step 5: fill code/page_template.html with numbers from data/results.json to make index.html.

A few page-level numbers derived from results.json are stored under "page" first, so that
results.json holds every number on the page. Run: python3 code/05_build_site.py
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import elements as E
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RP = os.path.join(ROOT, "data", "results.json")
R = json.load(open(RP))
size = {r[0]: r for r in R["size"]["rows"]}
cty = {r[0]: r for r in R["ireland"]["counties"]}
norse = {r[0]: r for r in R["norse"]["top_areas"]}
IF = R["irish_forms"]
R.setdefault("page", {}).update(
    chester_town=size["chester"][3], tre_hamlet=size["tre"][4], cot_hamlet=size["cot"][4],
    kil_coill_share=IF["kil"]["coill"] / IF["kil"]["n"], kil_cill_share=IF["kil"]["cill"] / IF["kil"]["n"],
    bal_baile_share=IF["bal"]["baile"] / IF["bal"]["n"], ards_bal=cty["Ards and North Down"][3], wex_bal=cty["Wexford"][3],
    lincs_norse=norse["Lincolnshire"][3], thwaite_top=R["elements"]["thwaite"]["top_areas"][0][0])
json.dump(R, open(RP, "w"), indent=1, ensure_ascii=False)

def get(path):
    cur = R
    for k in path.split("."):
        cur = cur[int(k)] if isinstance(cur, list) else cur[k]
    return cur
def f(m):
    path, _, fm = m.group(1).partition("|")
    v = get(path.strip())
    if fm == "int": return f"{round(v):,}"
    if fm == "pct": return f"{round(v * 100)}%"
    if fm == "pct1": return f"{v * 100:.1f}%"
    if fm == "len": return str(len(v))
    return str(v)
t = open(os.path.join(ROOT, "code", "page_template.html")).read()
t = re.sub(r"\{\{([^}]+)\}\}", f, t)
emb = dict(fam_order=E.FAM_ORDER, fam_labels=E.FAMILIES,
           elements=[[k, v["label"], v["fam"], v["meaning"], v["n"], v["n_townlands"]] for k, v in R["elements"].items()],
           families=R["families"], size=R["size"], border=R["border"], cornwall=R["cornwall"], irish_forms=R["irish_forms"],
           ireland=dict(counties=R["ireland"]["counties"]))
t = t.replace("/*R*/", json.dumps(emb, ensure_ascii=False, separators=(",", ":")))
assert "{{" not in t
open(os.path.join(ROOT, "index.html"), "w").write(t)
print("index.html", os.path.getsize(os.path.join(ROOT, "index.html")), "thwaite top:", R["page"]["thwaite_top"])
