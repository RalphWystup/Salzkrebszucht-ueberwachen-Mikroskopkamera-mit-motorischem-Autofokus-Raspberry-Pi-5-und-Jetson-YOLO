#!/usr/bin/env python3
"""jetson_veroeffentlichung_daten_1.0.py -- laeuft auf dem Jetson: Aufzeichnungen fuer die veroeffentlichte Seite (ohne Geraet) nach
~/mikroskop/veroeffentlichung/: Staende von Jetson-Dienst (:8095/stand, /yolo/verlauf, /selbst/stand, /selbst/verlauf), YOLO (:8096/stand),
Pi-Auswertung (mikroskop:8092/stand, /punkte, /zaehler) und Pi-Status (mikroskop:8090/status); Standbilder: YOLO (:8096/bild.jpg),
Selbsttraining (selbsttraining/bild.jpg), Pi-Kamera (mikroskop:8090/bild.jpg). 1.0 (14.11.2026).
Autoren: Prof. Dr.-Ing. Ralph Wystup M.Sc. und Claude (Anthropic, Claude Code) — gemeinsam erstellt."""
import os, json, urllib.request, shutil, time
Z = os.path.expanduser("~/mikroskop/veroeffentlichung"); os.makedirs(Z, exist_ok=True)
Q = {"stand_jetson.json": "http://127.0.0.1:8095/stand", "verlauf.json": "http://127.0.0.1:8095/yolo/verlauf", "selbst_stand.json": "http://127.0.0.1:8095/selbst/stand",
     "selbst_verlauf.json": "http://127.0.0.1:8095/selbst/verlauf", "stand_yolo.json": "http://127.0.0.1:8096/stand",
     "auswertung_stand.json": "http://mikroskop:8092/stand", "auswertung_punkte.json": "http://mikroskop:8092/punkte", "auswertung_zaehler.json": "http://mikroskop:8092/zaehler",
     "status_pi.json": "http://mikroskop:8090/status"}
B = {"bild_yolo_1.jpg": "http://127.0.0.1:8096/bild.jpg", "bild_roh_1.jpg": "http://mikroskop:8090/bild.jpg"}
for n, u in list(Q.items()) + list(B.items()):
    try:
        d = urllib.request.urlopen(u, timeout=15).read()
        if n.endswith(".json"): json.loads(d)
        open(os.path.join(Z, n), "wb").write(d); print("OK", n, len(d))
    except Exception as e: print("FEHLER", n, u, str(e)[:80])
s = os.path.expanduser("~/mikroskop/selbsttraining/bild.jpg")
if os.path.exists(s): shutil.copy(s, os.path.join(Z, "selbst_bild.jpg")); print("OK selbst_bild.jpg")
open(os.path.join(Z, "ZEIT.txt"), "w").write(time.strftime("%Y-%m-%d %H:%M:%S") + "\n"); print("FERTIG", time.strftime("%H:%M"))
