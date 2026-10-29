"""Place-name elements: the spelling rules used to tag settlement and townland names.

Each rule is matched against the tokens of a name (split on spaces and hyphens, accents and
apostrophes removed, qualifier words such as Upper, Little, North and Saint dropped).
A name can carry several elements (Birmingham: -ing and -ham). A match means only that the
spelling fits; it is not an etymology. Meanings are the standard, widely agreed readings of
each element, hedged where one spelling covers several words.

Rule fields
  key, label   identifier and display label
  fam          language family: english, norse, latin, brittonic, goidelic
  rx           regular expression that must match a whole token
  where        nations where the rule applies (E, W, S, NI, ROI); others are never tagged
  counties     optional set of areas the rule is limited to (within those nations)
  exclude      tokens never tagged
  meaning      short gloss shown on the page
Run python3 code/elements.py to run the tests.
"""
import re, unicodedata

GB = {"E", "W", "S"}
IRL = {"NI", "ROI"}
ALL = GB | IRL
GAEL = {"S", "NI", "ROI"}
CORNWALL = {"Cornwall", "Isles of Scilly", "Devon"}  # Cornish rules also run in Devon, to see where they stop
NORTHERN_ISLES = {"Shetland Islands", "Orkney Islands", "Na h-Eileanan an Iar", "Highland"}

FAMILIES = {
    "english": "English",
    "norse": "Norse",
    "latin": "Latin (via English or Welsh)",
    "brittonic": "Brittonic (Welsh, Cornish, Cumbric, Pictish)",
    "goidelic": "Gaelic (Irish and Scottish)",
}
FAM_ORDER = ["english", "norse", "latin", "brittonic", "goidelic"]

def R(key, label, fam, rx, meaning, where=ALL, counties=None, not_counties=None, exclude=(), group=None, cnation=None):
    return dict(cnation=cnation, key=key, label=label, fam=fam, rx=re.compile(rx), meaning=meaning, where=set(where),
                counties=set(counties) if counties else None, not_counties=set(not_counties) if not_counties else None,
                exclude=set(exclude), group=group or fam)

EN_WORDS = {"spring", "springs", "king", "kings", "ring", "wing", "swing", "string", "building", "buildings", "landing",
            "crossing", "siding", "sidings", "wharfing", "living", "morning", "evening", "farthing", "shilling", "sterling",
            "bowling", "riding", "ridings", "viking", "pudding", "lodging", "clearing", "opening", "fishing", "mining",
            "dwelling", "steading", "hanging", "canning", "bring", "sling", "thing", "nothing", "sing", "ping", "ling", "spelling", "skating", "parking", "nursing"}

