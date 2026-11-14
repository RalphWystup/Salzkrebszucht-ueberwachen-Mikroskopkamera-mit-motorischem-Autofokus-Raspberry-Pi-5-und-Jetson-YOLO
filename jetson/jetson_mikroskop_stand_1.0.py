#!/usr/bin/env python3
"""jetson_mikroskop_stand_1.0.py -- liest auf dem Jetson die Staende des Mikroskopdienstes (:8095/stand: statistik, yolo, platte,
nachziehen, lernen) und des YOLO-Livedienstes (:8096/stand) und druckt die Kernzahlen. 1.0 (14.11.2026).
Autoren: Prof. Dr.-Ing. Ralph Wystup M.Sc. und Claude (Anthropic, Claude Code) — gemeinsam erstellt."""
import json, urllib.request
for url, keys in (("http://127.0.0.1:8095/stand", ("fassung", "statistik", "yolo", "platte", "nachziehen", "lernen", "live", "pi_live")), ("http://127.0.0.1:8096/stand", None)):
    try:
        d = json.loads(urllib.request.urlopen(url, timeout=8).read())
        d = {k: d.get(k) for k in keys} if keys else d
        print(url, json.dumps(d, ensure_ascii=False)[:2500])
    except Exception as ex:
        print(url, "FEHLER", ex)
