#!/bin/bash
# pi_auswertung_wechsel_1.0.sh -- laeuft AUF dem Pi (als pi, sudo ohne Kennwort): Auswertung auf die genannte Fassung umstellen.
#   bash pi_auswertung_wechsel_1.0.sh 1.5      (erwartet /home/pi/wache/halten/auswertung_1.5.py und mikroskop-auswertung_1.5.service)
#   Rueckfall:  bash pi_auswertung_wechsel_1.0.sh 1.4   oder   bash /home/pi/RUECKFALL_2026-11-06/herstellen.sh
# Fokusdienst (:8090) wird nicht angefasst. Nach dem Neustart: /stand muss die Fassung nennen und Bilder liefern.
set -u
F=${1:?Fassung, z. B. 1.5}; H=/home/pi/wache/halten
[ -f $H/auswertung_$F.py ] || { echo "FEHLER: $H/auswertung_$F.py fehlt"; exit 1; }
python3 -m py_compile $H/auswertung_$F.py || { echo "FEHLER: Syntax auswertung_$F.py"; exit 1; }
cp $H/auswertung_$F.py /home/pi/auswertung_$F.py
if [ -f $H/mikroskop-auswertung_$F.service ]; then sudo cp $H/mikroskop-auswertung_$F.service /etc/systemd/system/mikroskop-auswertung.service
else sudo sed -i "s#/home/pi/auswertung_[0-9.]*\.py#/home/pi/auswertung_$F.py#" /etc/systemd/system/mikroskop-auswertung.service; fi
sudo systemctl daemon-reload && sudo systemctl restart mikroskop-auswertung && echo "Dienst neu gestartet $(date +%H:%M:%S) mit $(grep ExecStart /etc/systemd/system/mikroskop-auswertung.service)"
for i in $(seq 1 30); do sleep 1; curl -s --max-time 2 http://127.0.0.1:8092/stand >/dev/null 2>&1 && break; done
sleep 8; curl -s --max-time 5 http://127.0.0.1:8092/stand | python3 -c "import json,sys; d=json.load(sys.stdin); print('STAND fassung', d.get('fassung'), 'phase', d.get('phase'), 'bilder', d.get('bilder'), 'bilder_s', d.get('bilder_s'), 'kaputt', d.get('kaputt'), 'nachgesucht', d.get('nachgesucht'))"
systemctl is-active mikroskop-auswertung mikroskop-fokus | tr '\n' ' '; echo; ls -la /home/pi/wache/zaehler.json 2>/dev/null | cut -c1-80
