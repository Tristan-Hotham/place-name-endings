"""Step 8: blog post and metadata, and the Zenodo folder.
Writes release/blog/post.html and meta.json, release/zenodo/ (paper, key data files, code-and-data zip, meta.json).
Run after 07_paper.py: python3 code/08_release.py
"""
import json, os, re, shutil, zipfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
SLUG, DOI = "place-name-endings", "10.5281/zenodo.23761433"
PDF = "Hotham_Place_Name_Elements.pdf"
def get(path):
    cur = R
    for k in path.split("."):
        cur = cur[int(k)] if isinstance(cur, list) else cur[k]
    return cur
def f(m):
    path, _, fm = m.group(1).partition("|"); v = get(path.strip())
    if fm == "int": return f"{round(v):,}"
    if fm == "pct": return f"{round(v * 100)}%"
    if fm == "pct1": return f"{v * 100:.1f}%"
    return str(v)
rd = re.sub(r"\{\{([^}]+)\}\}", lambda m: (lambda path, fm: (str(len(get(path))) if fm == "len" else f(m)))(*m.group(1).partition("|")[::2]), open(os.path.join(ROOT, "code", "README_template.md")).read())
open(os.path.join(ROOT, "README.md"), "w").write(rd)
blog = os.path.join(ROOT, "release", "blog")
t = open(os.path.join(ROOT, "code", "blog_template.html")).read()
t = re.sub(r"\{\{(?!IMG\|)([^}]+)\}\}", f, t)
for img in re.findall(r"\{\{IMG\|([^|]+)\|", t): assert os.path.exists(os.path.join(blog, img)), img
open(os.path.join(blog, "post.html"), "w").write(t)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", t).split())
meta = dict(title="-ton, -by, llan- and bally-: what your town's name is made of", slug=SLUG,
            excerpt=f"I tagged {R['meta']['n_names']:,} place names in Britain and Ireland by the English, Norse, Latin, Welsh and Gaelic words inside them, and checked Irish spellings against their official Irish forms. Kil- is a wood far more often than you might think.",
            seo_description="Every town, village and Irish townland by its old words: -ton, -by, -chester, llan-, tre-, bally-, kil-. Map, search and findings.",
            tags=["place names", "toponymy", "maps", "Vikings", "Welsh", "Gaelic", "Ireland", "open data"],
            header_alt="Social card reading 'What is your town's name made of?' with coloured tiles for -ton (English), -by (Norse), -chester (Latin), llan- (Welsh) and bally- (Gaelic), beside a dot map of Britain and Ireland: red across England, blue in Lincolnshire and Yorkshire, green in Wales and Cornwall, gold across Ireland and the Scottish Highlands.")
json.dump(meta, open(os.path.join(blog, "meta.json"), "w"), indent=1, ensure_ascii=False)
print("post.html words", words)

# Zenodo
z = os.path.join(ROOT, "release", "zenodo"); os.makedirs(z, exist_ok=True)
shutil.copy(os.path.join(ROOT, "release", PDF), os.path.join(z, PDF))
for fn in ["names_tagged.csv.gz", "elements.csv", "areas.csv", "irish_forms.csv", "cells.csv", "results.json"]:
    shutil.copy(os.path.join(ROOT, "data", fn), os.path.join(z, fn))
zp = os.path.join(z, f"{SLUG}_code_and_data.zip")
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as zf:
    for base in ["code", "data"]:
        for dp, _, fs in os.walk(os.path.join(ROOT, base)):
            for fn in fs:
                if fn.endswith(".pyc") or "__pycache__" in dp: continue
                p = os.path.join(dp, fn); zf.write(p, os.path.relpath(p, ROOT))
    for fn in ["README.md", "LICENSE"]: zf.write(os.path.join(ROOT, fn), fn)
tex = open(os.path.join(ROOT, "release", "paper", PDF.replace(".pdf", ".tex"))).read()
ab = re.search(r"\\textbf\{Abstract\}\\end\{center\}(.*?)\\textbf\{Keywords", tex, re.S).group(1).strip()
ab = ab.replace("\\%", "%").replace("~", " ").replace("\\&", "&")
title = re.search(r"pdftitle=\{(.*?)\},pdfauthor", tex).group(1)
zmeta = dict(title=title,
             description_html=f"<p>{ab}</p><p>Interactive version: https://maps.tristanhotham.com/{SLUG}/. Data and code: https://github.com/Tristan-Hotham/{SLUG}. Blog post: to follow.</p>",
             keywords=["place names", "toponymy", "place-name elements", "Old English", "Old Norse", "Welsh", "Cornish", "Gaelic", "townlands", "open data"],
             licence="cc-by-4.0",
             related=[dict(identifier=f"https://github.com/Tristan-Hotham/{SLUG}", relation="issupplementedby", resource_type="software"),
                      dict(identifier=f"https://maps.tristanhotham.com/{SLUG}/", relation="issupplementedby", resource_type="other"),
                      dict(identifier="https://www.ordnancesurvey.co.uk/products/os-open-names", relation="isderivedfrom", resource_type="dataset"),
                      dict(identifier="https://admin.opendatani.gov.uk/dataset/osni-open-data-gazetteer-place-names", relation="isderivedfrom", resource_type="dataset"),
                      dict(identifier="https://admin.opendatani.gov.uk/dataset/osni-open-data-largescale-boundaries-townlands", relation="isderivedfrom", resource_type="dataset"),
                      dict(identifier="https://data.gov.ie/dataset/townlands-national-placenames-gazetteer", relation="isderivedfrom", resource_type="dataset"),
                      dict(identifier="https://data.gov.ie/dataset/centres-of-population-national-placenames-gazetteer", relation="isderivedfrom", resource_type="dataset")])
json.dump(zmeta, open(os.path.join(z, "meta.json"), "w"), indent=1, ensure_ascii=False)
for fn in sorted(os.listdir(z)): print(fn, os.path.getsize(os.path.join(z, fn)))
