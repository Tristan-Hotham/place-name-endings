"""Step 7: fill code/paper_template.tex from data/results.json and compile with xelatex.
Writes release/paper/ (tex and figures) and release/Hotham_Place_Name_Elements.pdf. Run: python3 code/07_paper.py
"""
import json, os, re, shutil, subprocess
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RP = os.path.join(ROOT, "data", "results.json"); R = json.load(open(RP))
size = {r[0]: r for r in R["size"]["rows"]}
R["page"].update(aber_town=size["aber"][3], inver_town=size["inver"][3], bury_town=size["bury"][3])
json.dump(R, open(RP, "w"), indent=1, ensure_ascii=False)
OUT = os.path.join(ROOT, "release", "paper"); os.makedirs(OUT, exist_ok=True)
NAME = "Hotham_Place_Name_Elements"
def tex(s): return str(s).replace("&", r"\&").replace("%", r"\%").replace("_", r"\_").replace("#", r"\#")
def get(path):
    cur = R
    for k in path.split("."):
        cur = cur[int(k)] if isinstance(cur, list) else cur[k]
    return cur
def sub(m):
    path, _, fm = m.group(1).partition("|"); v = get(path.strip())
    if fm == "int": return f"{round(v):,}"
    if fm == "pct": return f"{round(v * 100)}\\%"
    if fm == "pct1": return f"{v * 100:.1f}\\%"
    if fm == "len": return str(len(v))
    return tex(v)
E_ = R["elements"]
nat = ["England", "Wales", "Scotland", "Northern Ireland", "Republic of Ireland"]
rows = [r"\begin{table}[H]\centering\small", r"\caption{The five commonest elements among settlements in each nation, and among Irish townlands (counts).}\label{tab:top}",
        r"\begin{tabular}{rllllll}", r"\toprule", r" & England & Wales & Scotland & N. Ireland & Republic & Townlands \\", r"\midrule"]
tl = R["top_townlands"]
for i in range(5):
    cells = []
    for n in nat:
        k, c = R["top_by_nation"][n][i]; cells.append(f"{tex(E_[k]['label'].split(' / ')[0])} {c:,}")
    k, c = tl[i]; cells.append(f"{tex(E_[k]['label'].split(' / ')[0])} {c:,}")
    rows.append(f"{i + 1} & " + " & ".join(cells) + r" \\")
rows += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
tab_top = "\n".join(rows)
rows = [r"\begin{table}[H]\centering\small", r"\caption{Anglicised beginnings and the first word of the official Irish form, Republic of Ireland. Matching: share beginning with the expected Irish word. Others: the commonest other first words.}\label{tab:irish}",
        r"\begin{tabular}{llrrp{5.6cm}}", r"\toprule", r"Element & Expected & Names & Matching & Others \\", r"\midrule"]
for k, v in sorted(R["irish_forms"]["rows"].items(), key=lambda kv: kv[1]["agree_share"]):
    oth = ", ".join(f"{tex(w)} {c}" for w, c in v["others"][:3])
    rows.append(f"{tex(v['label'])} & {tex(v['word'])} & {v['n']:,} & {round(v['agree_share'] * 100)}\\% & {oth} \\\\")
rows += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
tab_irish = "\n".join(rows)
t = open(os.path.join(ROOT, "code", "paper_template.tex")).read()
t = t.replace("{{tab_top}}", tab_top).replace("{{tab_irish}}", tab_irish)
t = re.sub(r"\{\{([^}]+)\}\}", sub, t)
assert "{{" not in t
open(os.path.join(OUT, NAME + ".tex"), "w").write(t)
for f in ["b_families.png", "b_map.png", "b_border.png", "b_cornwall.png", "b_irish.png", "b_kil_map.png"]:
    shutil.copy(os.path.join(ROOT, "release", "blog", f), os.path.join(OUT, f))
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
if r.returncode: print(r.stdout[-3000:])
shutil.copy(os.path.join(OUT, NAME + ".pdf"), os.path.join(ROOT, "release", NAME + ".pdf"))
for ext in [".aux", ".log", ".out", ".pdf"]:
    p = os.path.join(OUT, NAME + ext)
    if os.path.exists(p): os.remove(p)
print("ok")
