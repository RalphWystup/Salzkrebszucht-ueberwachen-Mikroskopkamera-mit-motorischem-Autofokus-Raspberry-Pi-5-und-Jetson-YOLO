#!/usr/bin/env python3
"""jetson_selbst_einrichten_1.0.py -- laeuft AUF dem Jetson (jetson_fahren): richtet das Selbsttraining ein.
Dateien jetson_selbsttraining_1.0.py und jetson_dienst_1.14.py liegen vorher (jetson_senden) in ~/mikroskop. Schritte: Syntaxprobe,
crontab-Zeile 03:00 (ohne sudo), Dienst auf 1.14 umschalten (jetson_dienst_FASSUNG.txt; der Starter wechselt von selbst), warten,
/selbst/stand abfragen. Rueckfall: echo jetson_dienst_1.13.py > ~/mikroskop/jetson_dienst_FASSUNG.txt. 1.0 (14.11.2026).
Autoren: Prof. Dr.-Ing. Ralph Wystup M.Sc. und Claude (Anthropic, Claude Code) — gemeinsam erstellt."""
import os, subprocess, time, json, urllib.request, py_compile
H = os.path.expanduser("~/mikroskop"); PY = os.path.expanduser("~/yolo_umgebung/bin/python")
for f in ("jetson_selbsttraining_1.0.py", "jetson_dienst_1.14.py"):
    p = os.path.join(H, f)
    if not os.path.isfile(p): print("FEHLT", p); raise SystemExit(1)
    py_compile.compile(p, doraise=True); print("Syntax ok:", f)
os.makedirs(os.path.join(H, "selbsttraining"), exist_ok=True)
zeile = f"0 3 * * * cd {H} && {PY} -u {H}/jetson_selbsttraining_1.0.py >> {H}/selbsttraining/lauf.log 2>&1"
alt = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout
zeilen = [l for l in alt.splitlines() if "jetson_selbsttraining" not in l]; neu = "\n".join(zeilen + [zeile]) + "\n"
if neu != alt: subprocess.run(["crontab", "-"], input=neu, text=True); print("crontab: 03:00 taeglich eingetragen")
else: print("crontab: schon da")
fs = os.path.join(H, "jetson_dienst_FASSUNG.txt"); vorher = open(fs).read().strip() if os.path.exists(fs) else "?"
open(fs, "w").write("jetson_dienst_1.14.py\n"); print("FASSUNG:", vorher, "->", "jetson_dienst_1.14.py")
for i in range(12):
    time.sleep(5)
    try:
        d = json.loads(urllib.request.urlopen("http://127.0.0.1:8095/stand", timeout=5).read())
        if d.get("fassung") == "1.14":
            s = json.loads(urllib.request.urlopen("http://127.0.0.1:8095/selbst/stand", timeout=5).read())
            print("Dienst 1.14 antwortet; /selbst/stand:", json.dumps({k: s.get(k) for k in ("laeuft", "hinweis", "cron", "training_einheit")})); break
        print("Dienst meldet Fassung", d.get("fassung"), "- warte")
    except Exception as e:
        print("Dienst (noch) nicht erreichbar:", str(e)[:60])
print("FERTIG")
