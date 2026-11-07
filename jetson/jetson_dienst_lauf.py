#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""jetson_dienst_lauf.py -- Starter des Mikroskop-Dienstes auf dem Jetson (systemd ExecStart, 06.11.2026): startet die in
jetson_dienst_FASSUNG.txt genannte Fassung. Fassungswechsel und Rueckfall OHNE sudo: Dateiname in jetson_dienst_FASSUNG.txt
aendern (als Auftrag vom Pi); der laufende Dienst (ab 1.4) merkt das, endet, und systemd (Restart=always) startet hierueber
die genannte Fassung. Vorgabe ohne Datei: jetson_dienst_1.4.py."""
import os, sys
H = os.path.dirname(os.path.abspath(__file__)); F = os.path.join(H, "jetson_dienst_FASSUNG.txt"); VORGABE = "jetson_dienst_1.4.py"
try: name = open(F).read().strip() or VORGABE
except Exception: name = VORGABE
p = os.path.join(H, name)
if not os.path.isfile(p): print(f"FEHLER: {p} fehlt -- jetson_dienst_FASSUNG.txt nennt eine Datei, die es nicht gibt", flush=True); sys.exit(1)
os.environ["JETSON_LAUF"] = "1"; print(f"Starter: {name}", flush=True)
os.execv(sys.executable, [sys.executable, "-u", p])
