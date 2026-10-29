"""Step 2: tag every name with its elements and compute every number used anywhere.

Input:  work/names.csv.gz (from 01_prepare.py), code/elements.py (the rules)
Output: data/results.json, data/names_tagged.csv.gz, data/elements.csv, data/areas.csv,
        data/cells.csv, data/irish_forms.csv, work/tagged.pkl.gz
"""
import json, os, re, sys, collections
import numpy as np, pandas as pd
import shapely
from shapely.geometry import shape
from shapely.ops import unary_union
from pyproj import Transformer
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import elements as E

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK, DATA = os.path.join(ROOT, "work"), os.path.join(ROOT, "data")
LTLA = os.environ.get("LTLA", "/home/claude/hist/how-roman-is-your-road/data/ons/ltla.geojson")
os.makedirs(DATA, exist_ok=True)
NATN = {"E": "England", "W": "Wales", "S": "Scotland", "NI": "Northern Ireland", "ROI": "Republic of Ireland"}
NATS = ["E", "W", "S", "NI", "ROI"]
R = {}

d = pd.read_csv(os.path.join(WORK, "names.csv.gz"), keep_default_na=False)
d["el"] = [E.elements(n, na, a) for n, na, a in zip(d.name, d.nation, d.area)]
d["fams"] = [sorted({E.BY_KEY[k]["fam"] for k in e}, key=E.FAM_ORDER.index) for e in d.el]
d["n_el"] = d.el.str.len()
for f in E.FAM_ORDER: d["f_" + f] = d.fams.map(lambda s, f=f: f in s)
S = d[d.layer == "settlement"].copy(); T = d[d.layer == "townland"].copy()
pr = lambda x: round(float(x), 4)

prep = json.load(open(os.path.join(WORK, "prep_meta.json")))
R["meta"] = dict(prep, n_settlements=len(S), n_townlands=len(T), n_rules=len(E.RULES), n_names=len(d),
                 n_settlements_gb=int((S.nation.isin(["E", "W", "S"])).sum()), n_settlements_ie=int(S.nation.isin(["NI", "ROI"]).sum()),
                 n_nation={NATN[k]: int((S.nation == k).sum()) for k in NATS},
                 n_townlands_nation={NATN[k]: int((T.nation == k).sum()) for k in ["NI", "ROI"]})

# ---------- coverage ----------
R["coverage"] = dict(
    settlements_any=pr((S.n_el > 0).mean()), townlands_any=pr((T.n_el > 0).mean()),
    settlements_any_n=int((S.n_el > 0).sum()), townlands_any_n=int((T.n_el > 0).sum()),
    by_nation={NATN[k]: pr((S[S.nation == k].n_el > 0).mean()) for k in NATS},
    townlands_by_nation={NATN[k]: pr((T[T.nation == k].n_el > 0).mean()) for k in ["NI", "ROI"]},
    multi=int((S.n_el > 1).sum()))

# ---------- family shares ----------
fam = {}
for k in NATS:
    s = S[S.nation == k]
    fam[NATN[k]] = {f: pr(s["f_" + f].mean()) for f in E.FAM_ORDER}
famT = {NATN[k]: {f: pr(T[T.nation == k]["f_" + f].mean()) for f in E.FAM_ORDER} for k in ["NI", "ROI"]}
R["families"] = dict(labels=E.FAMILIES, order=E.FAM_ORDER, settlements=fam, townlands=famT,
                     counts={f: int(S["f_" + f].sum()) for f in E.FAM_ORDER}, counts_townlands={f: int(T["f_" + f].sum()) for f in E.FAM_ORDER})

