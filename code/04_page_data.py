"""Step 4: compact data files for the interactive page (data/page/).

  settlements.json  every settlement: name, alternative name, kind, nation, area, position, elements
  townlands.json    every townland in Ireland (loaded when the reader switches Ireland to townlands)
  cells.json        counts per grid cell (two sizes, settlements and townlands)
  outline.json      land and nation borders (simplified) for the plain base map and the borders layer
"""
import json, os, sys
import numpy as np, pandas as pd
import shapely
from shapely.geometry import shape, mapping
from shapely.ops import unary_union
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import elements as E

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "page"); os.makedirs(OUT, exist_ok=True)
LTLA = os.environ.get("LTLA", "/home/claude/hist/how-roman-is-your-road/data/ons/ltla.geojson")
NE = os.environ.get("NE_COUNTRIES", "/home/claude/hist/_data3/ne/geojson/ne_10m_admin_0_countries.geojson")
d = pd.read_pickle(os.path.join(ROOT, "work", "tagged.pkl.gz"))
KI = {k: i for i, k in enumerate(E.KEYS)}
NATS = ["E", "W", "S", "NI", "ROI"]
MAJOR = {"London", "Birmingham", "Manchester", "Glasgow", "Edinburgh", "Cardiff", "Belfast", "Leeds", "Newcastle upon Tyne", "Bristol", "Liverpool",
         "Sheffield", "Aberdeen", "Inverness", "Norwich", "Plymouth", "Southampton", "Nottingham", "Leicester", "York", "Dundee", "Swansea", "Hull",
         "Carlisle", "Exeter", "Cambridge", "Oxford", "Lincoln", "Dublin", "Cork", "Limerick", "Galway", "Waterford", "Londonderry", "Kilkenny", "Sligo"}
IE_TOWNS = {"Dublin": 4, "Cork": 4, "Limerick": 4, "Galway": 4, "Waterford": 4, "Kilkenny": 3, "Sligo": 3, "Drogheda": 3, "Dundalk": 3, "Athlone": 3, "Ennis": 3,
            "Tralee": 3, "Wexford": 3, "Letterkenny": 3, "Castlebar": 3, "Mullingar": 3, "Navan": 3, "Carlow": 3, "Tullamore": 3, "Killarney": 3, "Clonmel": 3,
            "Belfast": 4, "Londonderry": 4, "Lisburn": 3, "Newry": 3, "Armagh": 3, "Enniskillen": 3, "Omagh": 3, "Coleraine": 3, "Ballymena": 3, "Bangor": 3,
            "Portadown": 3, "Newtownards": 3, "Craigavon": 3, "Dungannon": 3, "Larne": 3, "Downpatrick": 3, "Letterkenny": 3}
def rank(r):
    if r.nation in ("E", "W", "S"):
        base = {"City": 4, "Town": 3, "Village": 1, "Hamlet": 0, "Other Settlement": 0, "Suburban Area": 0}[r.kind]
    elif r.layer == "townland": base = 0
    else: base = IE_TOWNS.get(r.name, 1)
    return 5 if (r.name in MAJOR and base >= 3) else base
KIND = sorted(d.kind.unique()); KIDX = {k: i for i, k in enumerate(KIND)}
AREA = sorted(d.area.unique()); AIDX = {k: i for i, k in enumerate(AREA)}

def pack(df):
    return dict(n=df.name.tolist(), a=df.alt.tolist(), la=(df.lat * 1e4).round().astype(int).tolist(), lo=(df.lon * 1e4).round().astype(int).tolist(),
                k=df.kind.map(KIDX).tolist(), na=df.nation.map(NATS.index).tolist(), ar=df.area.map(AIDX).tolist(),
                r=[rank(r) for r in df.itertuples()], e=[[KI[k] for k in e] for e in df.el])
S = d[d.layer == "settlement"]; T = d[d.layer == "townland"]
json.dump(dict(kinds=KIND, areas=AREA, **pack(S)), open(os.path.join(OUT, "settlements.json"), "w"), separators=(",", ":"), ensure_ascii=False)
json.dump(dict(kinds=KIND, areas=AREA, **pack(T)), open(os.path.join(OUT, "townlands.json"), "w"), separators=(",", ":"), ensure_ascii=False)

c = pd.read_csv(os.path.join(ROOT, "data", "cells.csv"), keep_default_na=False)
cells = {}
for (g, lay), h in c.groupby(["grid", "layer"]):
    rows = []
    for x in h.itertuples():
        ec = []
        if x.elements:
            for kv in x.elements.split(";"):
                k, v = kv.split(":"); ec += [KI[k], int(v)]
        rows.append([x.ci, x.cj, x.n, x.n_tagged, [getattr(x, "fam_" + f) for f in E.FAM_ORDER], ec])
    cells[f"{g}_{lay}"] = rows
json.dump(dict(steps={"fine": [0.15, 0.25], "coarse": [0.3, 0.5]}, cells=cells), open(os.path.join(OUT, "cells.json"), "w"), separators=(",", ":"))

# outlines: nations of the UK from ONS districts, Ireland from Natural Earth
def rnd(geom, tol):
    g = shapely.simplify(geom, tol, preserve_topology=True)
    return shapely.set_precision(g, 0.0001)
lj = json.load(open(LTLA)); parts = {"E": [], "W": [], "S": [], "N": []}
for f in lj["features"]:
    p = f["properties"]
    if p.get("end") is None: parts[p["areacd"][0]].append(shapely.make_valid(shape(f["geometry"])).buffer(0))
nat = {k: unary_union(v) for k, v in parts.items()}
ne = json.load(open(NE)); irl = [shape(f["geometry"]) for f in ne["features"] if f["properties"]["ADM0_A3"] == "IRL"][0]
land = unary_union([*nat.values(), irl])
borders = unary_union([nat["E"].boundary.intersection(nat["W"].buffer(0.002)), nat["E"].boundary.intersection(nat["S"].buffer(0.002)),
                       nat["N"].boundary.intersection(irl.buffer(0.01))])
out = dict(land=mapping(rnd(land, 0.004)), borders=mapping(rnd(borders, 0.002)))
json.dump(out, open(os.path.join(OUT, "outline.json"), "w"), separators=(",", ":"))
for f in os.listdir(OUT): print(f, os.path.getsize(os.path.join(OUT, f)))
