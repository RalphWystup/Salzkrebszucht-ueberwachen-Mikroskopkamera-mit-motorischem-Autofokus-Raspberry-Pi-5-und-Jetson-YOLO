#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""jetson_yolo_training_1.4.py -- laeuft auf dem Jetson (Auftrag, startet ABGELOEST): trainiert yolov8n auf ~/mikroskop/yolo/datensatz in
~/<yolo-umgebung> (GPU), Protokoll ~/mikroskop/yolo/training.log (ueber /datei abholbar), Ergebnis ~/mikroskop/yolo/modell/{best.pt,best.engine,
info.json}. Epochen in der ersten Zeile von EPOCHEN (Auftraege haben keine Argumente). Dauer: Minuten bis Stunden je nach Bilderzahl.
1.4 (06.11.2026): ohne TensorRT-Export (hing zweimal im Speicher; PyTorch FP16 reicht).
1.3 (06.11.2026): Start als systemd-Einheit mikroskop-training statt nohup unter dem Dienst (cgroup-Drosselung, KillMode).
1.2 (06.11.2026): Cache-Waechter alle 20 s waehrend des Trainings, workers 0, zweiter Versuch mit batch 4 bei Speichernot.
1.1 (06.11.2026): leert vor dem Start den Seitencache (sudo cache_leeren ohne Kennwort), sonst bekommt CUDA keinen Speicher."""
import os, subprocess
EPOCHEN = 40
Y = os.path.expanduser("~/mikroskop/yolo"); os.makedirs(Y + "/modell", exist_ok=True)
skript = f'''
import os, json, time, shutil, glob
from ultralytics import YOLO
Y = os.path.expanduser("~/mikroskop/yolo"); os.chdir(Y); t0 = time.time()
import subprocess, threading
def cache_leeren(): subprocess.run("sudo -n /usr/local/sbin/cache_leeren >/dev/null 2>&1", shell=True)
def waechter():                                                  # 1.2: waehrend des Trainings alle 20 s den Seitencache leeren (nvmap braucht freien Speicher)
    while True: time.sleep(20); cache_leeren()
threading.Thread(target=waechter, daemon=True).start()
m = YOLO("yolov8n.pt"); cache_leeren()
try:
    erg = m.train(data=Y + "/datensatz/data.yaml", epochs={EPOCHEN}, imgsz=640, batch=8, device=0, workers=0, project=Y + "/laeufe", name="lauf_" + time.strftime("%H%M"), exist_ok=True, patience=15, plots=False, verbose=False)
except RuntimeError as e:                                        # 1.2: bei Speichernot mit halber Stapelgroesse noch einmal
    print("Erster Versuch scheiterte:", str(e)[:160], "-- zweiter Versuch mit batch 4", flush=True); cache_leeren(); import torch; torch.cuda.empty_cache(); m = YOLO("yolov8n.pt")
    erg = m.train(data=Y + "/datensatz/data.yaml", epochs={EPOCHEN}, imgsz=640, batch=4, device=0, workers=0, project=Y + "/laeufe", name="lauf_" + time.strftime("%H%M"), exist_ok=True, patience=15, plots=False, verbose=False)
lauf = str(erg.save_dir) if hasattr(erg, "save_dir") else sorted(glob.glob(Y + "/laeufe/lauf_*"))[-1]
best = os.path.join(lauf, "weights", "best.pt"); shutil.copy(best, Y + "/modell/best.pt")
mm = YOLO(best); v = mm.val(data=Y + "/datensatz/data.yaml", imgsz=640, device=0, plots=False, verbose=False)
info = {{"lauf": lauf, "epochen": {EPOCHEN}, "sekunden": round(time.time() - t0), "mAP50": round(float(v.box.map50), 3), "mAP50_95": round(float(v.box.map), 3), "je_klasse_mAP50": [round(float(x), 3) for x in v.box.ap50], "uhr": time.strftime("%Y-%m-%d %H:%M:%S")}}
info["engine"] = "kein Export (1.4): TensorRT-Export brach zweimal mit CUDA out of memory ab bzw. hing; PyTorch FP16 liefert 49,8 Bilder/s, mehr als der Strom"
json.dump(info, open(Y + "/modell/info.json", "w"), indent=1); print("TRAINING_FERTIG", json.dumps(info), flush=True)
'''
open(Y + "/training_lauf.py", "w").write(skript)
# 1.3: kein Start von hier -- das Training laeuft als eigene systemd-Einheit mikroskop-training (eigene cgroup: kein Drosseln, kein Tod beim
#      Dienstneustart); Start: sudo -n systemctl start mikroskop-training (sudoers-Regel), Protokoll ~/mikroskop/yolo/training.log
r = subprocess.run("sudo -n systemctl start mikroskop-training && sleep 2 && systemctl is-active mikroskop-training", shell=True, capture_output=True, text=True, timeout=60)
print(f"Training als Einheit gestartet ({EPOCHEN} Epochen):", (r.stdout + r.stderr).strip()[-120:], "; Protokoll ~/mikroskop/yolo/training.log, Ergebnis ~/mikroskop/yolo/modell/")