# ---------- per element ----------
rows, elres = [], {}
for r in E.RULES:
    k = r["key"]; s = S[S.el.map(lambda e: k in e)]; t = T[T.el.map(lambda e: k in e)]
    by = {NATN[n]: int((s.nation == n).sum()) for n in NATS}
    byt = {NATN[n]: int((t.nation == n).sum()) for n in ["NI", "ROI"]}
    # where it is most at home: areas with at least 15 settlements (or 40 townlands)
    base = S if len(s) >= len(t) else T; sub = s if len(s) >= len(t) else t
    ac = base.groupby("area").size(); sc = sub.groupby("area").size()
    tab = pd.DataFrame({"n": ac, "k": sc}).fillna(0); tab = tab[tab.n >= (15 if base is S else 40)]
    tab["share"] = tab.k / tab.n
    top_n = sc.sort_values(ascending=False).head(5)
    top_s = tab.sort_values("share", ascending=False).head(5)
    ex = s.sort_values("kind").name.value_counts().head(0)
    big = s[s.kind.isin(["City", "Town"])].name.tolist()[:8]
    elres[k] = dict(label=r["label"], fam=r["fam"], meaning=r["meaning"], n=int(len(s)), n_townlands=int(len(t)), by_nation=by, townlands_by_nation=byt,
                    top_areas=[[a, int(c)] for a, c in top_n.items()], top_share_areas=[[a, int(x.k), int(x.n), pr(x.share)] for a, x in top_s.iterrows()],
                    town_share=pr(s.kind.isin(["City", "Town"]).mean()) if len(s) else None, towns=big)
    rows.append(dict(key=k, label=r["label"], family=r["fam"], meaning=r["meaning"], settlements=len(s), townlands=len(t),
                     **{"settlements_" + n: by[NATN[n]] for n in NATS}, **{"townlands_" + n: byt[NATN[n]] for n in ["NI", "ROI"]}))
R["elements"] = elres
R["element_order"] = sorted(elres, key=lambda k: -(elres[k]["n"] + elres[k]["n_townlands"]))
pd.DataFrame(rows).sort_values(["family", "settlements"], ascending=[True, False]).to_csv(os.path.join(DATA, "elements.csv"), index=False)

# top elements by nation (settlements)
R["top_by_nation"] = {NATN[n]: sorted([[k, v["by_nation"][NATN[n]]] for k, v in elres.items() if v["by_nation"][NATN[n]]], key=lambda x: -x[1])[:8] for n in NATS}
R["top_townlands"] = sorted([[k, v["n_townlands"]] for k, v in elres.items() if v["n_townlands"]], key=lambda x: -x[1])[:10]
eng = S[S.nation == "E"]
R["ton_share_england"] = pr(eng.el.map(lambda e: "ton" in e).mean())

# ---------- size: elements in towns and cities (Great Britain) ----------
G = S[S.nation.isin(["E", "W", "S"])]
base_town = G.kind.isin(["City", "Town"]).mean()
size = []
for k, v in elres.items():
    g = G[G.el.map(lambda e, k=k: k in e)]
    if len(g) >= 40:
        size.append([k, int(len(g)), int(g.kind.isin(["City", "Town"]).sum()), pr(g.kind.isin(["City", "Town"]).mean()), pr(g.kind.eq("Hamlet").mean())])
size.sort(key=lambda x: -x[3])
R["size"] = dict(base_town_share=pr(base_town), base_hamlet_share=pr(G.kind.eq("Hamlet").mean()), rows=size,
                 gb_kinds={k: int(v) for k, v in G.kind.value_counts().items()})

# ---------- Irish forms behind anglicised spellings (Republic of Ireland, official Irish forms) ----------
def ir_first(a):
    a = re.sub(r"\bt([AEIOUÁÉÍÓÚ])", r"\1", a)            # an tArd -> Ard
    a = re.sub(r"\bn([AEIOUÁÉÍÓÚ])", r"\1", a)            # na nOileán (eclipsis before a vowel)
    w = [x for x in re.split(r"[\s\-]+", E.fold(a)) if x not in ("an", "na", "")]
    if not w: return ""
    x = w[0]
    if len(x) > 2 and x[1] == "h" and x[0] in "bcdfgmpst": x = x[0] + x[2:]   # lenition: Chill -> Cill
    for ecl in ("mb", "gc", "nd", "bhf", "ng", "bp", "dt"):
        if x.startswith(ecl) and len(x) > 3: x = x[len(ecl) - 1:]; break
    return x
