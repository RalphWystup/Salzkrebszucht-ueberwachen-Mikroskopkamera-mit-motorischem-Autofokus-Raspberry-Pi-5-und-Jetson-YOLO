#!/usr/bin/env python3
"""jetson_selbst_start_1.0.py -- startet auf dem Jetson einen erzwungenen Lauf des Selbsttrainings ueber den Dienst (POST :8095/selbst/start). 1.0 (14.11.2026).
Autoren: Prof. Dr.-Ing. Ralph Wystup M.Sc. und Claude (Anthropic, Claude Code) — gemeinsam erstellt."""
import json, urllib.request, time
r = urllib.request.Request("http://127.0.0.1:8095/selbst/start", data=json.dumps({"erzwingen": True}).encode(), headers={"Content-Type": "application/json"})
print(urllib.request.urlopen(r, timeout=10).read().decode()); time.sleep(20)
s = json.loads(urllib.request.urlopen("http://127.0.0.1:8095/selbst/stand", timeout=10).read()); st = s.get("stand") or {}
print("laeuft", s.get("laeuft"), "| Phase", st.get("phase"), "|", st.get("meldung"), "| Drift Saetze", (st.get("drift") or {}).get("saetze_gefunden"))
