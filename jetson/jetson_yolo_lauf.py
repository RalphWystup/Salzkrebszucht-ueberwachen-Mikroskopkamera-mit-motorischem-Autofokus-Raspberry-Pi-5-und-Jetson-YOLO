#!/usr/bin/env python3
"""jetson_yolo_lauf.py -- Starter des YOLO-Livedienstes (systemd ExecStart): startet die in jetson_yolo_FASSUNG.txt genannte Fassung
(Vorgabe jetson_yolo_live_1.1.py) in der Umgebung, in der er selbst laeuft (~/<yolo-umgebung>/bin/python). Wechsel ohne sudo: Datei aendern,
dann sudo -n systemctl restart mikroskop-yolo (sudoers-Regel) oder warten, bis der Dienst von selbst neu startet."""
import os, sys
H = os.path.dirname(os.path.abspath(__file__)); F = os.path.join(H, "jetson_yolo_FASSUNG.txt"); VORGABE = "jetson_yolo_live_1.1.py"
try: name = open(F).read().strip() or VORGABE
except Exception: name = VORGABE
p = os.path.join(H, name)
if not os.path.isfile(p): print(f"FEHLER: {p} fehlt", flush=True); sys.exit(1)
print(f"Starter: {name}", flush=True); os.execv(sys.executable, [sys.executable, "-u", p])
