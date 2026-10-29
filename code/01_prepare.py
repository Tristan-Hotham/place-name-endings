"""Step 1: one table of settlement and townland names for Britain and Ireland.

Inputs (read in place; paths at the top or from environment variables):
  OSNAMES  OS Open Names extract for Great Britain (tab separated; populated places are used)
  RAW_DIR  the two bundles fetched in the browser on 2026-10-29:
           pne_ireland_gazetteer.json.gz  Tailte Eireann National Placenames Gazetteer:
                                          Centres of Population and Townlands (CC BY 4.0)
           pne_ni_osni.json.gz            OSNI Open Data Gazetteer Place Names (336 towns and villages)
                                          and OSNI Largescale Boundaries Townlands (centroids), OGL v3.0
  LTLA     ONS local authority districts (to give Northern Ireland places a district)
Output: work/names.csv.gz (one row per name), work/prep_meta.json
"""
import gzip, json, os
import numpy as np, pandas as pd
from pyproj import Transformer
import shapely
from shapely.geometry import shape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("RAW_DIR", "/home/claude/hist/_data18/place-name-endings")
OSN = os.environ.get("OSNAMES", "/home/claude/hist/osnames_gb.tsv")
LTLA = os.environ.get("LTLA", "/home/claude/hist/how-roman-is-your-road/data/ons/ltla.geojson")
WORK = os.path.join(ROOT, "work"); os.makedirs(WORK, exist_ok=True)

# ---------- Great Britain: OS Open Names populated places ----------
g = pd.read_csv(OSN, sep="\t", dtype=str, keep_default_na=False)
g = g[g.type == "populatedPlace"].copy()
# English (or unmarked) form as the main name; the Welsh or Gaelic form as the alternative
swap = g.lang1.isin(["cym", "gla"]) & (g.lang2 == "eng")
g["name"] = np.where(swap, g.name2, g.name1)
g["alt"] = np.where(swap, g.name1, np.where(g.lang2.isin(["cym", "gla"]), g.name2, ""))
g["alt_lang"] = np.where(swap, g.lang1, np.where(g.lang2.isin(["cym", "gla"]), g.lang2, ""))
g["nation"] = g.country.map({"England": "E", "Wales": "W", "Scotland": "S"})
g["area"] = np.where(g.county != "", g.county, g.district)
# Welsh areas are given as "Welsh - English" (Sir Benfro - Pembrokeshire): keep the English form
g["area"] = g.area.str.split(" - ").str[-1].str.replace(r"^the ", "", regex=True)
gb = pd.DataFrame(dict(name=g.name, alt=g.alt, alt_lang=g.alt_lang, kind=g.local_type, layer="settlement",
                       nation=g.nation, area=g.area, region=g.region, lat=g.lat.astype(float), lon=g.lon.astype(float),
                       src="OS Open Names"))
print("GB populated places", len(gb), gb.kind.value_counts().to_dict())

# ---------- Republic of Ireland: Tailte Eireann gazetteer ----------
ie = json.load(gzip.open(os.path.join(RAW, "pne_ireland_gazetteer.json.gz")))
itm = Transformer.from_crs(2157, 4326, always_xy=True)
def ie_frame(part, kind, layer):
    d = pd.DataFrame(ie[part]["rows"], columns=ie[part]["cols"])
    lon, lat = itm.transform(d.ITM_E.astype(float).values, d.ITM_N.astype(float).values)
    return pd.DataFrame(dict(name=d.English_Na.str.strip(), alt=d.Irish_Name.str.strip(), alt_lang=np.where(d.Irish_Name.str.strip() != "", "gle", ""),
                             kind=kind, layer=layer, nation="ROI", area=d.County.str.title(), region="Republic of Ireland",
                             lat=lat, lon=lon, src="Tailte Eireann gazetteer", gaeltacht=d.Gaeltacht))
cop = ie_frame("cop", "Centre of population", "settlement")
tl = ie_frame("tl", "Townland", "townland")
# townland names are in capitals in the source: title case them for display
tl["name"] = tl.name.str.title().str.replace(r"'S\b", "'s", regex=True)
print("ROI centres of population", len(cop), "townlands", len(tl), "with Irish form", int((tl.alt != "").sum()))

# ---------- Northern Ireland: OSNI ----------
ni = json.load(gzip.open(os.path.join(RAW, "pne_ni_osni.json.gz")))
npl = pd.DataFrame(ni["places"]["rows"], columns=ni["places"]["cols"])
ntl = pd.DataFrame(ni["townlands"]["rows"], columns=ni["townlands"]["cols"])
nip = pd.DataFrame(dict(name=npl.name.str.title(), alt="", alt_lang="", kind="Town or village", layer="settlement", nation="NI",
                        area="", region="Northern Ireland", lat=npl.lat, lon=npl.lon, src="OSNI gazetteer"))
nit = pd.DataFrame(dict(name=ntl.name.str.title().str.replace(r"'S\b", "'s", regex=True), alt="", alt_lang="", kind="Townland", layer="townland", nation="NI",
                        area="", region="Northern Ireland", lat=ntl.lat, lon=ntl.lon, src="OSNI townlands"))
nn = pd.concat([nip, nit], ignore_index=True)
# district from ONS boundaries (current Northern Ireland councils)
lj = json.load(open(LTLA))
polys, names = [], []
for f in lj["features"]:
    p = f["properties"]
    if p.get("end") is not None or not p["areacd"].startswith("N"): continue
    polys.append(shape(f["geometry"])); names.append(p["areanm"])
tree = shapely.STRtree(polys)
pts = shapely.points(nn.lon.values, nn.lat.values)
near = tree.query_nearest(pts)
nn["area"] = np.array(names)[near[1]]
print("NI places", len(nip), "townlands", len(nit))

allp = pd.concat([gb, cop, tl, nn], ignore_index=True)
allp["gaeltacht"] = allp.get("gaeltacht", pd.Series(dtype=str)).fillna("")
allp = allp[allp.name.str.strip() != ""].reset_index(drop=True)
allp["lat"] = allp.lat.round(5); allp["lon"] = allp.lon.round(5)
allp.to_csv(os.path.join(WORK, "names.csv.gz"), index=False, compression="gzip")
meta = dict(gb_n=len(gb), roi_cop_n=len(cop), roi_townlands_n=len(tl), roi_townlands_irish=int((tl.alt != "").sum()),
            ni_places_n=len(nip), ni_townlands_n=len(nit), ie_retrieved=ie["retrieved"], ni_retrieved=ni["retrieved"],
            gb_kinds=gb.kind.value_counts().to_dict())
json.dump(meta, open(os.path.join(WORK, "prep_meta.json"), "w"), indent=1)
print(meta)
