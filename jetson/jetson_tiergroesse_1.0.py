#!/usr/bin/env python3
"""jetson_tiergroesse_1.0.py -- je Tag (jeder 3. Satz): Median der Rahmenbreite/-hoehe der Farbtiere (rb, rh), der braunen Flaeche a und des
Fuellgrads a/(rb*rh): schrumpfen die Tiere, oder wird nur ihr brauner Kern kleiner (Transparenz)? 1.0 (14.11.2026).
Autoren: Prof. Dr.-Ing. Ralph Wystup M.Sc. und Claude (Anthropic, Claude Code) — gemeinsam erstellt."""
import os, glob, json, re, collections
import numpy as np
A = os.path.expanduser("~/mikroskop/aufnahmen"); T = collections.defaultdict(lambda: {"rb": [], "rh": [], "a": [], "f": [], "lang": []})
for i, p in enumerate(sorted(glob.glob(A + "/*_farbe.jsonl"))):
    if i % 3: continue
    m = re.match(r"(\d{8})", os.path.basename(p))
    if not m: continue
    try: z = [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()][1:]
    except Exception: continue
    for w in z:
        for t in w.get("tiere", []):
            rb, rh, a = t.get("rb"), t.get("rh"), t.get("a")
            if rb and rh and a:
                d = T[m.group(1)]; d["rb"].append(rb); d["rh"].append(rh); d["a"].append(a); d["f"].append(a / (rb * rh)); d["lang"].append(max(rb, rh))
print("Tag       Tiere   Rahmen lang px P50/P90   braune Flaeche P50   Fuellgrad P50   Rahmenflaeche P50")
for tag in sorted(T):
    d = T[tag]; L = np.array(d["lang"]); a = np.array(d["a"]); f = np.array(d["f"]); rf = np.array(d["rb"]) * np.array(d["rh"])
    print(f"{tag}  {len(L):7d}   {np.median(L):5.0f} / {np.percentile(L, 90):5.0f}        {np.median(a):6.0f}            {np.median(f):5.2f}          {np.median(rf):6.0f}")
