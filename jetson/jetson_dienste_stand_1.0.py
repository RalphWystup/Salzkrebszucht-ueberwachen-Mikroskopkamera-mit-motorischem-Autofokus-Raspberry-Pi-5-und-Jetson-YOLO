#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""jetson_dienste_stand_1.0.py -- laeuft AUF dem Jetson (jetson_fahren_1.3, ohne sudo). 07.11.2026.
Zweck: Vor dem vorlaeufigen Abschalten des FEM-Dienstes (sein Wort 07.11.2026: "wenn der FEM dienst nicht
gebraucht wird kann es voruebergehend deaktiviert werden") den Ist-Stand festhalten -- erst nachsehen, dann handeln:
Welche Einheiten laufen, was belegt Speicher und Auslagerung, wer horcht auf welchem Anschluss, hat der FEM-Dienst
in den letzten Tagen ueberhaupt gearbeitet. Nur lesen, nichts anfassen."""
import subprocess, os
def sh(c, t=60):
    try:
        r = subprocess.run(c, shell=True, capture_output=True, text=True, timeout=t)
        return (r.stdout + r.stderr).strip()
    except Exception as e:
        return f"(Fehler: {e})"

print("===== Rechner:"); print(sh("hostname; uptime"))
print("===== Speicher und Auslagerung:"); print(sh("free -m; echo; swapon --show 2>&1"))
print("===== Groesste Prozesse (RSS kB):")
print(sh("ps -eo pid,user,rss,etimes,comm,args --sort=-rss | head -14 | cut -c1-150"))
print("===== Laufende Einheiten (system):")
print(sh("systemctl list-units --type=service --state=running --no-pager --no-legend | cut -c1-110"))
print("===== Aktivierte Einheiten, die beim Start kommen:")
print(sh("systemctl list-unit-files --type=service --state=enabled --no-pager --no-legend | cut -c1-90"))
print("===== Anschluesse, die horchen:")
print(sh("ss -ltnp 2>/dev/null | head -25 || netstat -ltnp 2>/dev/null | head -25"))
print("===== Einheiten mit FEM/femm/rechen im Namen:")
print(sh("systemctl list-unit-files --no-pager --no-legend | grep -iE 'fem|rechen|verbund|solver' | cut -c1-90"))
for e in ("fem.service", "femdienst.service", "fem-dienst.service", "rechenverbund.service", "mikroskop-fem.service"):
    z = sh(f"systemctl is-active {e} 2>&1"); 
    if "could not be found" not in z and z: print(f"  {e}: {z}")
print("===== Einheitentexte der gefundenen FEM-Einheiten:")
print(sh("for u in $(systemctl list-unit-files --no-pager --no-legend | grep -iE 'fem|rechen|verbund' | awk '{print $1}'); do echo \"--- $u\"; systemctl cat $u 2>&1 | grep -vE '^#|^$' | head -20; echo \"  aktiv: $(systemctl is-active $u) / $(systemctl is-enabled $u 2>&1)\"; done"))
print("===== Hat der FEM-Dienst gearbeitet? (Journal, 7 Tage)")
print(sh("for u in $(systemctl list-unit-files --no-pager --no-legend | grep -iE 'fem|rechen|verbund' | awk '{print $1}'); do echo \"--- $u\"; journalctl -u $u --since '-7 days' --no-pager -n 12 -o short 2>&1 | cut -c1-150; done"))
print("===== Desktop (nicht anfassen, nur ansehen):")
print(sh("systemctl get-default; systemctl is-active gdm3 gdm display-manager 2>&1 | tr '\\n' ' '"))
print("===== Mikroskop-Einheiten (muessen laufen bleiben):")
print(sh("for u in mikroskop-jetson mikroskop-yolo mikroskop-training; do echo \"$u: $(systemctl is-active $u) / $(systemctl is-enabled $u 2>&1)\"; done"))
print("===== Platte:"); print(sh("df -h / /home 2>&1 | head -5"))
