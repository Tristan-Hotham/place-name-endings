"""Step 3: spelling check on random samples of matches (recorded verdicts).

For 14 common elements, 20 settlement names were drawn at random (seed 7) and read through
for obvious false friends: a name where the letters fit the rule but the element is plainly
something else (a modern word, a personal name, a word from another language). This checks the
spelling rules only. It is not an etymological check: a name passing here may still have a
different origin, which only a place-name dictionary can settle.
Writes the audit into data/results.json.
"""
import json, os, random
import pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = pd.read_pickle(os.path.join(ROOT, "work", "tagged.pkl.gz"))
S = d[d.layer == "settlement"]
# names judged to be spelling false friends in the drawn samples, with the reason
FALSE = {
    "ley": {"Folley": "probably folly"},
    "ing": {"Tucking Mill": "tucking, cloth fulling", "Chipping Norton": "chipping, a market"},
    "by": {"Barnaby Green": "may be the personal name Barnaby"},
    "wick": {"Boslowick": "a Cornish name"},
    "pen": {"Pennypot": "penny"},
    "dun": {"Duncanstone": "personal name Duncan", "Duncansclett": "personal name Duncan"},
    "ard": {"Ardee": "Irish Baile Atha Fhirdhia"},
}
KEYS = ["ton", "ley", "ing", "ham", "ford", "by", "bury", "wick", "pen", "dun", "kil", "bal", "town", "ard"]
random.seed(7)
rows, tot, bad = [], 0, 0
for k in KEYS:
    ex = [n for n, e in zip(S.name, S.el) if k in e]
    smp = random.sample(ex, 20)
    f = [n for n in smp if n in FALSE.get(k, {})]
    rows.append(dict(key=k, sample=smp, false_friends=f, ok=20 - len(f)))
    tot += 20; bad += len(f)
p = os.path.join(ROOT, "data", "results.json"); R = json.load(open(p))
R["audit"] = dict(elements=KEYS, per_element=20, n=tot, false=bad, ok_share=round((tot - bad) / tot, 4), rows=rows, reasons=FALSE)
json.dump(R, open(p, "w"), indent=1, ensure_ascii=False)
print(tot, bad, round((tot - bad) / tot, 4))
