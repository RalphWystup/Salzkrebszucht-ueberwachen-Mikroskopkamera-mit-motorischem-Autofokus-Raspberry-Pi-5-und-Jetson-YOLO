#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""jetson_yolo_einrichten_1.3.py -- laeuft AUF dem Jetson ueber jetson_fahren_1.3 (sudo ueber JK): schreibt die Einheiten mikroskop-training und
mikroskop-yolo neu, nur daemon-reload, kein Neustart des laufenden Livedienstes.
1.3 (06.11.2026, 17:20), Befund aus dem Journal 16:46:53: 'cache_leeren: cannot create /proc/sys/vm/drop_caches: Permission denied' -- ExecStartPre
ohne '+' lief als dhbw, der Seitencache wurde beim Start NIE geleert (Befund 14:28: CUDA/nvmap braucht physisch freien Speicher). Jetzt
'ExecStartPre=-+/usr/local/sbin/cache_leeren' (+ = als root, - = Fehler nicht toedlich) in beiden Einheiten. Sonst wie 1.2: die Trainingseinheit
haelt den Livedienst an (ExecStartPre=+systemctl stop) und startet ihn danach (ExecStopPost=+systemctl start), KillMode=control-group.
Nachweis der Kette 16:42-16:47: Fertig -> Datensatz -> Training 215 s (Livedienst pausiert) -> best.pt 16:46:45 -> Livedienst 16:46:53 neu, Modell geladen 16:47:00."""
import os, subprocess
kw = os.environ.get("JK", ""); H = os.path.expanduser("~/mikroskop"); V = os.path.expanduser("~/<yolo-umgebung>")
def su(c, t=120):
    r = subprocess.run(f"sudo -S -p '' sh -c {c!r}", shell=True, input=(kw + "\n") * 2, capture_output=True, text=True, timeout=t); return (r.stdout + r.stderr).strip()[-600:]
training = f"""[Unit]
Description=Mikroskop-YOLO-Training (yolov8n auf ~/mikroskop/yolo/datensatz; eigene cgroup, kein Speicherlimit; haelt den Livedienst waehrend des Trainings an)
After=network-online.target
[Service]
Type=oneshot
User=dhbw
WorkingDirectory={H}/yolo
Environment=LD_LIBRARY_PATH=/usr/lib/aarch64-linux-gnu/libcudss/12
ExecStartPre=+/bin/systemctl stop mikroskop-yolo.service
ExecStartPre=-+/usr/local/sbin/cache_leeren
ExecStart=/bin/sh -c '{V}/bin/python -u {H}/yolo/training_lauf.py >> {H}/yolo/training.log 2>&1'
ExecStopPost=+/bin/systemctl start mikroskop-yolo.service
KillMode=control-group
TimeoutStartSec=6h
"""
yolo = f"""[Unit]
Description=Mikroskop-YOLO (Livestrom des Pi durch YOLO auf dem Grafikprozessor; Starter jetson_yolo_lauf.py, Fassung aus jetson_yolo_FASSUNG.txt; Auskunft :8096)
After=network-online.target mikroskop-jetson.service
ConditionPathExists=|{H}/yolo/modell/best.engine
ConditionPathExists=|{H}/yolo/modell/best.pt
[Service]
Type=simple
User=dhbw
WorkingDirectory={H}
Environment=LD_LIBRARY_PATH=/usr/lib/aarch64-linux-gnu/libcudss/12
ExecStartPre=-+/usr/local/sbin/cache_leeren
ExecStart={V}/bin/python -u {H}/jetson_yolo_lauf.py
Restart=always
RestartSec=10
[Install]
WantedBy=multi-user.target
"""
open(H + "/mikroskop-training.service", "w").write(training); open(H + "/mikroskop-yolo.service", "w").write(yolo)
print("Einheiten:", su(f"cp {H}/mikroskop-training.service {H}/mikroskop-yolo.service /etc/systemd/system/ && systemctl daemon-reload && systemctl cat mikroskop-training mikroskop-yolo | grep -E '^(Exec|Kill)'", 60))
print("Zustand:", subprocess.run("systemctl is-active mikroskop-training mikroskop-yolo mikroskop-yolo.path | tr '\\n' ' '; systemctl show -p NRestarts mikroskop-yolo", shell=True, capture_output=True, text=True).stdout.strip())
