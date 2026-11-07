#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""auswertung_1.4.py -- Bildauswertung am Mikroskop-Pi, neu aufgesetzt am 05.11.2026.

Sein Wort: "du faengst noch einmal ganz von vorne an ... die Bildauswertung setze komplett neu auf, nachdem du die
angeordneten Recherchen durchgefuehrt hast, dazu vermesse die Tiere, die Dynamik, alle Randbedingungen".
Grundlage: RANDBEDINGUNGEN_1.0.md (gemessen), RECHERCHE_1.0.md (SORT, OC-SORT, ByteTrack, track-before-detect,
TRex/idtracker.ai, Daphnia-SORT, Copepoden-Kinematik), ENTWURF_1.0.md (Weg A). Bewaehrte, gemessene Teile der
Beobachter 2.x (Stromleser mit Endmarke, MOG2 mit Beleuchtungswechsel, Koerpermass am Rohbild, Ablage) sind uebernommen;
Erkennung und Verfolgung sind neu geschrieben.

Vier Stufen auf demselben Bild derselben Folge:
 1. ERKENNUNG   MOG2 (Graubild) -> Oeffnen/Schliessen -> Gruppen (naeher als GRUPPE px) -> Koerper am Rohbild (dunkler als
                KOERPER_ANTEIL des Hintergrunds) -> Bruchstuecke einschmelzen -> je Tier EINE Erkennung mit Mitte, Rahmen,
                Flaeche, Laenge/Breite. Kein Formfilter (gemessen: L/B 1,0..5,3 ohne Trennschaerfe).
 2. VERFOLGUNG  Hungarian-Zuordnung mit Tor TOR px um die LETZTE BEOBACHTUNG (keine Geschwindigkeitsvorhersage: Huepfen alle
                4 Bilder, 48 % Kehrtwenden je Bild; Kalman-Tracker driften bei springenden Objekten, arXiv 2509.18451).
                Kosten: Abstand + Flaechenaehnlichkeit + Aufschlag je fehlendem Bild + Aufschlag fuer ruhende Bahnen.
                Eine Bahn wird erst nach MIN_TREFFER Treffern in Folge gemeldet (SORT min_hits; track-before-detect) und
                nach GEDAECHTNIS Bildern ohne Treffer geloescht. "ruht": neu bis zum ersten Weg >= RUHE_WEG und wieder,
                wenn RUHE_BILDER lang keine RUHE_WEG zurueckgelegt wurden.
                1.1 RUDERSCHLAG-NACHWEIS: gemeldet wird eine Bahn erst, wenn sie einmal einen Schritt >= SCHLAG_MIN in einem
                Bild gemacht hat. Gemessen (60 Bahnen mit Farbwahrheit): 36 von 37 echten Bahnen zeigen einen Schritt
                >= 20 px (die eine ist ein ruhendes Tier), 70 % der Geisterbahnen (treibender Kruemel, Flackern an der
                Folienschrift, Teilchen) nie. Nauplien huepfen (Ruderschlag alle 4 Bilder, 25..68 px), Treibgut treibt.
 1.4 AUSSEHENS-NACHWEIS (Weg A, Stufe 2): je Kandidat werden die braunen Punkte (Saettigung > BRAUN_S, Helligkeit 40..235)
                im Koerperfeld (Rahmen + 4 px) gezaehlt. Gemessen an vier Rohaufnahmen: echte Kandidaten Median 740..1200,
                95 % ueber 220; Geister (Lichtmuster, Flackern an der Schrift, graues Treibgut) Median 2..44, 90 % unter 150.
                Eine Bahn wird gemeldet, wenn sie >= MIN_TREFFER Treffer hat UND in mindestens der Haelfte ihrer letzten
                AUSSEHEN_FENSTER Bilder >= BRAUN_MIN braune Punkte hatte. Der Ruderschlag-Nachweis (1.1) entfaellt damit;
                ruhende Tiere bleiben Tiere (grauer Punkt, zaehlen mit) und behalten ihre Nummer (GEDAECHTNIS_BESTAETIGT).
                Sein Wort: "also verbessern!" -- 60 % der ruhenden Tiere waren ohne Marke, Lichtmuster ohne Tier markiert.
 3. ANZEIGE     :PORT/strom_marken -- dasselbe Bild mit einem Punkt je gemeldetem bewegtem Tier, QUER zur Koerperachse auf
                einer festen Seite (1.3), ohne Text; jedes ANZEIGE_JEDES-te Bild, nur bei Zuschauern. Messbild bleibt roh.
                1.3: Der Punkt "hinter dem Tier bezogen auf den letzten Schritt" (1.1) sprang in 49 % der Bildschritte um mehr als
                eine halbe Koerperlaenge, weil die Tiere in 48 % der Schritte die Richtung umkehren -- sein Auge sah zwei Punkte
                ("sie schalten schnell um"). Die Koerperachse aus der Form ist stabil; der Punkt sitzt jetzt senkrecht dazu, auf der
                Seite mit positivem y (bei waagerechter Senkrechten: positivem x), Abstand halbe Breite + PUNKT_ABSTAND.
                (1.2, zwei Schlaege gleitend, verworfen: kostete Treffer ohne Gewinn.)
 4. AUFZEICHNUNG Ausloeser IN_FOLGE Bilder mit gemeldetem Tier; VORLAUF davor; Rohvideo, Video mit Rahmen, Rahmendatei je Bild
                (synchron), Bildtafel, Ausschnitte; Aufbewahrung BEHALTEN_MIN Minuten / BEHALTEN Saetze.
 Auskunft       /stand, /punkte, /zaehler (je Stunde das Hoechste und Mittel), /strom_marken