STEMS = {  # the Irish word each anglicised spelling is usually said to stand for
    "bal": ("baile", ["bail"]), "kil": ("cill", ["cill"]), "rath": ("rath", ["rath", "raith"]), "tully": ("tulach", ["tul"]),
    "ard": ("ard", ["ard", "aird"]), "clon": ("cluain", ["cluain", "cluan"]), "drum": ("droim", ["droim", "drom", "druim"]),
    "mullagh": ("mullach", ["mullach", "mullaigh"]), "lis": ("lios", ["lios", "lis"]), "derry": ("doire", ["doir"]),
    "carrick": ("carraig", ["carraig", "carrag"]), "bel": ("beal", ["beal"]), "inis": ("inis", ["inis", "inse", "insi", "inis"]),
    "knock": ("cnoc", ["cnoc", "cnoic"]), "dun": ("dun", ["dun", "duin"]), "glen": ("gleann", ["glean", "glin", "glinn"]),
    "kin": ("ceann", ["ceann", "cionn", "cinn"]), "auch": ("achadh", ["achadh", "achaidh", "acha"]),
}
ALT_LABEL = {"coill": "coill, wood", "beal": "beal (atha), mouth (of a ford)", "bealach": "bealach, pass or road", "buaile": "buaile, milking place",
             "domhnach": "domhnach, church", "ath": "ath, ford", "each": "each, horse", "cuil": "cuil, corner", "doirin": "doirin, little oak wood"}
IR = d[(d.nation == "ROI") & (d.alt != "")]
irows, ires = [], {}
for k, (word, stems) in STEMS.items():
    rr = E.BY_KEY[k]; c = collections.Counter()
    for n, a in zip(IR.name, IR.alt):
        t = E.tokens(n)
        if not t or t[0] in rr["exclude"] or not rr["rx"].fullmatch(t[0]): continue
        c[ir_first(a)] += 1
    tot = sum(c.values())
    if tot < 20: continue
    agree = sum(v for w, v in c.items() if any(w.startswith(s) for s in stems))
    others = [[w, v] for w, v in c.most_common(12) if not any(w.startswith(s) for s in stems)][:4]
    ires[k] = dict(label=rr["label"], word=word, n=tot, agree=agree, agree_share=pr(agree / tot), others=others)
    irows.append(dict(element=k, label=rr["label"], expected_irish_word=word, names_with_irish_form=tot, matching=agree, share=round(agree / tot, 4),
                      other_first_words="; ".join(f"{w} {v}" for w, v in others)))
# specific splits that the text quotes
def split(k, groups):
    rr = E.BY_KEY[k]; c = collections.Counter()
    for n, a in zip(IR.name, IR.alt):
        t = E.tokens(n)
        if t and t[0] not in rr["exclude"] and rr["rx"].fullmatch(t[0]): c[ir_first(a)] += 1
    tot = sum(c.values()); out = {}
    for g, pre in groups.items(): out[g] = sum(v for w, v in c.items() if any(w.startswith(p) for p in pre))
    out["other"] = tot - sum(out.values()); out["n"] = tot
    return out
R["irish_forms"] = dict(rows=ires, n_with_irish=int(len(IR)), n_townlands_irish=int((IR.layer == "townland").sum()),
                        kil=split("kil", {"cill": ["cill"], "coill": ["coill"]}),
                        bal=split("bal", {"baile": ["bail"], "beal": ["beal", "bel"], "bealach": ["bealach"], "buaile": ["buail"]}),
                        dun=split("dun", {"dun": ["dun", "duin"], "domhnach": ["domhnach"]}),
                        auch=split("auch", {"achadh": ["acha"], "ath": ["ath"], "each": ["each"]}))
# Kil- townlands: church (cill) or wood (coill), by county
rr = E.BY_KEY["kil"]; kk = IR[(IR.layer == "townland") & IR.name.map(lambda n: bool(E.tokens(n)) and E.tokens(n)[0] not in rr["exclude"] and bool(rr["rx"].fullmatch(E.tokens(n)[0])))]
kw = kk.alt.map(ir_first)
kc = pd.DataFrame({"area": kk.area, "cill": kw.str.startswith("cill"), "coill": kw.str.startswith("coill")}).groupby("area").agg(n=("cill", "size"), cill=("cill", "sum"), coill=("coill", "sum"))
kc = kc[kc.n >= 20].assign(sh=lambda t: t.coill / t.n).sort_values("sh", ascending=False)
R["irish_forms"]["kil_townlands"] = dict(cill=int(kw.str.startswith("cill").sum()), coill=int(kw.str.startswith("coill").sum()), n=int(len(kw)),
    counties=[[a, int(x.coill), int(x.n), round(float(x.sh), 4)] for a, x in kc.iterrows()])
