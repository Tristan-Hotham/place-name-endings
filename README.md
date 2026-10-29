# What is your town's name made of? Place-name elements of Britain and Ireland

Every settlement in Britain and Ireland, and every Irish townland, 105,532 names in all, tagged by the old words inside them: English -ton, -ham and -ley, Norse -by and -thorpe, Latin -chester, Welsh llan- and aber-, Cornish tre- and pol-, Pictish pit-, Gaelic bally-, kil- and inver-. The interactive page maps each language family and each of 67 elements, and lets you look up any town, village or townland.

**Interactive version:** https://maps.tristanhotham.com/place-name-endings/

**Paper and archived release:** https://doi.org/10.5281/zenodo.23761433

**Blog post:** https://blog.tristanhotham.com/2026/10/29/place-name-endings/

A data study by Dr Tristan Hotham (Independent researcher, ORCID 0000-0003-4931-9349).

## Headline results

- 45,632 settlements (43,274 in Great Britain, 2,358 in Ireland) and 59,900 Irish townlands. 43% of settlements and 44% of townlands carry at least one of the 67 elements.
- The commonest element is the English -ton: 5,949 settlements, 16% of all those in England. Among townlands, Bally- leads (6,282, 10%).
- Settlements with -chester or -caster (Old English ceaster, from Latin castra) are towns or cities 33% of the time, against 3.3% for all settlements in Great Britain.
- The Welsh border is sharp: 20 to 40 km inside Wales 31% of settlements have a Welsh element, against 0.5% at the same distance inside England; 73 English settlements within 60 km have Welsh spellings.
- Cornish elements mark 27% of Cornwall's settlements and 1.4% of Devon's (mostly false friends) with the same rules.
- Scotland: 22 aber- and 54 inver- settlements; 20 of the abers and 21 of 25 Pictish pit- names lie east of 4 degrees west.
- Official Irish forms (Republic of Ireland, 37,175 names) test what anglicised spellings stand for: Knock- is cnoc in 99% of cases and Bally- is baile in 90%, but Kil- is cill (church) in only 68% and coill (wood) in 30%, rising to 95 of 105 Kil- townlands in Monaghan.
- The English -town ends 35% of townland names in Meath, 26% in Dublin and 25% in Kildare, the medieval Pale.

Every number is in `data/results.json`, which the page, paper, blog and collage are built from.

## Files

| Path | What it is |
|---|---|
| `index.html` | The interactive page (results embedded; map data loaded from `data/page/`). |
| `header.png` | Social card (1200 by 630). |
| `data/names_tagged.csv.gz` | Every name: name, alternative (Welsh, Gaelic or official Irish) form, kind, layer (settlement or townland), nation, area, latitude, longitude, source, elements and families. |
| `data/elements.csv` | The 67 elements: label, family, gloss and counts by nation, for settlements and townlands. |
| `data/areas.csv` | Counts by county, council or unitary area: names, tagged names, names in each family, commonest elements. |
| `data/cells.csv` | Counts by grid cell (0.15 by 0.25 and 0.3 by 0.5 degrees), for settlements and townlands. |
| `data/irish_forms.csv` | For each Gaelic beginning, Republic of Ireland names with an official Irish form and how many begin with the expected Irish word. |
| `data/results.json` | Every number used anywhere, including the spelling-check samples. |
| `data/page/` | Compact files for the page (`settlements.json`, `townlands.json`, `cells.json`, `outline.json`). |
| `code/elements.py` | The rules, with tests (`python3 code/elements.py`). |
| `code/01_prepare.py` to `code/08_release.py` | The pipeline, run in order (below). `code/shots.js` makes test screenshots with Playwright. |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |
| `release/` | Paper PDF and source, blog post and figures, Zenodo files. |

## Method in brief

- **Names.** Great Britain: the 43,274 populated places in OS Open Names. Northern Ireland: the 336 towns and villages of the OSNI gazetteer and 9,520 OSNI townlands (centroids). Republic of Ireland: the 2,022 centres of population and 50,380 townlands of Tailte Éireann's National Placenames Gazetteer, with official Irish forms. Townlands are counted separately from settlements.
- **Rules.** Names are split into words (qualifiers such as Upper and Little dropped) and each word is matched against regular expressions for each element. Some rules only run where the language was spoken (no Gaelic rules in England or Wales; Kirk- as Norse only in England; Cornish rules in Cornwall, Scilly and Devon). A name can carry several elements.
- **Border profiles.** Distance from the England and Wales land border (ONS boundaries) and longitude bands across Cornwall and Devon, with the Welsh or Cornish rules applied on both sides.
- **Irish forms.** First word of the official Irish form (article and initial mutations removed) compared with the expected Irish word.
- **Spelling check.** 280 random matches for 14 elements read through for plain false friends during the analysis: 9 found.

## Known limits

- A spelling is not an etymology: the tags are first guesses, and the glosses are the commonly given meanings, not checked name by name.
- The sources differ: Great Britain's list includes hamlets and suburbs; the Irish town lists hold only larger places (Northern Ireland's dates from 2015). Compare shares, and use the townland layer for Ireland.
- Modern spellings can hide or fake an element; newer names (Newtown, Mount Pleasant) count as English. Nothing here dates a name.
- Official Irish forms exist in this data for the Republic only.

## How to rerun

Inputs are read in place (paths at the top of each script, or environment variables): `osnames_gb.tsv` (an extract of OS Open Names), the two browser-fetched bundles `pne_ireland_gazetteer.json.gz` and `pne_ni_osni.json.gz` in `RAW_DIR`, ONS district boundaries (`LTLA`) and Natural Earth countries (`NE_COUNTRIES`).

```
python3 code/elements.py      # tests
python3 code/01_prepare.py
python3 code/02_analyse.py
python3 code/03_audit.py
python3 code/04_page_data.py
python3 code/05_build_site.py
FONT_DIR=path/to/fonts python3 code/06_figures.py
python3 code/07_paper.py
python3 code/08_release.py
```

Needs Python 3 with numpy, pandas, shapely, pyproj and matplotlib, and xelatex with TeX Gyre Pagella and Inter for the paper.

## Sources and licences

- **Great Britain:** OS Open Names, Ordnance Survey. Contains OS data © Crown copyright and database right 2026. Open Government Licence v3.0.
- **Northern Ireland:** OSNI Open Data Gazetteer Place Names and Largescale Boundaries Townlands, Land and Property Services. Contains public sector information licensed under the Open Government Licence v3.0. Townland centroids were read from a hosted copy of the OSNI layer.
- **Republic of Ireland:** National Placenames Gazetteer (Centres of Population; Townlands), © Tailte Éireann, CC BY 4.0. Retrieved 2026-10-29.
- **Boundaries:** Office for National Statistics local authority districts (OGL v3.0); Natural Earth (public domain).
- **Map tiles on the page:** Esri.

Code: MIT (see `LICENSE`). Data and text: CC BY 4.0; please keep the source credits above when reusing.

## Citation

Hotham, T. (2026) *What Is Your Town's Name Made Of? A Spelling-Based Atlas of Place-Name Elements in Britain and Ireland*. Zenodo. https://doi.org/10.5281/zenodo.23761433

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
