#!/usr/bin/env python3
"""jetson_selbst_abnahme_1.0.py -- startet auf dem Jetson das Selbsttraining im Betrieb ABNAHME_NUR=1 (nur Drift messen und den
vorhandenen Kandidaten modell/kandidat/best.pt gegen das alte Modell abnehmen; kein Training). 1.0 (14.11.2026).
Autoren: Prof. Dr.-Ing. Ralph Wystup M.Sc. und Claude (Anthropic, Claude Code) — gemeinsam erstellt."""
import os, subprocess, time, json, urllib.request
H = os.path.expanduser("~/mikroskop"); PY = os.path.expanduser("~/yolo_umgebung/bin/python")
if subprocess.run("pgrep -f '[j]etson_selbsttraining_1.0.py'", shell=True, capture_output=True, text=True).stdout.strip(): print("laeuft schon"); raise SystemExit(1)
env = dict(os.environ, ABNAHME_NUR="1", ERZWINGEN="1")
subprocess.Popen(["nohup", PY, "-u", os.path.join(H, "jetson_selbsttraining_1.0.py")], stdout=open(os.path.join(H, "selbsttraining", "lauf.log"), "a"), stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True, env=env, cwd=H)
time.sleep(20); s = json.loads(urllib.request.urlopen("http://127.0.0.1:8095/selbst/stand", timeout=10).read()); st = s.get("stand") or {}
print("laeuft", s.get("laeuft"), "| Phase", st.get("phase"), "|", st.get("meldung"))
