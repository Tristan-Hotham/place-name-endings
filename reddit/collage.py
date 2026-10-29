"""Reddit collage: run from this folder (python3 collage.py). Reads ../work/tagged.pkl.gz, ../data/results.json, ../data/page/outline.json."""
import json, os, sys
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.collections import PolyCollection
sys.path.insert(0, "../code")
import elements as E
F = os.environ.get("FONT_DIR", "/tmp/claude-0/-home-claude/c232619d-81e0-53f3-9de6-41e973630753/scratchpad/fonts/")
for f in ["FrauncesVar.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "SourceSerif4-It.ttf"]: fm.fontManager.addfont(F + f)
DISP = fm.FontProperties(fname=F + "FrauncesVar.ttf", weight=900)
SER, MONO = "Source Serif 4", "IBM Plex Mono"
BG, FG, MUT, LAND, GREY = "#EEF0E9", "#1B1D1A", "#5E625A", "#DCDFD3", "#B9BDB0"
FC = {"english": "#B23A48", "norse": "#2B5C9E", "latin": "#7A5195", "brittonic": "#13866A", "goidelic": "#C98A0B"}
R = json.load(open("../data/results.json")); d = pd.read_pickle("../work/tagged.pkl.gz")
ol = json.load(open("../data/page/outline.json"))
K = np.cos(np.radians(54.5))
P = []
g = ol["land"]
for p in (g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]):
    a = np.array(p[0]); P.append(np.column_stack([a[:, 0] * K, a[:, 1]]))
def base(ax, lw=.4):
    ax.add_collection(PolyCollection(P, facecolors=LAND, edgecolors="#C6C9BC", linewidths=lw, zorder=0))
    ax.set_xlim(-10.7 * K, 1.9 * K); ax.set_ylim(49.85, 60.9); ax.set_aspect("equal"); ax.axis("off")
pts = d[((d.layer == "settlement") & d.nation.isin(["E", "W", "S"])) | (d.layer == "townland")]
fam1 = pts.el.map(lambda e: E.BY_KEY[e[0]]["fam"] if e else None)
x, y = pts.lon.values * K, pts.lat.values
fig = plt.figure(figsize=(12, 15), dpi=200, facecolor=BG)
fig.text(.04, .968, "What is your town's name made of?", fontproperties=DISP, fontsize=44, color=FG, va="top")
fig.text(.04, .922, f"Every settlement in Britain and every Irish townland, {R['meta']['n_names']:,} names, coloured by the language\nof the old word inside: -ton and -ham, -by and -thorpe, -chester, llan- and tre-, bally- and kil-.", family=SER, fontsize=15.5, color=FG, va="top", linespacing=1.35)
ax = fig.add_axes([-.03, .272, .63, .605]); base(ax)
m = fam1.isna().values; ax.scatter(x[m], y[m], s=.35, c=GREY, lw=0, rasterized=True)
for f in ["english", "goidelic", "brittonic", "norse", "latin"]:
    mm = (fam1 == f).values; ax.scatter(x[mm], y[mm], s=(5 if f == "latin" else 2.4 if f in ("brittonic", "norse") else 1.5), c=FC[f], lw=0, rasterized=True)
LEG = [("english", "English", "-ton  -ham  -ley  -ing"), ("norse", "Norse", "-by  -thorpe  -thwaite"), ("latin", "Latin", "-chester  -caster  strat-"),
       ("brittonic", "Welsh, Cornish, Pictish", "llan-  aber-  tre-  pol-  pit-"), ("goidelic", "Gaelic", "bally-  kil-  inver-  drum-")]
for i, (f, lab, ex) in enumerate(LEG):
    yy = .848 - i * .036
    fig.text(.585, yy, "●", color=FC[f], fontsize=17, va="center"); fig.text(.61, yy + .006, lab, family=MONO, fontsize=12.5, color=FG, va="center", weight="medium")
    fig.text(.61, yy - .011, ex, family=MONO, fontsize=10.5, color=MUT, va="center")
