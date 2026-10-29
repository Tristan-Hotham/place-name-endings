"""Step 6: static figures for the blog and paper (release/blog/b_*.png) and the social card (header.png).
Run: FONT_DIR=path/to/fonts python3 code/06_figures.py
"""
import json, os, re, sys
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib import font_manager as fm
from matplotlib.collections import PolyCollection
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import elements as E

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_DIR = os.environ.get("FONT_DIR", "/tmp/claude-0/-home-claude/c232619d-81e0-53f3-9de6-41e973630753/scratchpad/fonts/")
for f in ["FrauncesVar.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "SourceSerif4-It.ttf"]:
    p = os.path.join(FONT_DIR, f)
    if os.path.exists(p): fm.fontManager.addfont(p)
DISP = fm.FontProperties(fname=os.path.join(FONT_DIR, "FrauncesVar.ttf"), weight=900)
SER, MONO = "Source Serif 4", "IBM Plex Mono"
BG, FG, MUT, RULE, LAND = "#F5F1E6", "#1D1A16", "#625D54", "#DAD2C0", "#E9E3D3"
FC = {"english": "#B23A48", "norse": "#2B5C9E", "latin": "#7A5195", "brittonic": "#13866A", "goidelic": "#C98A0B"}
FL = {"english": "English", "norse": "Norse", "latin": "Latin", "brittonic": "Brittonic (Welsh, Cornish, Pictish)", "goidelic": "Gaelic (Irish, Scottish)"}
plt.rcParams.update({"font.family": SER, "axes.edgecolor": MUT, "axes.labelcolor": FG, "xtick.color": MUT, "ytick.color": MUT,
                     "savefig.facecolor": BG, "figure.facecolor": BG, "axes.facecolor": BG, "font.size": 15})
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
OUT = os.path.join(ROOT, "release", "blog"); os.makedirs(OUT, exist_ok=True)
d = pd.read_pickle(os.path.join(ROOT, "work", "tagged.pkl.gz"))
K = np.cos(np.radians(54.5))
def xy(lon, lat): return np.asarray(lon) * K, np.asarray(lat)
ol = json.load(open(os.path.join(ROOT, "data", "page", "outline.json")))
def land(ax, fc=LAND, ec="#BDB3A0", lw=.5, z=0):
    g = ol["land"]; polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    P = []
    for p in polys:
        a = np.array(p[0]); x, y = xy(a[:, 0], a[:, 1]); P.append(np.column_stack([x, y]))
    ax.add_collection(PolyCollection(P, facecolors=fc, edgecolors=ec, linewidths=lw, zorder=z))
def borders(ax, c="#6B6458", lw=.8, z=5):
    g = ol["borders"]; lines = g["coordinates"] if g["type"] == "MultiLineString" else [g["coordinates"]]
    for l in lines:
        a = np.array(l); x, y = xy(a[:, 0], a[:, 1]); ax.plot(x, y, color=c, lw=lw, ls=(0, (3, 2)), zorder=z)
def save(fig, name, **kw):
    fig.savefig(os.path.join(OUT, name), dpi=100, **kw); plt.close(fig); print(name)
def first_fam(e): return E.BY_KEY[e[0]]["fam"] if e else None

# ---------- 1. the big map: Great Britain settlements and Irish townlands ----------
def big_map(ax, dot=1.6, grey=.5):
    pts = d[((d.layer == "settlement") & d.nation.isin(["E", "W", "S"])) | (d.layer == "townland")]
    x, y = xy(pts.lon, pts.lat); f = pts.el.map(first_fam)
    land(ax)
    m = f.isna().values
    ax.scatter(x[m], y[m], s=grey, color="#B8AE9C", lw=0, zorder=1)
    for fam in ["english", "goidelic", "brittonic", "norse", "latin"]:
        mm = (f == fam).values
        ax.scatter(x[mm], y[mm], s=dot * (1.6 if fam == "latin" else 1), color=FC[fam], lw=0, zorder=2 + (fam in ("norse", "latin")))
    borders(ax)
    ax.set_xlim(-10.7 * K, 1.9 * K); ax.set_ylim(49.85, 60.9); ax.set_aspect("equal"); ax.axis("off")
fig = plt.figure(figsize=(15.2, 16.5)); ax = fig.add_axes([0, 0, 1, 1]); big_map(ax, dot=2.4, grey=.9)
for i, fam in enumerate(["english", "norse", "latin", "brittonic", "goidelic"]):
    ax.scatter([-10.3 * K], [60.35 - i * .36], s=160, color=FC[fam], zorder=6)
    ax.text(-10.3 * K + .2, 60.35 - i * .36, FL[fam], family=MONO, fontsize=17, va="center", color=FG)
ax.scatter([-10.3 * K], [60.35 - 5 * .36], s=60, color="#B8AE9C", zorder=6); ax.text(-10.3 * K + .2, 60.35 - 5 * .36, "none of the 67 elements", family=MONO, fontsize=17, va="center", color=MUT)
ax.text(-10.45 * K, 49.95, "Great Britain: settlements (OS Open Names).\nIreland: townlands (OSNI; Tailte Éireann).\nColour: first language family in the name.", family=MONO, fontsize=13.5, color=MUT, va="bottom", linespacing=1.4)
save(fig, "b_map.png")

# ---------- 2. family shares by nation ----------
rows = [(n, R["families"]["settlements"][n]) for n in ["England", "Wales", "Scotland", "Northern Ireland", "Republic of Ireland"]] + \
       [("Northern Ireland townlands", R["families"]["townlands"]["Northern Ireland"]), ("Republic townlands", R["families"]["townlands"]["Republic of Ireland"])]
fig, ax = plt.subplots(figsize=(15.2, 6.6)); fig.subplots_adjust(left=.25, right=.97, top=.86, bottom=.1)
for i, (n, f) in enumerate(rows[::-1]):
    x0 = 0
    for fam in E.FAM_ORDER:
        v = f[fam]
        if v: ax.barh(i, v, left=x0, color=FC[fam], height=.66); x0 += v
    ax.text(x0 + .006, i, f"{round(x0 * 100)}%", va="center", family=MONO, fontsize=13, color=MUT)
ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0] for r in rows[::-1]], fontsize=16)
ax.set_xlim(0, .62); ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1, decimals=0)); ax.tick_params(labelsize=13)
for s in ["top", "right", "left"]: ax.spines[s].set_visible(False)
ax.grid(axis="x", color=RULE); ax.set_axisbelow(True)
for i, fam in enumerate(E.FAM_ORDER):
    fig.text(.25 + i * .15, .93, "■", color=FC[fam], fontsize=18, va="center"); fig.text(.265 + i * .15, .93, FL[fam].split(" (")[0], family=MONO, fontsize=13.5, va="center")