"""
import os, sys, time, json, glob, threading, collections, queue, http.server, socketserver, urllib.request, re
import numpy as np, cv2
try:
    from scipy.optimize import linear_sum_assignment
except Exception:
    linear_sum_assignment = None

FASSUNG = "1.4"
STROM = "http://127.0.0.1:8090/strom"
ABLAGE = "/home/pi/wache/aufnahmen"
PORT = 8092
AUS = (slice(40, 440), slice(60, 580))        # Einblendung oben links und Rand bleiben draussen (RANDBEDINGUNGEN)
BILDRATE = 28.8                                # Bilder/s des Stroms (gemessen)
# Erkennung
MOG_GESCHICHTE, MOG_VAR = 400, 24              # Lernfenster ~14 s; Mahalanobis-Schwelle (Zivkovic); sah 60 von 61 Tieren
KERN_AUF, KERN_ZU = 3, 7                       # Oeffnen gegen Kantenlinien, Schliessen gegen Loecher
GRUPPE = 25                                    # px: Rumpf und zerfallender Schwanz (2-3 Rumpflaengen) sind EIN Tier
KOERPER_ANTEIL = 0.15                          # Koerper = dunkler als 15 % des oertlichen Hintergrunds (Saum: <= 20 Stufen, Koerper 23..76)
KOERPER = (60, 4000)                           # px Koerperflaeche; Tiere gemessen 100..1700
FLAECHE = (100, 6000)                          # px Bewegungsmaske (weit; gemessen 111..2894)
BRUCH_ANTEIL, BRUCH_RAND = 0.5, 40             # Bruchstueck: < 50 % der Koerperflaeche eines Objekts, Mitte in dessen Rahmen + 40 px
WECHSEL_ANTEIL, WECHSEL_BILDER, WECHSEL_RATE = 0.15, 30, 0.05   # Beleuchtungssprung: > 15 % Vordergrund -> nachlernen
# Verfolgung
TOR = 70.0                                     # px um die letzte Beobachtung; groesster gemessener Sprung 68 px
FLAECHEN_GEWICHT, FEHLT_AUFSCHLAG, RUHE_AUFSCHLAG = 15.0, 3.0, 40.0
MIN_TREFFER, GEDAECHTNIS = 3, 10               # SORT min_hits / max_age; Geisterbahnen leben 1-3 Bilder
RUHE_BILDER, RUHE_WEG = 20, 10.0
BRAUN_S, BRAUN_MIN, AUSSEHEN_FENSTER = 40, 150, 10
AUSSEHEN_ANTEIL = 0.3                           # Anteil der letzten Bilder mit genug Braun; gemessen an 4 Aufnahmen: 150 px / 1/3 haelt die Treffer (92/75/97/95 %) bei Geistern 2/15/1/3 (1/2: 89/62/92/93 bei 1/8/1/3)   # 1.4: braune Punkte im Koerperfeld; Schwelle 150 px, Anteil >= 1/2 der letzten 10 Bilder
GEDAECHTNIS_BESTAETIGT = 60                    # 1.4: Bilder ohne Treffer, die eine schon gemeldete Bahn ueberlebt (2 s Pause behaelt die Nummer)
# Anzeige
ANZEIGE_JEDES, ANZEIGE_GUETE, PUNKT_ABSTAND, PUNKT_RADIUS = 2, 55, 8, 4
FARBEN = [(0x5e,0xc5,0x22),(0xf6,0x82,0x3b),(0x0b,0x9e,0xf5),(0x9e,0x27,0xec),(0xd0,0xb8,0x14),(0x4b,0x4b,0xef),(0x16,0xb8,0x84),(0x2b,0xcc,0x84)]
# Aufzeichnung
IN_FOLGE, VORLAUF, SEKUNDEN, HOECHSTENS_S = 5, 20, 5.0, 15.0
BEHALTEN, BEHALTEN_MIN = 40, 20

Z = {"fassung": FASSUNG, "phase": "start", "zeichnet": False, "rest_s": 0.0, "objekte": 0, "ausgeloest_uhr": None,
     "aufnahme_s": 0.0, "kaputt": 0, "mindest_s": SEKUNDEN, "hoechst_s": HOECHSTENS_S, "vordergrund": 0, "in_folge": 0,
     "aufnahmen": 0, "letzte": None, "bilder": 0, "bilder_s": 0.0, "helligkeit": 0.0, "beleuchtungswechsel": 0,
     "letzter_wechsel_uhr": None, "nachlernen": 0, "bahnen_offen": 0, "seit": time.time()}
sperre = threading.Lock()
LIVE = {"t": 0.0, "tiere": [], "ruhend": [], "breite": 640, "hoehe": 480, "massstab_um_px": None}
BILD = {"jpeg": None, "n": 0, "zuschauer": 0}; bild_da = threading.Condition()
ZAEHLER = {"stunden": [], "laufend": None}
SCHREIBER = queue.Queue()
LAENGE = re.compile(rb"Content-Length:\s*(\d+)")


def log(s): print(time.strftime("%H:%M:%S "), s, flush=True)


# ------------------------------------------------------------------ Bildstrom (uebernommen: Endmarke FF D9, Wiederaufsetzen)
def strom(quelle=STROM):
    while True:
        try:
            r = urllib.request.urlopen(quelle, timeout=20); puf = b""
            while True:
                s = r.read(65536)
                if not s: break
                puf += s; t = time.time()
                while True:
                    a = puf.find(b"\r\n\r\n")
                    if a < 0: break
                    m = LAENGE.search(puf[:a])
                    if not m: puf = puf[a+4:]; break
                    n = int(m.group(1))
                    if len(puf) < a+4+n: break
                    b = puf[a+4:a+4+n]; puf = puf[a+4+n:]
                    if b[-2:] != b"\xff\xd9":
                        with sperre: Z["kaputt"] += 1
                        continue
                    yield b, t
        except Exception as e:
            log(f"Strom abgerissen ({e}) -- neuer Versuch in 2 s"); time.sleep(2)


# ------------------------------------------------------------------ 1. Erkennung
class Erkenner:
    def __init__(self):
        self.mog = cv2.createBackgroundSubtractorMOG2(history=MOG_GESCHICHTE, varThreshold=MOG_VAR, detectShadows=False)
        self.k_auf, self.k_zu = np.ones((KERN_AUF, KERN_AUF), np.uint8), np.ones((KERN_ZU, KERN_ZU), np.uint8)
        self.k_gruppe = np.ones((GRUPPE + 1, GRUPPE + 1), np.uint8)
        self.gelernt = 0; self.hintergrund = None; self.hell = 0.0; self.nachlernen = 0; self.wechsel = 0; self.grenze = None

    def schritt(self, grau, farbe=None):
        """grau: Ausschnitt uint8; farbe: derselbe Ausschnitt in BGR (1.4, fuer den Aussehens-Nachweis). Liefert (vordergrundpunkte, [erkennungen])."""
        self.hell = float(grau.mean())
        if self.grenze is None: self.grenze = int(WECHSEL_ANTEIL * grau.size)
        fg = self.mog.apply(grau, learningRate=(WECHSEL_RATE if self.nachlernen > 0 else -1)); self.gelernt += 1
        if self.hintergrund is None or self.gelernt % 10 == 0: self.hintergrund = self.mog.getBackgroundImage()
        fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, self.k_auf); fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, self.k_zu)
        n_fg = int(cv2.countNonZero(fg))
        if self.gelernt >= 60 and n_fg > self.grenze and self.nachlernen == 0:
            self.wechsel += 1; self.nachlernen = WECHSEL_BILDER
            log(f"BELEUCHTUNGSWECHSEL: {n_fg} Vordergrundpunkte ({100*n_fg/grau.size:.0f} %), Helligkeit {self.hell:.0f} -- lerne {WECHSEL_BILDER} Bilder nach")
            return n_fg, []
        if self.nachlernen > 0: self.nachlernen -= 1; return n_fg, []
        if self.gelernt < 60 or n_fg < FLAECHE[0]: return n_fg, []
        grob = cv2.dilate(fg, self.k_gruppe)
        nn, lab, st, _ = cv2.connectedComponentsWithStats(grob, 8)
        erk = []
        for i in (np.argsort(-st[1:, cv2.CC_STAT_AREA], kind="stable") + 1)[:12]:
            i = int(i); gx, gy = int(st[i, cv2.CC_STAT_LEFT]), int(st[i, cv2.CC_STAT_TOP]); gw, gh = int(st[i, cv2.CC_STAT_WIDTH]), int(st[i, cv2.CC_STAT_HEIGHT])
            ys, xs = np.nonzero((lab[gy:gy+gh, gx:gx+gw] == i) & (fg[gy:gy+gh, gx:gx+gw] > 0)); a = int(len(xs))
            if not (FLAECHE[0] <= a <= FLAECHE[1]): continue
            x0, y0 = int(xs.min()) + gx, int(ys.min()) + gy; bw, bh = int(xs.max() - xs.min()) + 1, int(ys.max() - ys.min()) + 1
            kx0, ky0 = max(0, x0 - 4), max(0, y0 - 4); kx1, ky1 = min(grau.shape[1], x0 + bw + 4), min(grau.shape[0], y0 + bh + 4)
            hg = self.hintergrund[ky0:ky1, kx0:kx1].astype(np.int16)
            dunkler = (hg - grau[ky0:ky1, kx0:kx1].astype(np.int16)) > (KOERPER_ANTEIL * hg)
            kys, kxs = np.nonzero(dunkler); ma = int(len(kxs))
            if not (KOERPER[0] <= ma <= KOERPER[1]): continue
            kxs = kxs.astype(float) + kx0; kys = kys.astype(float) + ky0
            w, v = np.linalg.eigh(np.cov(np.stack([kxs, kys])) if ma >= 3 else np.eye(2))
            mL, mB = round(float(np.sqrt(max(w[1], 0)) * 4), 1), round(float(max(np.sqrt(max(w[0], 0)) * 4, 1e-9)), 1)
            erk.append({"a": a, "ma": ma, "mL": mL, "mB": mB, "L": mL, "B": mB,     # L/B: dieselben Werte fuer aeltere Werkzeuge
                        "w": round(float(np.degrees(np.arctan2(v[1, 1], v[0, 1]))), 1),
                        "x": round(kxs.mean() + AUS[1].start, 1), "y": round(kys.mean() + AUS[0].start, 1),
                        "rx": int(kxs.min()) + AUS[1].start, "ry": int(kys.min()) + AUS[0].start,
                        "rb": int(kxs.max() - kxs.min()) + 1, "rh": int(kys.max() - kys.min()) + 1})
        erk = einschmelzen(erk)
        if farbe is not None:                                           # 1.4: braune Punkte je Kandidat (nur im kleinen Feld)
            for o in erk:
                x0, y0 = max(0, o["rx"] - AUS[1].start - 4), max(0, o["ry"] - AUS[0].start - 4)
                x1, y1 = min(farbe.shape[1], o["rx"] - AUS[1].start + o["rb"] + 4), min(farbe.shape[0], o["ry"] - AUS[0].start + o["rh"] + 4)
                hsv = cv2.cvtColor(farbe[y0:y1, x0:x1], cv2.COLOR_BGR2HSV)
                o["braun"] = int(((hsv[:, :, 1] > BRAUN_S) & (hsv[:, :, 2] > 40) & (hsv[:, :, 2] < 235)).sum())
        return n_fg, erk


def einschmelzen(erk):
    """Bruchstuecke (klein, nahe an einem groesseren Objekt) in dieses einschmelzen; Mitte bleibt die des Grossen."""
    fertig = []
    for o in sorted(erk, key=lambda o: -o["ma"]):
        for g in fertig:
            if o["ma"] < BRUCH_ANTEIL * g["ma"] and g["rx"] - BRUCH_RAND <= o["x"] <= g["rx"] + g["rb"] + BRUCH_RAND and g["ry"] - BRUCH_RAND <= o["y"] <= g["ry"] + g["rh"] + BRUCH_RAND:
                x1, y1 = min(g["rx"], o["rx"]), min(g["ry"], o["ry"]); x2, y2 = max(g["rx"] + g["rb"], o["rx"] + o["rb"]), max(g["ry"] + g["rh"], o["ry"] + o["rh"])
                g["rx"], g["ry"], g["rb"], g["rh"] = x1, y1, x2 - x1, y2 - y1; g["a"] += o["a"]; g["ma"] += o["ma"]; g["stuecke"] = g.get("stuecke", 1) + 1
                break
        else:
            fertig.append(o)
    return fertig


# ------------------------------------------------------------------ 2. Verfolgung
class Verfolger:
    """Bahnen: nr, x, y (letzte Beobachtung), a (gleitende Flaeche), treffer (in Folge), fehlt, alter, ruht, geburt, spur, schritt (dx, dy)."""
    def __init__(self):
        self.bahnen = []; self.naechste = 0

    def _zuordnen(self, erk):
        if not self.bahnen or not erk: return {}
        D = np.empty((len(self.bahnen), len(erk))); K = np.empty_like(D)
        for i, b in enumerate(self.bahnen):
            for j, e in enumerate(erk):
                D[i, j] = np.hypot(e["x"] - b["x"], e["y"] - b["y"])
                K[i, j] = D[i, j] + FLAECHEN_GEWICHT * abs(np.log(max(e["ma"], 1) / max(b["a"], 1))) + FEHLT_AUFSCHLAG * b["fehlt"] + (RUHE_AUFSCHLAG if b["ruht"] and D[i, j] > RUHE_WEG else 0.0)
        if linear_sum_assignment is not None:
            zi, zj = linear_sum_assignment(np.where(D <= TOR, K, TOR * 1000.0))
            return {int(j): int(i) for i, j in zip(zi, zj) if D[i, j] <= TOR}
        zu, belegt = {}, set()
        for i, j in sorted(((i, j) for i in range(K.shape[0]) for j in range(K.shape[1])), key=lambda ij: K[ij]):
            if D[i, j] > TOR or i in belegt or j in zu: continue
            zu[j] = i; belegt.add(i)
        return zu

    def schritt(self, erk):
        """Liefert (bewegt, ruhend): nur bestaetigte Bahnen (treffer >= MIN_TREFFER); jede Erkennung bekommt nr, alter, ruht."""
        zu = self._zuordnen(erk)
        for b in self.bahnen: b["gesehen"] = False
        bewegt, ruhend = [], []
        for j, e in enumerate(erk):
            if j in zu:
                b = self.bahnen[zu[j]]; b["schritt"] = (e["x"] - b["x"], e["y"] - b["y"]); b["treffer"] += 1; b["alter"] += 1
                b["a"] = 0.7 * b["a"] + 0.3 * e["ma"]
            else:
                self.naechste += 1
                b = {"nr": self.naechste, "treffer": 1, "alter": 1, "fehlt": 0, "a": float(e["ma"]), "ruht": True, "bewegt_je": False, "gemeldet": False,
                     "aussehen": collections.deque(maxlen=AUSSEHEN_FENSTER),
                     "geburt": (e["x"], e["y"]), "spur": collections.deque(maxlen=RUHE_BILDER), "schritt": (0.0, 0.0)}
                self.bahnen.append(b)
            b["x"], b["y"], b["fehlt"], b["gesehen"] = e["x"], e["y"], 0, True
            b["spur"].append((e["x"], e["y"]))
            if "braun" in e: b["aussehen"].append(1 if e["braun"] >= BRAUN_MIN else 0)                  # 1.4: Aussehen je Bild
            if not b["bewegt_je"] and np.hypot(e["x"] - b["geburt"][0], e["y"] - b["geburt"][1]) >= RUHE_WEG: b["bewegt_je"] = True; b["ruht"] = False
            if b["bewegt_je"] and len(b["spur"]) >= RUHE_BILDER:
                x0, y0 = b["spur"][0]; b["ruht"] = max(np.hypot(x - x0, y - y0) for x, y in b["spur"]) < RUHE_WEG
            e["nr"], e["alter"], e["ruht"], e["schritt"] = b["nr"], b["alter"], bool(b["ruht"]), [round(b["schritt"][0], 1), round(b["schritt"][1], 1)]
            aussehen_ok = (not b["aussehen"]) or (sum(b["aussehen"]) >= AUSSEHEN_ANTEIL * len(b["aussehen"]))   # ohne Farbbild: kein Einwand
            if b["treffer"] < MIN_TREFFER or not aussehen_ok: continue                                # 1.4: ohne Aussehen keine Meldung
            b["gemeldet"] = True
            (ruhend if e["ruht"] else bewegt).append(e)
        for b in self.bahnen:
            if not b["gesehen"]: b["fehlt"] += 1; b["treffer"] = 0
        self.bahnen = [b for b in self.bahnen if b["fehlt"] <= (GEDAECHTNIS_BESTAETIGT if b["gemeldet"] else GEDAECHTNIS)][-60:]
        return bewegt, ruhend


# ------------------------------------------------------------------ 3. Anzeige
def punkt_lage(t):
    """1.3: quer zur Koerperachse, feste Seite (Senkrechte mit positivem y, sonst positivem x), halbe Breite + Abstand."""
    B = float(t.get("mB") or 15.0); w = np.radians(float(t.get("w", 0.0)))
    ex, ey = -np.sin(w), np.cos(w)                      # Senkrechte zur Achse (cos w, sin w)
    if ey < 0 or (abs(ey) < 1e-6 and ex < 0): ex, ey = -ex, -ey
    r = B / 2 + PUNKT_ABSTAND
    return int(round(t["x"] + ex * r)), int(round(t["y"] + ey * r))


def markieren(im, tiere, ruhend=()):
    """Punkt je gemeldetem Tier: Bahnfarbe fuer bewegte, grau fuer ruhende (1.4)."""
    h, w = im.shape[:2]
    for t, f in [(t, FARBEN[t["nr"] % len(FARBEN)]) for t in tiere] + [(t, (120, 120, 120)) for t in ruhend]:
        px, py = punkt_lage(t); px = min(max(px, PUNKT_RADIUS + 2), w - PUNKT_RADIUS - 3); py = min(max(py, PUNKT_RADIUS + 2), h - PUNKT_RADIUS - 3)
        cv2.circle(im, (px, py), PUNKT_RADIUS + 2, (255, 255, 255), -1, cv2.LINE_AA); cv2.circle(im, (px, py), PUNKT_RADIUS, f, -1, cv2.LINE_AA)
    return im


def zaehlen(n_tiere, t):
    uhr = time.strftime("%Y-%m-%dT%H:00", time.localtime(t)); l = ZAEHLER["laufend"]
    if l is None or l["uhr"] != uhr:
        if l is not None:
            l["mittel"] = round(l["summe"] / max(l["bilder"], 1), 2); del l["summe"]; ZAEHLER["stunden"] = (ZAEHLER["stunden"] + [l])[-72:]
        l = ZAEHLER["laufend"] = {"uhr": uhr, "hoechstens": 0, "summe": 0, "bilder": 0}
    l["bilder"] += 1; l["summe"] += n_tiere; l["hoechstens"] = max(l["hoechstens"], n_tiere)


# ------------------------------------------------------------------ 4. Aufzeichnung (uebernommen, Rahmen und Nummern nur in der Ablage)
def aufraeumen():
    namen = sorted({os.path.basename(p)[:-6] for p in glob.glob(os.path.join(ABLAGE, "*.jsonl"))})
    grenze = time.strftime("%Y%m%d_%H%M%S", time.localtime(time.time() - 60 * BEHALTEN_MIN))
    for alt in [n for n in namen[:-BEHALTEN] if n < grenze]:
        for p in glob.glob(os.path.join(ABLAGE, alt + "*")):
            try: os.remove(p)
            except OSError: pass
        log(f"alte Aufnahme {alt} geloescht")


def ablegen(name, bilder, zeiten, funde, fps, zusatz):
    os.makedirs(ABLAGE, exist_ok=True)
    erst = cv2.imdecode(np.frombuffer(bilder[0], np.uint8), cv2.IMREAD_COLOR); h, w = erst.shape[:2]
    roh = cv2.VideoWriter(os.path.join(ABLAGE, name + ".avi"), cv2.VideoWriter_fourcc(*"MJPG"), fps, (w, h))
    mit = cv2.VideoWriter(os.path.join(ABLAGE, name + "_rahmen.avi"), cv2.VideoWriter_fourcc(*"MJPG"), fps, (w, h))
    tafel, schnitte = [], []
    for i, (b, tr) in enumerate(zip(bilder, funde)):
        im = cv2.imdecode(np.frombuffer(b, np.uint8), cv2.IMREAD_COLOR); roh.write(im); im2 = im.copy()
        for t in tr:
            f = (120, 120, 120) if t["ruht"] else FARBEN[t["nr"] % len(FARBEN)]
            cv2.rectangle(im2, (t["rx"] - 2, t["ry"] - 2), (t["rx"] + t["rb"] + 2, t["ry"] + t["rh"] + 2), f, 1)
            cv2.putText(im2, ("ruht " if t["ruht"] else "") + str(t["nr"]), (t["rx"], max(11, t["ry"] - 4)), cv2.FONT_HERSHEY_SIMPLEX, .45, f, 1, cv2.LINE_AA)
            if not t["ruht"] and len(schnitte) < 48:
                cx, cy = int(t["x"]), int(t["y"]); r = 40; s = im2[max(0, cy - r):cy + r, max(0, cx - r):cx + r]
                if s.size:
                    s = cv2.copyMakeBorder(s, 0, 2 * r - s.shape[0], 0, 2 * r - s.shape[1], cv2.BORDER_CONSTANT, value=(30, 30, 30))
                    cv2.putText(s, f"{i}:{t['nr']}", (2, 12), cv2.FONT_HERSHEY_SIMPLEX, .4, (255, 255, 255), 1, cv2.LINE_AA); schnitte.append(s)
        cv2.putText(im2, f"{i} {zeiten[i]-zeiten[0]:.2f}s {len(tr)}", (6, h - 6), cv2.FONT_HERSHEY_SIMPLEX, .45, (255, 255, 255), 1, cv2.LINE_AA)
        mit.write(im2); tafel.append(im2)
    roh.release(); mit.release()
    kh, kw, sp = 120, 160, 8; tb = np.full((((len(tafel) + sp - 1) // sp) * kh, sp * kw, 3), 30, np.uint8)
    for k, im in enumerate(tafel):
        r_, c_ = divmod(k, sp); tb[r_*kh:(r_+1)*kh, c_*kw:(c_+1)*kw] = cv2.resize(im, (kw, kh))
    cv2.imwrite(os.path.join(ABLAGE, name + "_tafel.jpg"), tb, [cv2.IMWRITE_JPEG_QUALITY, 62])
    if schnitte:
        ab = np.full((((len(schnitte) + 7) // 8) * 80, 8 * 80, 3), 30, np.uint8)
        for k, s in enumerate(schnitte):
            r_, c_ = divmod(k, 8); ab[r_*80:(r_+1)*80, c_*80:(c_+1)*80] = s
        cv2.imwrite(os.path.join(ABLAGE, name + "_ausschnitte.jpg"), ab, [cv2.IMWRITE_JPEG_QUALITY, 80])
    with sperre: mst = LIVE["massstab_um_px"]
    with open(os.path.join(ABLAGE, name + ".jsonl"), "w", encoding="utf-8") as f:
        f.write(json.dumps({"name": name, "fassung": "auswertung " + FASSUNG, "bilder": len(bilder), "fps": round(fps, 2), "sekunden": round(zeiten[-1] - zeiten[0], 3),
                            "ausschnitt": [AUS[0].start, AUS[0].stop, AUS[1].start, AUS[1].stop], "massstab_um_px": mst, "koerper_anteil": KOERPER_ANTEIL,
                            "tor": TOR, "min_treffer": MIN_TREFFER, "uhr": time.strftime("%Y-%m-%d %H:%M:%S")}) + "\n")
        for i, (z, tr) in enumerate(zip(zeiten, funde)):
            f.write(json.dumps(dict({"b": i, "t": round(z - zeiten[0], 4), "objekte": tr}, **zusatz[i]), separators=(",", ":")) + "\n")
    n_mit = sum(1 for x in funde if any(not t["ruht"] for t in x))
    log(f"{name}: {len(bilder)} Bilder, {n_mit} mit bewegtem Tier, {fps:.1f}/s, {len(schnitte)} Ausschnitte"); aufraeumen(); return n_mit


def schreiber():
    while True:
        name, bilder, zeiten, funde, fps, zusatz = SCHREIBER.get()
        try: mitz = ablegen(name, bilder, zeiten, funde, fps, zusatz)
        except Exception as e: log(f"Ablage {name} fehlgeschlagen: {e}"); mitz = -1
        with sperre:
            Z["aufnahmen"] += 1; Z["letzte"] = {"name": name, "bilder": len(bilder), "mit_objekt": mitz, "ausgeloest_uhr": Z["ausgeloest_uhr"], "dauer_s": round(zeiten[-1] - zeiten[0], 1), "uhr": time.strftime("%H:%M:%S")}


def massstab_holen():
    while True:
        try:
            d = json.load(urllib.request.urlopen("http://127.0.0.1:8091/stand", timeout=4))
            with sperre: LIVE["massstab_um_px"] = d.get("massstab_um_px")
        except Exception: pass
        time.sleep(30)


# ------------------------------------------------------------------ Hauptschleife
def lauf(quelle=STROM, einmal=None):
    E = Erkenner(); V = Verfolger(); ring = collections.deque(maxlen=VORLAUF)
    folge = 0; auf = None; n = 0; t_rate = time.time(); n_rate = 0; t_start = time.time()
    quelle_it = ((b, t_start + i / BILDRATE) for i, b in enumerate(einmal)) if einmal is not None else strom(quelle)
    for b, t in quelle_it:
        with sperre: zuschauer = BILD["zuschauer"]
        farbbild = cv2.imdecode(np.frombuffer(b, np.uint8), cv2.IMREAD_COLOR)        # 1.4: Farbbild immer (Aussehens-Nachweis)
        if farbbild is None: continue
        g = cv2.cvtColor(farbbild, cv2.COLOR_BGR2GRAY)
        n += 1; n_rate += 1
        if time.time() - t_rate >= 5:
            with sperre: Z["bilder_s"] = round(n_rate / (time.time() - t_rate), 1)
            t_rate, n_rate = time.time(), 0
        n_fg, erk = E.schritt(g[AUS], farbbild[AUS]); bewegt, ruhend = V.schritt(erk)
        with sperre:
            LIVE["t"] = t; LIVE["tiere"] = bewegt; LIVE["ruhend"] = ruhend
            Z["bilder"] = n; Z["vordergrund"] = n_fg; Z["objekte"] = len(bewegt) + len(ruhend); Z["helligkeit"] = round(E.hell, 1); Z["nachlernen"] = E.nachlernen; Z["bahnen_offen"] = len(V.bahnen)
            if E.wechsel != Z["beleuchtungswechsel"]: Z["beleuchtungswechsel"] = E.wechsel; Z["letzter_wechsel_uhr"] = time.strftime("%H:%M:%S")
            if auf is None: Z["phase"] = "wacht" if E.gelernt >= 60 else f"lernt {E.gelernt}/60"
        zaehlen(len(bewegt) + len(ruhend), t)                                          # 1.4: ruhende Tiere zaehlen mit
        if zuschauer and n % ANZEIGE_JEDES == 0:
            ok_, jpg = cv2.imencode(".jpg", markieren(farbbild, bewegt, ruhend), [cv2.IMWRITE_JPEG_QUALITY, ANZEIGE_GUETE])
            if ok_:
                with bild_da: BILD["jpeg"] = jpg.tobytes(); BILD["n"] = n; bild_da.notify_all()
        alle = bewegt + ruhend; zusatz = {"hell": round(E.hell, 1), "erkannt": len(erk)}
        folge = folge + 1 if bewegt else 0
        with sperre: Z["in_folge"] = folge
        if auf is None:
            ring.append((b, t, alle, zusatz))
            if folge >= IN_FOLGE:
                auf = {"t0": t, "b": [x[0] for x in ring], "z": [x[1] for x in ring], "f": [x[2] for x in ring], "v": [x[3] for x in ring], "name": time.strftime("%Y%m%d_%H%M%S", time.localtime(t))}
                with sperre: Z["zeichnet"] = True; Z["phase"] = "zeichnet auf"; Z["ausgeloest_uhr"] = time.strftime("%H:%M:%S"); Z["aufnahme_s"] = 0.0
                log(f"AUSGELOEST: {len(bewegt)} bewegte Tiere, {n_fg} Vordergrundpunkte, {folge} Bilder in Folge")
        else:
            auf["b"].append(b); auf["z"].append(t); auf["f"].append(alle); auf["v"].append(zusatz); dauer = t - auf["t0"]
            with sperre: Z["rest_s"] = round(max(0.0, SEKUNDEN - dauer), 2); Z["aufnahme_s"] = round(dauer, 1)
            if (dauer >= SEKUNDEN and not bewegt) or dauer >= HOECHSTENS_S or (einmal is not None and n == len(einmal)):
                d = auf["z"][-1] - auf["z"][0]; SCHREIBER.put((auf["name"], auf["b"], auf["z"], auf["f"], len(auf["b"]) / d if d > 0 else 25.0, auf["v"]))
                with sperre: Z["zeichnet"] = False; Z["rest_s"] = 0.0; Z["phase"] = "wacht"
                auf = None; folge = 0; ring.clear()


class Auskunft(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def _json(self, d):
        b = json.dumps(d).encode(); self.send_response(200); self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*"); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        p = self.path.split("?")[0]
        if p in ("/", "/stand"):
            with sperre: d = dict(Z)
            d["laeuft_min"] = round((time.time() - Z["seit"]) / 60, 1); self._json(d)
        elif p == "/punkte":
            with sperre: self._json({"t": LIVE["t"], "alter_s": round(time.time() - LIVE["t"], 2) if LIVE["t"] else None, "breite": LIVE["breite"], "hoehe": LIVE["hoehe"], "massstab_um_px": LIVE["massstab_um_px"], "tiere": LIVE["tiere"], "erinnert": [], "ruhend": LIVE["ruhend"]})
        elif p == "/zaehler":
            with sperre:
                l = ZAEHLER["laufend"]; d = {"stunden": list(ZAEHLER["stunden"]), "laufend": (dict(l, mittel=round(l["summe"] / max(l["bilder"], 1), 2)) if l else None), "fassung": FASSUNG}
            if d["laufend"]: d["laufend"].pop("summe", None)
            self._json(d)
        elif p in ("/strom_marken", "/strom_rahmen"):
            self.send_response(200); self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=bild"); self.send_header("Cache-Control", "no-cache"); self.send_header("Access-Control-Allow-Origin", "*"); self.end_headers()
            with sperre: BILD["zuschauer"] += 1
            letzte = -1
            try:
                while True:
                    with bild_da:
                        if BILD["n"] == letzte: bild_da.wait(timeout=1.0)
                        jpg, letzte = BILD["jpeg"], BILD["n"]
                    if not jpg: continue
                    self.wfile.write(b"--bild\r\nContent-Type: image/jpeg\r\nContent-Length: " + str(len(jpg)).encode() + b"\r\n\r\n" + jpg + b"\r\n"); self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError, OSError): pass
            finally:
                with sperre: BILD["zuschauer"] = max(0, BILD["zuschauer"] - 1)
        else:
            self.send_response(404); self.end_headers()


def main():
    class S(socketserver.ThreadingTCPServer): allow_reuse_address = True; daemon_threads = True
    threading.Thread(target=S(("", PORT), Auskunft).serve_forever, daemon=True).start()
    threading.Thread(target=schreiber, daemon=True).start(); threading.Thread(target=massstab_holen, daemon=True).start()
    log(f"Auswertung {FASSUNG} -- Erkennung, Verfolgung (Tor {TOR:.0f} px, {MIN_TREFFER} Treffer), Anzeige, Aufzeichnung; :{PORT}/stand, /punkte, /zaehler, /strom_marken")
    lauf()


if __name__ == "__main__":
    sys.exit(main())
