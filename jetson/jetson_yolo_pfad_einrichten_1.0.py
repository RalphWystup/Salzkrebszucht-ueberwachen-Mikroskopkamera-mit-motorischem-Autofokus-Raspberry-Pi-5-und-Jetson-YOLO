#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""jetson_yolo_pfad_einrichten_1.0.py -- laeuft AUF dem Jetson ueber jetson_fahren_1.3 (sudo): systemd-Pfadwaechter mikroskop-yolo.path, der den
Dienst mikroskop-yolo startet, sobald ~/mikroskop/yolo/modell/best.pt erscheint (und beim Hochfahren, wenn es schon da ist). Dazu laeuft der
Dienst ohne ConditionPathExists weiter wie eingerichtet (Restart=always)."""
import os, subprocess
kw = os.environ.get("JK", ""); H = os.path.expanduser("~/mikroskop")
def su(c, t=120):
    r = subprocess.run(f"sudo -S -p '' sh -c {c!r}", shell=True, input=(kw + "\n") * 2, capture_output=True, text=True, timeout=t); return (r.stdout + r.stderr).strip()[-300:]
pfad = f"""[Unit]
Description=Startet Mikroskop-YOLO, sobald ein Modell liegt
[Path]
PathExists={H}/yolo/modell/best.pt
Unit=mikroskop-yolo.service
[Install]
WantedBy=multi-user.target
"""
open(H + "/mikroskop-yolo.path", "w").write(pfad)
print("Pfadwaechter:", su(f"cp {H}/mikroskop-yolo.path /etc/systemd/system/ && systemctl daemon-reload && systemctl enable --now mikroskop-yolo.path && systemctl is-active mikroskop-yolo.path && systemctl is-active mikroskop-yolo || true"))
print("Modell da?", os.path.exists(H + "/yolo/modell/best.pt"), "| Training laeuft:", subprocess.run("pgrep -fc training_lauf.py", shell=True, capture_output=True, text=True).stdout.strip())