save(fig, "b_families.png")

# ---------- 3. commonest elements ----------
top = sorted(R["elements"].items(), key=lambda kv: -kv[1]["n"])[:16]
twn = sorted(R["elements"].items(), key=lambda kv: -kv[1]["n_townlands"])[:8]
fig, (a1, a2) = plt.subplots(1, 2, figsize=(15.2, 7.4), gridspec_kw=dict(width_ratios=[1.35, 1])); fig.subplots_adjust(left=.17, right=.97, top=.9, bottom=.06, wspace=.55)
for ax, lst, key, ttl in [(a1, top, "n", "Settlements, Britain and Ireland"), (a2, twn, "n_townlands", "Irish townlands")]:
    for i, (k, v) in enumerate(lst[::-1]):
        ax.barh(i, v[key], color=FC[v["fam"]], height=.7); ax.text(v[key] * 1.01, i, f"{v[key]:,}", va="center", family=MONO, fontsize=12.5)
    ax.set_yticks(range(len(lst))); ax.set_yticklabels([v["label"] for k, v in lst[::-1]], family=MONO, fontsize=14)
    ax.set_xticks([]); [ax.spines[s].set_visible(False) for s in ["top", "right", "bottom"]]
    ax.set_title(ttl, family=MONO, fontsize=15, loc="left", color=MUT); ax.set_xlim(0, lst[0][1][key] * 1.2)
