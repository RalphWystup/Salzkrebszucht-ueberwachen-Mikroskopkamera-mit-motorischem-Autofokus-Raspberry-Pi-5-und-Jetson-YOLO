#!/usr/bin/env python3
"""jetson_selbst_stand_1.0.py -- Stand des Selbsttrainings vom Jetson-Dienst (:8095/selbst/stand, /selbst/verlauf) und Ende von lauf.log. 1.0 (14.11.2026).
Autoren: Prof. Dr.-Ing. Ralph Wystup M.Sc. und Claude (Anthropic, Claude Code) — gemeinsam erstellt."""
import json, urllib.request, os
for u in ("http://127.0.0.1:8095/stand", "http://127.0.0.1:8095/selbst/stand", "http://127.0.0.1:8095/selbst/verlauf"):
    try:
        d = json.loads(urllib.request.urlopen(u, timeout=6).read())
        if u.endswith("/stand") and "selbst" not in u: d = {"fassung": d.get("fassung"), "laeuft_min": d.get("laeuft_min")}
        if "selbst/stand" in u and d.get("stand"): d["stand"] = {k: v for k, v in d["stand"].items() if k in ("phase", "fortschritt", "meldung", "uhr", "drift", "marken", "training", "abnahme", "ergebnis", "fehler", "start")}; d.pop("training_log", None)
        print(u, json.dumps(d, ensure_ascii=False)[:1800])
    except Exception as e: print(u, "FEHLER", e)
p = os.path.expanduser("~/mikroskop/selbsttraining/lauf.log"); print("lauf.log:", open(p, errors="replace").read()[-800:] if os.path.exists(p) else "-")