# fix: bealach also starts with "beal": count it once
b = R["irish_forms"]["bal"]; b["beal"] -= b["bealach"]; b["other"] = b["n"] - b["baile"] - b["beal"] - b["bealach"] - b["buaile"]
pd.DataFrame(irows).sort_values("names_with_irish_form", ascending=False).to_csv(os.path.join(DATA, "irish_forms.csv"), index=False)

# ---------- Ireland: Bally and friends by county (townlands) ----------
cty = T.groupby("area").agg(n=("name", "size"), bal=("el", lambda s: int(sum("bal" in e for e in s))), kil=("el", lambda s: int(sum("kil" in e for e in s))),
                            drum=("el", lambda s: int(sum("drum" in e for e in s))), knock=("el", lambda s: int(sum("knock" in e for e in s))),
                            lis=("el", lambda s: int(sum("lis" in e for e in s))), derry=("el", lambda s: int(sum("derry" in e for e in s))),
                            clon=("el", lambda s: int(sum("clon" in e for e in s))))
cty["bal_share"] = cty.bal / cty.n
R["ireland"] = dict(
    bal_townlands=int(T.el.map(lambda e: "bal" in e).sum()), bal_townland_share=pr(T.el.map(lambda e: "bal" in e).mean()),
    bal_share_roi=pr(T[T.nation == "ROI"].el.map(lambda e: "bal" in e).mean()), bal_share_ni=pr(T[T.nation == "NI"].el.map(lambda e: "bal" in e).mean()),
    bal_settlements=int(S[S.nation.isin(["NI", "ROI"])].el.map(lambda e: "bal" in e).sum()),
    bal_settlement_share=pr(S[S.nation.isin(["NI", "ROI"])].el.map(lambda e: "bal" in e).mean()),
    goidelic_townlands=pr(T.f_goidelic.mean()), english_townlands=pr(T.f_english.mean()),
    town_settlements_ie=int(S[S.nation.isin(["NI", "ROI"])].el.map(lambda e: "town" in e).sum()),
    town_share_ie=pr(S[S.nation.isin(["NI", "ROI"])].el.map(lambda e: "town" in e).mean()),
    town_share_townlands=pr(T.el.map(lambda e: "town" in e).mean()),
    counties=[[a, int(x.n), int(x.bal), pr(x.bal_share)] for a, x in cty.sort_values("bal_share", ascending=False).iterrows()],
    gaeltacht_cop=int(((d.layer == "settlement") & (d.nation == "ROI") & (d.gaeltacht == "Y")).sum()))
cty.reset_index().to_csv(os.path.join(WORK, "ireland_counties.csv"), index=False)

# ---------- Scotland: aber versus inver, and Pictish pit- ----------
sc = S[S.nation == "S"]
ab = sc[sc.el.map(lambda e: "aber" in e)]; iv = sc[sc.el.map(lambda e: "inver" in e)]; pit = sc[sc.el.map(lambda e: "pit" in e)]
R["scotland"] = dict(aber=int(len(ab)), inver=int(len(iv)), pit=int(len(pit)),
                     aber_mean_lon=pr(ab.lon.mean()), inver_mean_lon=pr(iv.lon.mean()), aber_east_of_4w=int((ab.lon > -4).sum()), inver_west_of_4w=int((iv.lon <= -4).sum()),
                     aber_areas=[[a, int(c)] for a, c in ab.area.value_counts().head(6).items()], inver_areas=[[a, int(c)] for a, c in iv.area.value_counts().head(6).items()],
                     pit_areas=[[a, int(c)] for a, c in pit.area.value_counts().head(6).items()], pit_east_of_4w=int((pit.lon > -4).sum()),
                     families={a: {f: pr(g["f_" + f].mean()) for f in E.FAM_ORDER} | {"n": int(len(g))} for a, g in sc.groupby("area") if len(g) >= 40},
                     norse_isles={a: pr(sc[sc.area == a].f_norse.mean()) for a in ["Shetland Islands", "Orkney Islands"]},
                     gaelic_share=pr(sc.f_goidelic.mean()), english_share=pr(sc.f_english.mean()))

# ---------- Wales and England: the border profile ----------
to_bng = Transformer.from_crs(4326, 27700, always_xy=True)
lj = json.load(open(LTLA))
wal, engp = [], []
for f in lj["features"]:
    p = f["properties"]
    if p.get("end") is not None: continue
    if p["areacd"].startswith("W"): wal.append(shapely.make_valid(shape(f["geometry"])).buffer(0))
    elif p["areacd"].startswith("E"): engp.append(shapely.make_valid(shape(f["geometry"])).buffer(0))