save(fig, "b_top.png")

# ---------- 4. the Welsh border ----------
b = pd.DataFrame(R["border"]["rows"], columns=["band", "n", "welsh", "english"]); b["mid"] = b.band + 2.5
fig, ax = plt.subplots(figsize=(15.2, 6.8)); fig.subplots_adjust(left=.08, right=.97, top=.92, bottom=.2)
ax.plot(b.mid, b.welsh, "-o", color=FC["brittonic"], lw=3.5, ms=7); ax.plot(b.mid, b.english, "-o", color=FC["english"], lw=3.5, ms=7)
ax.axvline(0, color=FG, ls=(0, (4, 3)), lw=1.4)
ax.text(1.5, .53, "the border", family=MONO, fontsize=14)
ax.text(-58, .55, "English element", color=FC["english"], family=MONO, fontsize=16, weight="bold"); ax.text(31, .44, "Welsh element", color=FC["brittonic"], family=MONO, fontsize=16, weight="bold")
ax.set_xticks(range(-60, 61, 20)); ax.set_xticklabels([f"{abs(v)} km" for v in range(-60, 61, 20)], fontsize=13)
ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1, decimals=0)); ax.tick_params(labelsize=13); ax.set_ylim(0, .6)
ax.text(0, -.14, "England", family=MONO, fontsize=15, transform=ax.transAxes); ax.text(1, -.14, "Wales", family=MONO, fontsize=15, ha="right", transform=ax.transAxes)
[ax.spines[s].set_visible(False) for s in ["top", "right"]]; ax.grid(axis="y", color=RULE); ax.set_axisbelow(True)
save(fig, "b_border.png")

# ---------- 5. Cornwall and the Tamar ----------
c = pd.DataFrame(R["cornwall"]["rows"], columns=["band", "n", "share"])
fig, ax = plt.subplots(figsize=(15.2, 6.2)); fig.subplots_adjust(left=.08, right=.97, top=.92, bottom=.21)
ax.bar(c.band + .125, c.share, width=.23, color=FC["brittonic"])
for r in c.itertuples(): ax.text(r.band + .125, r.share + .01, f"{round(r.share * 100)}%", ha="center", family=MONO, fontsize=12.5)
ax.axvline(-4.2, color=FG, ls=(0, (4, 3)), lw=1.4); ax.text(-4.17, .45, "the Tamar", family=MONO, fontsize=14)
ax.set_xticks([-5.75, -5.25, -4.75, -4.25, -3.75, -3.25, -2.75]); ax.set_xticklabels([f"{-v:.2f}° W" for v in [-5.75, -5.25, -4.75, -4.25, -3.75, -3.25, -2.75]], fontsize=13)
ax.text(0, -.15, "Land's End", family=MONO, fontsize=14, transform=ax.transAxes); ax.text(1, -.15, "east Devon", family=MONO, fontsize=14, ha="right", transform=ax.transAxes)
ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1, decimals=0)); ax.tick_params(labelsize=13); ax.set_ylim(0, .52)
[ax.spines[s].set_visible(False) for s in ["top", "right"]]; ax.grid(axis="y", color=RULE); ax.set_axisbelow(True)
save(fig, "b_cornwall.png")

# ---------- 6. Irish forms ----------
rows = sorted(R["irish_forms"]["rows"].items(), key=lambda kv: -kv[1]["agree_share"])
fig, ax = plt.subplots(figsize=(15.2, 8.6)); fig.subplots_adjust(left=.2, right=.96, top=.97, bottom=.08)
for i, (k, v) in enumerate(rows[::-1]):
    low = v["agree_share"] < .85
    ax.barh(i, v["agree_share"], color=FC["goidelic"], alpha=1 if low else .5, height=.7)
    ax.text(v["agree_share"] + .004, i, f"{round(v['agree_share'] * 100)}% {v['word']}  (of {v['n']:,})", va="center", family=MONO, fontsize=12.5, color=FG)