IF = R["irish_forms"]; kc = IF["kil_townlands"]["counties"][0]
notes = [(f"{R['elements']['ton']['n']:,}", FC["english"], f"settlements end in -ton, the Old English\nword for a farmstead: {round(R['ton_share_england'] * 100)}% of England's."),
         (f"{round(R['page']['kil_coill_share'] * 100)}%", FC["goidelic"], f"of Irish Kil- names are coill, wood, not cill,\nchurch. In {kc[0]}, {kc[1]} of {kc[2]} Kil- townlands."),
         (f"{round(R['border']['welsh_20_40_w'] * 100)}% | {R['border']['welsh_20_40_e'] * 100:.1f}%", FC["brittonic"], "of settlements with a Welsh element, 20 to\n40 km inside Wales and inside England."),
         (f"{round(R['cornwall']['cornwall_share'] * 100)}% | {R['cornwall']['devon_share'] * 100:.1f}%", FC["brittonic"], "with a Cornish element (tre-, pol-, pen-)\nin Cornwall and in Devon. The Tamar holds.")]
for i, (big, col, small) in enumerate(notes):
    yy = .655 - i * .097
    fig.text(.585, yy, big, fontproperties=DISP, fontsize=30, color=col, va="top")
    fig.text(.585, yy - .037, small, family=SER, fontsize=12.5, color=FG, va="top", linespacing=1.25)
# small multiples
SM = [("by", "-by", "Norse farmstead"), ("chester", "-chester", "Roman fort, via English"), ("llan", "llan-", "Welsh church enclosure"),
      ("pit", "pit-", "Pictish share of land"), ("bal", "bally- / bal-", "Gaelic homestead"), ("kil", "kil-", "church or wood?")]
IRF = d[(d.nation == "ROI") & (d.alt != "")]
for i, (k, lab, sub) in enumerate(SM):
    a = fig.add_axes([.012 + i * .163, .09, .158, .15]); base(a, lw=.2)
    q = d[d.el.map(lambda e, k=k: k in e)]
    if k == "kil":
        import re
        def first(s): w = [t for t in re.split(r"[\s\-]+", E.fold(s)) if t not in ("an", "na", "")]; x0 = w[0] if w else ""; return x0[0] + x0[2:] if len(x0) > 2 and x0[1] == "h" else x0
        qi = q[(q.nation == "ROI") & (q.alt != "")]; fw = qi.alt.map(first)
        for pre, col in [("cill", FC["latin"]), ("coill", FC["brittonic"])]:
            qq = qi[fw.str.startswith(pre)]; a.scatter(qq.lon * K, qq.lat, s=1.6, c=col, lw=0, rasterized=True)
        a.text(.5, -.02, "purple: cill, church\ngreen: coill, wood", transform=a.transAxes, ha="center", va="top", family=MONO, fontsize=9, color=MUT)
        n = f"{R['elements']['kil']['n'] + R['elements']['kil']['n_townlands']:,}"
    else:
        s = 6 if len(q) < 200 else 2.4 if len(q) < 1500 else 1.0
        a.scatter(q.lon * K, q.lat, s=s, c=FC[E.BY_KEY[k]["fam"]], lw=0, rasterized=True)
        a.text(.5, -.02, sub, transform=a.transAxes, ha="center", va="top", family=MONO, fontsize=9, color=MUT)
        n = f"{len(q):,}"
    a.set_title(f"{lab}  {n}", family=MONO, fontsize=11.5, color=FG, pad=3)
fig.text(.04, .268, "SIX ELEMENTS", family=MONO, fontsize=11, color=MUT)
fig.text(.04, .014, "Data: OS Open Names (contains OS data © Crown copyright and database right 2026, OGL v3); OSNI Open Data\ngazetteer and townlands (OGL v3); National Placenames Gazetteer © Tailte Éireann (CC BY 4.0). Spelling rules,\nnot etymologies. Analysis and chart: Tristan Hotham, with Python and matplotlib. maps.tristanhotham.com/place-name-endings",
         family=MONO, fontsize=9, color=MUT, linespacing=1.4)
fig.savefig("place_name_endings.png", facecolor=BG, dpi=200)
print("ok")
