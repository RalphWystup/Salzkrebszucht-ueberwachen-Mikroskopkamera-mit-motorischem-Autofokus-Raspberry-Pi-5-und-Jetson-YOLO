#!/usr/bin/env python3
"""jetson_transparenz_1.0.py -- Groesse und Farbe der Farbtiere je Tag (jeder 3. Satz): Perzentile der Flaeche, Median von braun/dunkel
(je Tier in <name>_farbe.jsonl), Anteil kleiner Tiere (< 400 px); dazu je Tag ein Satz mit vielen Tieren, dessen _ausschnitte.jpg /
_tafel.jpg noch da ist. 1.0 (14.11.2026). Autoren: Prof. Dr.-Ing. Ralph Wystup M.Sc. und Claude (Anthropic, Claude Code) — gemeinsam erstellt."""
import os, glob, json, re, collections
import numpy as np
A = os.path.expanduser("~/mikroskop/aufnahmen"); tage = collections.defaultdict(lambda: {"a": [], "braun": [], "dunkel": [], "bilder": []})
farben = sorted(glob.glob(A + "/*_farbe.jsonl"))
for i, p in enumerate(farben):
    if i % 3: continue
    n = os.path.basename(p)[:-12]; m = re.match(r"(\d{8})", n)
    if not m: continue
    T = tage[m.group(1)]
    try:
        z = [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()][1:]; tiere = [t for w in z for t in w.get("tiere", [])]
    except Exception: continue
    for t in tiere:
        T["a"].append(t.get("a", 0)); T["braun"].append(t.get("braun")); T["dunkel"].append(t.get("dunkel"))
    if len(tiere) / max(len(z), 1) > 1.5:
        for suf in ("_ausschnitte.jpg", "_tafel.jpg"):
            if os.path.exists(os.path.join(A, n + suf)): T["bilder"].append(n + suf)
print("Tag       Tiere   Flaeche px P10/P50/P90   <400px   braun P50   dunkel P50   Bilder vorhanden (Beispiel)")
for tag in sorted(tage):
    T = tage[tag]; a = np.array(T["a"], float); b = np.array([x for x in T["braun"] if x is not None], float); d = np.array([x for x in T["dunkel"] if x is not None], float)
    if not len(a): continue
    print(f"{tag}  {len(a):6d}   {np.percentile(a,10):5.0f}/{np.percentile(a,50):5.0f}/{np.percentile(a,90):5.0f}   {100*np.mean(a<400):5.1f} %   {np.median(b) if len(b) else float('nan'):8.1f}   {np.median(d) if len(d) else float('nan'):9.1f}   {len(T['bilder'])} ({T['bilder'][len(T['bilder'])//2] if T['bilder'] else '-'})")