ax.set_yticks(range(len(rows))); ax.set_yticklabels([v["label"] for k, v in rows[::-1]], family=MONO, fontsize=13.5)
ax.set_xlim(.5, 1.18); ax.set_xticks([.5, .6, .7, .8, .9, 1]); ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1, decimals=0)); ax.tick_params(axis="x", labelsize=13)
[ax.spines[s].set_visible(False) for s in ["top", "right"]]; ax.grid(axis="x", color=RULE); ax.set_axisbelow(True)
save(fig, "b_irish.png")

# ---------- 7. Kil-: church or wood, mapped ----------
IR = d[(d.nation == "ROI") & (d.layer == "townland") & (d.alt != "")]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib.util
spec = importlib.util.spec_from_file_location("an", os.path.join(os.path.dirname(os.path.abspath(__file__)), "02_analyse.py"))
def ir_first(a):
    a = re.sub(r"\bt([AEIOUÁÉÍÓÚ])", r"\1", a); a = re.sub(r"\bn([AEIOUÁÉÍÓÚ])", r"\1", a)
    w = [x for x in re.split(r"[\s\-]+", E.fold(a)) if x not in ("an", "na", "")]
    if not w: return ""
    x = w[0]
    if len(x) > 2 and x[1] == "h" and x[0] in "bcdfgmpst": x = x[0] + x[2:]
    return x
rr = E.BY_KEY["kil"]
kil = IR[IR.name.map(lambda n: bool(E.tokens(n)) and E.tokens(n)[0] not in rr["exclude"] and bool(rr["rx"].fullmatch(E.tokens(n)[0])))].copy()
kil["w"] = kil.alt.map(ir_first)
fig = plt.figure(figsize=(15.2, 14)); ax = fig.add_axes([0, 0, 1, 1])
land(ax, ec="#BDB3A0")
for lab, pre, col in [("cill: church", "cill", "#7A5195"), ("coill: wood", "coill", "#13866A")]:
    m = kil[kil.w.str.startswith(pre)]; x, y = xy(m.lon, m.lat); ax.scatter(x, y, s=26, color=col, lw=.3, edgecolor="white", label=f"{lab} ({len(m):,})", zorder=3)
borders(ax)
ax.set_xlim(-10.7 * K, -5.3 * K); ax.set_ylim(51.35, 55.45); ax.set_aspect("equal"); ax.axis("off")
lg = ax.legend(loc="upper left", frameon=False, prop=dict(family=MONO, size=18), markerscale=2.2, bbox_to_anchor=(0.02, 0.98))
ax.text(-10.6 * K, 51.42, "Townlands in the Republic of Ireland starting with Kil- or Kill-, by the first word of their official Irish form.\nNorthern Ireland has no Irish forms in this data.", family=MONO, fontsize=13.5, color=MUT)
save(fig, "b_kil_map.png")

# ---------- social card ----------
fig = plt.figure(figsize=(12, 6.3)); 
ax = fig.add_axes([.55, 0, .45, 1]); big_map(ax, dot=.35, grey=.12)
fig.text(.04, .86, "What is your\ntown's name\nmade of?", fontproperties=DISP, fontsize=50, color=FG, va="top", linespacing=.98)
chips = [("-ton", "english"), ("-by", "norse"), ("-chester", "latin"), ("llan-", "brittonic"), ("bally-", "goidelic")]
x = .04
for t, fam in chips:
    tt = fig.text(x, .34, t, fontproperties=DISP, fontsize=25, color="white" if fam != "goidelic" else FG, va="center",
                  bbox=dict(boxstyle="square,pad=0.28", fc=FC[fam], ec="none"))
    x += .028 + len(t) * .0185
fig.text(.04, .2, f"{R['meta']['n_names']:,} place names in Britain and Ireland,\ntagged by their English, Norse, Latin, Welsh and Gaelic words", family=SER, fontsize=15.5, color=FG, va="top")
fig.text(.04, .055, "maps.tristanhotham.com/place-name-endings", family=MONO, fontsize=12, color=MUT)
fig.savefig(os.path.join(ROOT, "header.png"), dpi=100); plt.close(fig); print("header.png")