RULES = [
    # ---------- English (Old English and later) ----------
    R("ton", "-ton", "english", r"[a-z]{2,}tons?", "farmstead, estate, later village (Old English tun). Some -ston names are stan, stone", where=ALL,
      exclude={"cotton", "button", "mutton", "glutton", "wanton", "canton", "piston"}),
    R("town", "-town", "english", r"[a-z]*towns?|newtown[a-z]+", "town, farm or settlement (later English town, from Old English tun)", where=ALL),
    R("ham", "-ham", "english", r"[a-z]{2,}hams?", "homestead, village (Old English ham); some are hamm, land in a river bend, which the spelling cannot separate",
      where=GB, exclude={"graham", "abraham", "gotham"}),
    R("ing", "-ing / -ings", "english", r"[a-z]{3,}ings?|[a-z]{2,}ing(ham|ton|tons|ford|ley|den|field|worth|hurst|don|wick|bury|borough|stead|ham)s?", "the people of, or place of (Old English -ingas, -ing)", where=GB,
      exclude=EN_WORDS),
    R("ley", "-ley / -leigh", "english", r"[a-z]{2,}(ley|leigh|leys)|leigh", "woodland clearing, later meadow (Old English leah)", where=GB,
      exclude={"valley", "trolley", "alley", "volley", "barley", "galley", "medley", "motley", "parsley", "jockey"}),
    R("worth", "-worth", "english", r"[a-z]{2,}(worth|worthy|wardine)", "enclosure, enclosed farmstead (Old English worth)", where=GB),
    R("bury", "-bury / -borough", "english", r"[a-z]{2,}(bury|borough|brough|burgh|borrow)", "fortified place, later manor or town (Old English burh); some -borough names are beorg, hill",
      where=GB, exclude={"edinburgh"}),
    R("field", "-field", "english", r"[a-z]{2,}fields?", "open land, cleared country (Old English feld)", where=GB),
    R("ford", "-ford", "english", r"[a-z]{2,}fords?", "ford, a river crossing (Old English ford)", where=GB, not_counties=None),
    R("stead", "-stead", "english", r"[a-z]{2,}ste(a)?d", "place, site, farm (Old English stede)", where={"E"}),
    R("hurst", "-hurst", "english", r"[a-z]{2,}hurst", "wooded hill (Old English hyrst)", where={"E", "W"}),
    R("den", "-den / -dean", "english", r"[a-z]{3,}(den|dean|dene)", "valley (denu) or woodland pasture for pigs (denn), Old English", where={"E"},
      exclude={"garden", "golden", "hidden", "sudden", "linden", "warden", "harden", "wooden"}),
    R("don", "-don", "english", r"[a-z]{3,}don", "hill (Old English dun)", where={"E"}),
    R("cot", "-cote / -cott", "english", r"[a-z]{2,}(cote|cotes|cot|cott|cotts|coat|coats)", "cottage, hut, shelter (Old English cot)", where=GB,
      exclude={"apricot", "ascot"}),
    R("stow", "-stow", "english", r"[a-z]{2,}stowe?|stowe?", "place, often a holy place or meeting place (Old English stow)", where=GB),
    R("minster", "-minster", "english", r"[a-z]*minster", "monastery or major church (Old English mynster)", where=GB),
    R("wick", "-wick / -wich", "english", r"[a-z]{2,}(wick|wich|wych)", "specialised farm (often a dairy farm) or trading place (Old English wic, from Latin vicus)",
      where=GB, not_counties=NORTHERN_ISLES, exclude={"sandwich"}),
    # ---------- Latin, through Old English or Welsh ----------
    R("chester", "-chester / -caster", "latin", r"[a-z]*(chester|caster|cester|caister|xeter|chesters)|caister|chester",
      "Old English ceaster, a Roman fort or town (from Latin castra)", where=GB, counties=None),
    R("strat", "strat- / stret-", "latin", r"(strat|stret|streat)(?!h)[a-z]+", "Old English straet, a paved road, often Roman (from Latin strata)", where={"E", "W"}),
    R("eccles", "eccles-", "latin", r"eccles[a-z]*|egglest[a-z]*", "church, from Brittonic, from Latin ecclesia", where=GB),
    R("pont", "pont-", "latin", r"pont[a-z]{2,}", "bridge (Welsh pont, from Latin pons)", where={"W"}),
    # ---------- Norse ----------
    R("by", "-by", "norse", r"[a-z]{2,}by|[a-z]{3,}bie", "farmstead, village (Old Norse byr)", where={"E", "S"},
      exclude={"tenby", "abby", "hobby", "lobby", "rugby_"}),
    R("thorpe", "-thorpe", "norse", r"[a-z]*thorpe?s?|[a-z]*throp", "outlying farm (Old Norse thorp; a few are Old English throp)", where=GB),
    R("thwaite", "-thwaite", "norse", r"[a-z]*thwaites?|[a-z]*thwait", "clearing, meadow (Old Norse thveit)", where=GB),
    R("toft", "-toft", "norse", r"[a-z]*tofts?", "site of a house, homestead (Old Norse topt)", where=GB),
    R("holme", "-holme / -holm", "norse", r"[a-z]*(holme|hulme|holm)s?", "island, dry ground in marsh, water meadow (Old Norse holmr)", where=GB),
    R("kirk", "kirk-", "norse", r"kirk[a-z]*|[a-z]+kirk", "church (Old Norse kirkja). Counted in England only, because Scots kirk is an everyday word", where={"E"}, exclude={"dunkirk"}),
    R("scale", "-scale(s)", "norse", r"[a-z]*scales?|[a-z]*skaill", "hut, shieling (Old Norse skali)", where=GB, exclude={"scale", "scales"}),
    R("setter", "-setter / -bister", "norse", r"[a-z]*(setter|bister|busta|ster)", "dwelling, farm (Old Norse setr, bolstadr)", where={"S"},
      counties=NORTHERN_ISLES, exclude={"easter", "wester", "lister", "webster", "dempster", "chester", "minster"}),
    R("vik", "-wick (bay)", "norse", r"[a-z]{2,}(wick|vaig|bhaig)", "bay (Old Norse vik)", where={"S"}, counties=NORTHERN_ISLES),
    # ---------- Brittonic ----------
    R("aber", "aber-", "brittonic", r"aber[a-z]{2,}", "river mouth or confluence (Brittonic aber)", where=GB),
    R("llan", "llan-", "brittonic", r"llan[a-z]+", "church enclosure, church (Welsh llan)", where={"W", "E"}),
    R("pen", "pen-", "brittonic", r"pen[a-z]{2,}", "head, top, end (Brittonic penn)", where={"W", "E"},
      exclude={"penny", "pennington", "penton", "pentonville", "pends", "pennsylvania"}),
    R("tre", "tre- / tref-", "brittonic", r"tre[a-z]{3,}", "farmstead, settlement (Welsh tref, Cornish tre)", where={"W", "E"},
      counties=CORNWALL | {"Devon", "Isle of Anglesey", "Gwynedd", "Conwy", "Denbighshire", "Flintshire", "Wrexham", "Powys", "Ceredigion",
                           "Pembrokeshire", "Carmarthenshire", "Swansea", "Neath Port Talbot", "Bridgend", "Vale of Glamorgan", "Cardiff",
                           "Rhondda Cynon Taf", "Merthyr Tydfil", "Caerphilly", "Blaenau Gwent", "Torfaen", "Monmouthshire", "Newport"}, cnation="E",
      exclude={"trent", "trench", "treetops", "treeton", "trentham", "trees", "treacle"}),
    R("caer", "caer- / car-", "brittonic", r"caer[a-z]{2,}|caerau|cardiff", "fort (Brittonic caer)", where={"W"}),
    R("cwm", "cwm-", "brittonic", r"cwm[a-z]*", "valley (Welsh cwm)", where={"W"}),
    R("bryn", "bryn-", "brittonic", r"bryn[a-z]*", "hill (Welsh bryn)", where={"W"}),
    R("nant", "nant-", "brittonic", r"nant[a-z]*", "stream, stream valley (Welsh nant)", where={"W"}),
    R("rhyd", "rhyd-", "brittonic", r"rhyd[a-z]*", "ford (Welsh rhyd)", where={"W"}),
    R("maes", "maes-", "brittonic", r"maes[a-z]*", "open field (Welsh maes)", where={"W"}),
    R("betws", "betws", "brittonic", r"betws[a-z]*", "chapel, prayer house (Welsh betws, from Old English bedhus)", where={"W"}),
    R("pol", "pol-", "brittonic", r"pol[a-z]{2,}", "pool, cove (Cornish pol)", where={"E"}, counties=CORNWALL),
    R("porth", "porth-", "brittonic", r"porth[a-z]*|port[a-z]{3,}", "cove, landing place (Cornish porth)", where={"E"}, counties=CORNWALL),
    R("bos", "bos-", "brittonic", r"bos[a-z]{2,}", "dwelling (Cornish bod, bos)", where={"E"}, counties=CORNWALL),
    R("lan", "lan-", "brittonic", r"lan(?!g)[a-z]{3,}", "church enclosure (Cornish lann)", where={"E"}, counties=CORNWALL, exclude={"lane", "lanes"}),
    R("ros", "ros-", "brittonic", r"ros[a-z]{2,}", "heath, promontory (Cornish ros)", where={"E"}, counties=CORNWALL),
    R("pit", "pit-", "brittonic", r"pit[a-z]{3,}", "a portion of land, farm (Pictish pett)", where={"S"}, exclude={"pitch", "pitts"}),
    # ---------- Gaelic (Goidelic) ----------
    R("bal", "bally- / bal-", "goidelic", r"bal{1,2}[aiy][a-z]{2,}|bal[a-z]{3,}", "baile: farm, homestead, settlement. In Irish names Bally- can also be beal atha, ford mouth",
      where=GAEL, exclude={"ballast", "ballroom"}),
    R("kil", "kil- / kill-", "goidelic", r"kil[a-z]{3,}", "cill: church. Kil- can also be coill, wood, and other words", where=GAEL),
    R("inver", "inver-", "goidelic", r"inver[a-z]{2,}|inner[a-z]{3,}", "inbhir: river mouth or confluence", where=GAEL, exclude={"innerleithen_"}),
    R("dun", "dun- / dum-", "goidelic", r"dun[a-z]{2,}|dum[a-z]{3,}|don[a-z]{3,}", "dun: fort, stronghold. Irish Don- is often domhnach, church", where=GAEL,
      exclude={"dunnet_"}),
    R("strath", "strath-", "goidelic", r"strath[a-z]*", "srath: broad river valley", where={"S"}),
    R("auch", "auch- / agha-", "goidelic", r"(auch|ach|agha|augh|aha)[a-z]{2,}", "achadh: field", where=GAEL),
    R("glen", "glen-", "goidelic", r"glen[a-z]*|glin[a-z]+", "gleann: glen, valley", where=GAEL),
    R("knock", "knock-", "goidelic", r"knock[a-z]*|cnoc[a-z]*", "cnoc: hill", where=GAEL),
    R("drum", "drum- / drom-", "goidelic", r"(drum|drom|drim)[a-z]*", "druim: ridge", where=GAEL),
    R("ard", "ard-", "goidelic", r"ard[a-z]{2,}", "ard: height, high place, promontory", where=GAEL, exclude={"ardent"}),
    R("kin", "kin- / ken-", "goidelic", r"(kin|ken)(?!gs|gst)[a-z]{3,}", "ceann: head, end", where=GAEL, exclude={"kingston", "kings", "kingsland", "kingswood", "kingsmills", "kingscourt", "kinsley"}),
    R("carrick", "carrick- / carrig-", "goidelic", r"carri(ck|g)[a-z]*|carrag[a-z]*", "carraig: rock", where=GAEL),
    R("clon", "clon- / cloon-", "goidelic", r"(clon|cloon|cluan)[a-z]*", "cluain: meadow, pasture", where=IRL),
    R("rath", "rath-", "goidelic", r"rath[a-z]*|ra[a-z]{0}", "rath: ringfort", where=IRL),
    R("lis", "lis-", "goidelic", r"lis[a-z]{2,}|liss[a-z]*", "lios: ringfort, enclosure", where=IRL),
    R("tully", "tully- / tulla-", "goidelic", r"tull[aoy][a-z]*|tulli[a-z]+", "tulach: low hill, mound", where=IRL),
    R("derry", "derry-", "goidelic", r"(derry|derri|dirry|dery)[a-z]*|derr[a-z]{2,}", "doire: oak wood", where=IRL),
    R("inis", "ennis- / inish-", "goidelic", r"(ennis|inis|inish|innis|inch)[a-z]*", "inis: island, river meadow", where=GAEL),
    R("mullagh", "mullagh-", "goidelic", r"mullagh[a-z]*|mulla[a-z]+", "mullach: summit", where=IRL),
    R("bel", "bel- / bella-", "goidelic", r"(bel|bella)(?!ir|mont|view|grove|ville|field|lev|lg|lv|lm|lh|ls|lw|lf)[a-z]{3,}", "beal: mouth, approach (often to a ford)", where=IRL, exclude={"bellevue", "belmont", "belview", "belgrove", "belvedere"}),
]
# the "rath" alt pattern ra[a-z]{0} is a no-op guard; keep the plain rath rule
RULES = [r for r in RULES]
BY_KEY = {r["key"]: r for r in RULES}
KEYS = [r["key"] for r in RULES]