W_ = shapely.transform(unary_union(wal), lambda a: np.column_stack(to_bng.transform(a[:, 0], a[:, 1])))
E_ = shapely.transform(unary_union(engp), lambda a: np.column_stack(to_bng.transform(a[:, 0], a[:, 1])))
border = W_.boundary.intersection(E_.buffer(200))       # the land border only
gw = G[G.nation.isin(["E", "W"]) & (G.lat > 51.45) & (G.lat < 53.45)].copy()
x, y = to_bng.transform(gw.lon.values, gw.lat.values)
pts = shapely.points(x, y)
dist = shapely.distance(pts, border) / 1000
gw["sd"] = np.where(gw.nation == "W", dist, -dist)
gw = gw[gw.sd.abs() <= 60]
WEL = {"llan", "aber", "pen", "tre", "caer", "cwm", "bryn", "nant", "rhyd", "maes", "betws", "pont"}
gw["welsh"] = gw.name.map(lambda n: E.matches_any(n, WEL))
gw["english"] = gw.f_english
gw["band"] = (np.floor(gw.sd / 5) * 5).astype(int)
prof = gw.groupby("band").agg(n=("name", "size"), welsh=("welsh", "mean"), english=("english", "mean")).reset_index()
R["border"] = dict(rows=[[int(b), int(n), pr(w), pr(e)] for b, n, w, e in prof.itertuples(index=False)],
                   welsh_within5_w=pr(gw[(gw.sd > 0) & (gw.sd <= 5)].welsh.mean()), welsh_within5_e=pr(gw[(gw.sd < 0) & (gw.sd >= -5)].welsh.mean()),
                   welsh_20_40_w=pr(gw[(gw.sd > 20) & (gw.sd <= 40)].welsh.mean()), welsh_20_40_e=pr(gw[(gw.sd < -20) & (gw.sd >= -40)].welsh.mean()),
                   english_within5_w=pr(gw[(gw.sd > 0) & (gw.sd <= 5)].english.mean()), english_20_40_w=pr(gw[(gw.sd > 20) & (gw.sd <= 40)].english.mean()),
                   english_within5_e=pr(gw[(gw.sd < 0) & (gw.sd >= -5)].english.mean()),
                   welsh_in_england_n=int(gw[(gw.sd < 0)].welsh.sum()),
                   welsh_in_england_examples=gw[(gw.sd < 0) & gw.welsh].sort_values("sd").name.tolist()[-12:],
                   welsh_rules=sorted(WEL))
WALES = S[S.nation == "W"]
R["wales"] = dict(any_welsh=pr(WALES.el.map(lambda e: bool(WEL & set(e))).mean()), english_share=pr(WALES.f_english.mean()),
                  llan=elres["llan"]["by_nation"]["Wales"], top=R["top_by_nation"]["Wales"],
                  west_counties={a: pr(g.el.map(lambda e: bool(WEL & set(e))).mean()) for a, g in WALES.groupby("area")})

# ---------- Cornwall and Devon: west to east ----------
CORN = {"tre", "pol", "pen", "porth", "bos", "lan", "ros"}
cw = G[G.area.isin(["Cornwall", "Devon"])].copy()
cw["cornish"] = cw.name.map(lambda n: E.matches_any(n, CORN))
cw["band"] = (np.floor(cw.lon / 0.25) * 0.25).round(2)
cp = cw.groupby("band").agg(n=("name", "size"), cornish=("cornish", "mean")).reset_index()
R["cornwall"] = dict(rows=[[float(b), int(n), pr(c)] for b, n, c in cp.itertuples(index=False) if n >= 15],
                     cornwall_share=pr(cw[cw.area == "Cornwall"].cornish.mean()), devon_share=pr(cw[cw.area == "Devon"].cornish.mean()),
                     cornwall_n=int((cw.area == "Cornwall").sum()), devon_n=int((cw.area == "Devon").sum()),
                     tre_cornwall=int(cw[(cw.area == "Cornwall")].el.map(lambda e: "tre" in e).sum()), tre_devon=int(cw[(cw.area == "Devon")].el.map(lambda e: "tre" in e).sum()),
                     west_share=pr(cw[(cw.area == "Cornwall") & (cw.lon < -5.0)].cornish.mean()), east_share=pr(cw[(cw.area == "Cornwall") & (cw.lon >= -4.6)].cornish.mean()),
                     devon_examples=cw[(cw.area == "Devon") & cw.cornish].name.tolist()[:12])

