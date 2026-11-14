#!/usr/bin/env python3
"""jetson_dienst_neustart_1.0.py -- laeuft auf dem Jetson: Jetson-Dienst ueber die FASSUNG-Datei neu starten (1.13 -> 1.14), dann /stand lesen. 1.0 (14.11.2026).
Autoren: Prof. Dr.-Ing. Ralph Wystup M.Sc. und Claude (Anthropic, Claude Code) — gemeinsam erstellt."""
import os, time, json, urllib.request
fs = os.path.expanduser("~/mikroskop/jetson_dienst_FASSUNG.txt")
open(fs, "w").write("jetson_dienst_1.13.py\n"); time.sleep(8); open(fs, "w").write("jetson_dienst_1.14.py\n")
for i in range(12):
    time.sleep(5)
    try:
        d = json.loads(urllib.request.urlopen("http://127.0.0.1:8095/stand", timeout=5).read()); print("Fassung", d.get("fassung"), "laeuft_min", d.get("laeuft_min"))
        if d.get("fassung") == "1.14":
            s = json.loads(urllib.request.urlopen("http://127.0.0.1:8095/selbst/stand", timeout=5).read()); print("selbst:", {k: s.get(k) for k in ("laeuft", "hinweis", "cron")}); break
    except Exception as e: print("warte:", str(e)[:50])