QUALIFIERS = {"upper", "lower", "nether", "great", "little", "north", "south", "east", "west", "old", "new", "mid", "middle", "high",
              "long", "st", "saint", "easter", "wester", "over", "far", "near", "the", "le", "la", "on", "upon", "in", "under", "by",
              "and", "of", "cum", "next", "sea", "bishops", "kings", "monks", "abbots", "church", "chapel", "market", "royal", "regis",
              "magna", "parva", "superior", "inferior", "glebe", "demesne", "beg", "more", "mor", "bheag", "mhor", "uachdarach",
              "iochdarach", "isaf", "uchaf", "fawr", "fach", "bach", "mawr", "td", "ed", "a", "an", "y", "yr", "na", "nan", "na",
              "isle", "island", "bridge", "green", "end", "street", "common", "heath", "moor", "hill", "wood", "park", "farm", "estate",
              "village", "hamlet", "cross", "hall", "house", "lodge", "mill", "mills", "gate", "row", "bank", "side", "top", "head", "foot",
              "bay", "port", "harbour", "station", "junction", "quay", "lane"}

def fold(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    s = s.replace("'", "").replace("’", "").replace(".", " ").replace(",", " ").replace("(", " ").replace(")", " ")
    return s

def tokens(name):
    t = [w for w in re.split(r"[\s\-/]+", fold(name)) if w]
    core = [w for w in t if w not in QUALIFIERS and not w.isdigit()]
    return core or t

def elements(name, nation, county=""):
    """Return the list of element keys whose rule matches any token of the name."""
    toks = tokens(name)
    out = []
    for r in RULES:
        if nation not in r["where"]:
            continue
        if r["counties"] is not None and (r["cnation"] is None or r["cnation"] == nation) and county not in r["counties"]:
            continue
        if r["not_counties"] is not None and county in r["not_counties"]:
            continue
        for w in toks:
            if w in r["exclude"]:
                continue
            if r["rx"].fullmatch(w):
                out.append(r["key"]); break
    # one spelling, one element: resolve known overlaps
    s = set(out)
    if "vik" in s: s.discard("wick")
    if "chester" in s: s.discard("setter")
    if "town" in s: s.discard("ton")
    if "inver" in s and any(w.startswith("inner") for w in toks) and nation != "S": s.discard("inver")
    return [k for k in KEYS if k in s]

TESTS = [
    ("Birmingham", "E", "", {"ing", "ham"}), ("Kirkby Lonsdale", "E", "", {"kirk", "by"}), ("Scunthorpe", "E", "", {"thorpe"}),
    ("Tenby", "W", "", set()), ("Llanfair Caereinion", "W", "", {"llan", "caer"}), ("Aberystwyth", "W", "", {"aber"}),
    ("Aberdeen", "S", "", {"aber"}), ("Inverness", "S", "", {"inver"}), ("Pitlochry", "S", "", {"pit"}),
    ("Ballymena", "NI", "", {"bal"}), ("Kilkenny", "ROI", "", {"kil", "kin"} - {"kin"}), ("Lerwick", "S", "Shetland Islands", {"vik"}),
    ("Berwick-upon-Tweed", "E", "", {"wick"}), ("Manchester", "E", "", {"chester"}), ("Stratford-upon-Avon", "E", "", {"strat", "ford"}),
    ("Strathaven", "S", "", {"strath"}), ("Truro", "E", "Cornwall", set()), ("Tregony", "E", "Cornwall", {"tre"}),
    ("Polperro", "E", "Cornwall", {"pol"}), ("Spring Gardens", "E", "", set()), ("Reading", "E", "", {"ing"}),
    ("Lockerbie", "S", "", {"by"}), ("Newtownards", "NI", "", {"town"}), ("Ardee", "ROI", "", {"ard"}),
    ("Drumcondra", "ROI", "", {"drum"}), ("Lisburn", "NI", "", {"lis"}), ("Derrylin", "NI", "", {"derry"}),
]

if __name__ == "__main__":
    bad = 0
    for name, nation, county, want in TESTS:
        got = set(elements(name, nation, county))
        if got != want:
            bad += 1; print("FAIL", name, "got", sorted(got), "want", sorted(want))
    print(len(RULES), "rules;", len(TESTS) - bad, "of", len(TESTS), "tests pass")

def matches_any(name, keys):
    """True if any of the given rules matches a token, ignoring the rules' geographic limits
    (used for the border profiles, where the point is to see how far a spelling reaches)."""
    toks = tokens(name)
    for k in keys:
        r = BY_KEY[k]
        if any(w not in r["exclude"] and r["rx"].fullmatch(w) for w in toks):
            return True
    return False