# ---------- Norse: a pointer, not a repeat of dale-down-fell-beck ----------
NORSE = ["by", "thorpe", "thwaite", "toft", "holme", "kirk", "scale", "setter", "vik"]
R["norse"] = dict(n=int(S.f_norse.sum()), england=pr(eng.f_norse.mean()),
                  top_areas=[[a, int(g.f_norse.sum()), int(len(g)), pr(g.f_norse.mean())] for a, g in sorted(G.groupby("area"), key=lambda x: -x[1].f_norse.mean()) if len(g) >= 40][:8])

# ---------- grids: equal steps of latitude and longitude ----------
def grid(df, dlat, dlon, label):
    i = np.floor(df.lat / dlat).astype(int); j = np.floor(df.lon / dlon).astype(int)
    df = df.assign(ci=i, cj=j)
    out = []
    for (a, b), g in df.groupby(["ci", "cj"]):
        fc = [int(g["f_" + f].sum()) for f in E.FAM_ORDER]
        ec = collections.Counter(k for e in g.el for k in e)
        out.append(dict(grid=label, ci=int(a), cj=int(b), lat0=round(a * dlat, 4), lon0=round(b * dlon, 4), n=len(g), n_tagged=int((g.n_el > 0).sum()),
                        **{"fam_" + f: c for f, c in zip(E.FAM_ORDER, fc)}, elements=";".join(f"{k}:{v}" for k, v in sorted(ec.items()))))
    return out
GR = dict(fine=(0.15, 0.25), coarse=(0.3, 0.5))
cells = []
for nm, (a, b) in GR.items():
    cells += [dict(c, layer="settlement") for c in grid(S, a, b, nm)]
    cells += [dict(c, layer="townland") for c in grid(T, a, b, nm)]
cdf = pd.DataFrame(cells); cdf.to_csv(os.path.join(DATA, "cells.csv"), index=False)
# dominant family in fine settlement cells
fs = cdf[(cdf.grid == "fine") & (cdf.layer == "settlement") & (cdf.n_tagged >= 3)]
dom = fs[["fam_" + f for f in E.FAM_ORDER]].idxmax(axis=1).str[4:]
R["grid"] = dict(steps=GR, fine_cells=int(len(cdf[(cdf.grid == "fine") & (cdf.layer == "settlement")])),
                 dominant_counts={f: int((dom == f).sum()) for f in E.FAM_ORDER}, dominant_n=int(len(fs)))

# ---------- areas ----------
ar = []
for (na, a), g in d.groupby(["nation", "area"]):
    for lay, h in g.groupby("layer"):
        ec = collections.Counter(k for e in h.el for k in e)
        ar.append(dict(nation=NATN[na], area=a, layer=lay, names=len(h), tagged=int((h.n_el > 0).sum()),
                       **{"fam_" + f: int(h["f_" + f].sum()) for f in E.FAM_ORDER}, top_elements="; ".join(f"{k} {v}" for k, v in ec.most_common(6))))
pd.DataFrame(ar).to_csv(os.path.join(DATA, "areas.csv"), index=False)

# ---------- names ----------
R["common_names"] = {NATN[n]: [[k, int(v)] for k, v in S[S.nation == n].name.value_counts().head(6).items()] for n in ["E", "W", "S"]}
R["common_townlands"] = [[k, int(v)] for k, v in T.name.value_counts().head(8).items()]

out = d[["name", "alt", "alt_lang", "kind", "layer", "nation", "area", "lat", "lon", "src"]].copy()
out["nation"] = out.nation.map(NATN); out["elements"] = d.el.map(";".join); out["families"] = d.fams.map(";".join)
out.to_csv(os.path.join(DATA, "names_tagged.csv.gz"), index=False, compression="gzip")
d.to_pickle(os.path.join(WORK, "tagged.pkl.gz"), compression="gzip")
json.dump(R, open(os.path.join(DATA, "results.json"), "w"), indent=1, ensure_ascii=False)
print(json.dumps({k: R[k] for k in ["border", "cornwall", "ireland", "irish_forms", "size", "grid", "norse", "wales"]}, ensure_ascii=False)[:9000])
