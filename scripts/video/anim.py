"""LinkedIn speedrun film: AI makes a real board change (ECO) on the ECP5 Mini.
Intro with typed task -> make room -> the I2C dead end -> routing -> DRC/parity -> SPICE -> end card.
usage: FORMAT=square|vertical python3 anim.py [--test t1,t2,...]"""
import os, sys, json, math, subprocess
import numpy as np, cairo

SQ = os.environ.get("FORMAT", "square") == "square"
W, H, FPS = (1080, 1080, 30) if SQ else (1080, 1920, 30)
D = "/home/claude/ecovid/"; OUT = D + ("sq/" if SQ else "vt/"); os.makedirs(OUT, exist_ok=True)
G = json.load(open(D + "geo.json"))
BG = (.07, .08, .10); YEL = (1, .82, .25); GRN = (.35, .9, .5); INK = (1, 1, 1); SUB = (.75, .8, .9); MUT = (.55, .6, .7)
PINK = (1, .32, .55); NF = (1.0, .55, .15); NB = (.25, .85, 1.0); RED = (1, .3, .3)
clip = lambda x: max(0.0, min(1.0, x))
ease = lambda t: (lambda u: u * u * (3 - 2 * u))(clip(t))
def ramp(t, a, b): return clip((t - a) / (b - a)) if b > a else float(t >= a)

# ------------------------------------------------------------------ layout
if SQ:
    TITLE_Y, SUB_Y = 62, 108
    VIEW = (20, 138, 690, 690)                 # board viewport
    SIDE = (730, 150, 330, 670)                # stats / legend column
    TIMER_Y, STEP_Y, CAP_Y = 925, 978, 1040
    SCOPES = [(40, 150, 1000, 330), (40, 500, 1000, 330)]
else:
    TITLE_Y, SUB_Y = 150, 215
    VIEW = (20, 290, 1040, 1040)
    SIDE = (40, 1360, 1000, 220)
    TIMER_Y, STEP_Y, CAP_Y = 1700, 1765, 1840
    SCOPES = [(40, 330, 1000, 500), (40, 880, 1000, 500)]
X0, X1, Y0, Y1 = 95.6, 124.4, 80.9, 109.1

# ------------------------------------------------------------------ timeline
EV = []
TYPE_LINES = [("board ", "ECP5 FPGA \"Mini\", 4 layers, fully routed"),
              ("      ", "(open-source design, not mine)"),
              ("goal  ", "add a Qwiic I2C port"),
              ("goal  ", "swap the JTAG header for Tag-Connect pads"),
              ("rule  ", "don't touch the dense BGA fan-out"),
              ("done  ", "0 new DRC errors, schematic = PCB")]
HEAD = "Can AI make a real change to a finished PCB?"
CPS = 34.0
t = 0.6; T_HEAD = t; t += len(HEAD) / 28 + 0.5
LINE_T = []
for a, b in TYPE_LINES:
    LINE_T.append(t); n = len(a + b)
    for k in range(0, n, 2): EV.append((t + k / CPS, "type"))
    t += n / CPS + 0.28
T_GO = t + 0.7; EV.append((T_GO, "go"))
T1 = T_GO + 0.6                                       # part 1: make room
P1 = dict(j2=T1 + 0.3, leds=T1 + 1.9, shift=T1 + 3.4, j6=T1 + 4.9, bot=T1 + 6.0, fid=T1 + 7.0)
for k in ("j2", "leds"): EV.append((P1[k], "mark")); EV.append((P1[k] + 0.8, "remove"))
EV += [(P1["shift"], "shift"), (P1["j6"], "place"), (P1["bot"], "place"), (P1["bot"] + 0.35, "place"), (P1["fid"], "move")]
T2 = T1 + 8.3                                         # part 2: I2C dead end
SCAN0, SCAN1 = T2 + 0.9, T2 + 4.4
for k in range(45): EV.append((SCAN0 + (SCAN1 - SCAN0) * k / 45, "scan"))
T_FAIL = SCAN1 + 0.1; EV.append((T_FAIL, "buzz"))
T_FIX = T_FAIL + 1.5; EV.append((T_FIX, "fix"))
T3 = T_FIX + 2.4                                      # part 3: routing
EV.append((T3, "part"))
nets = []
for s in G["route"]:
    if not nets or nets[-1][0] != s[5]: nets.append([s[5], []])
    nets[-1][1].append(s)
lens = [sum(math.dist(s[:2], s[2:4]) for s in ss) for _, ss in nets]
R0, R1 = T3 + 0.8, T3 + 10.8
SEG_T = []                                            # (t_on, t_full, seg)
tc = R0; tot = sum(lens)
for (name, ss), L in zip(nets, lens):
    dur = (R1 - R0) * L / tot
    for s in ss:
        l = math.dist(s[:2], s[2:4]); d = dur * l / max(L, 1e-6); SEG_T.append((tc, tc + d, s)); tc += d
for k, (a, b, s) in enumerate(SEG_T):
    if k % 3 == 0: EV.append((a, "wire"))
VIA_T = []
for v in G["new_vias"]:
    tt = min((a for a, b, s in SEG_T if math.dist(v[:2], s[:2]) < 0.05 or math.dist(v[:2], s[2:4]) < 0.05), default=R1)
    VIA_T.append((tt, v)); EV.append((tt, "via"))
TX = R1 + 0.5; EV.append((TX + 0.2, "explode"))     # exploded layer view
TA = TX + 6.6; EV.append((TA + 1.0, "wipe")); EV.append((TA + 4.6, "wipe")); EV.append((TA + 2.4, "callout")); EV.append((TA + 5.9, "callout"))
T4 = TA + 7.6                                         # part 4: checks
T_DRC, T_PAR = T4 + 0.4, T4 + 1.5; EV += [(T_DRC, "check"), (T_PAR, "check2")]
T5 = T4 + 3.6; EV.append((T5, "part"))                # part 5: SPICE
S_I2C, S_TCK = T5 + 0.8, T5 + 4.6
T_END = T5 + 9.4; EV.append((T_END, "end"))
T_TOTAL = T_END + 5.0
PARTS = [(0, "the task"), (T1, "part 1: make room"), (T2, "part 2: where does I²C go?"), (T3, "part 3: route it"), (TX, "which layers changed?"), (TA, "assembled: before \u2192 after"),
         (T4, "part 4: check it"), (T5, "part 5: does it work? (SPICE)"), (T_END, "done")]
STEPS = [(T1, "01  Remove the JTAG header"), (P1["leds"], "02  Drop 3 RGB LEDs (D9–D11)"), (P1["shift"], "03  Shift D4–D8 down 0.20 mm"),
         (P1["j6"], "04  Place Qwiic J6 (top)"), (P1["bot"], "05  Pull-ups + TC2050 pads (bottom)"), (P1["fid"], "06  Move 2 fiducials"),
         (T2, "07  Look for 2 free FPGA pins"), (T_FAIL, "07  45 of 45 free balls are boxed in"), (T_FIX, "08  Share PORT_H0/H1 instead"),
         (T3, "09  Route 16 nets, rip-up & reroute"), (TX, "10  Exploded view: 4 copper layers"), (TA, "11  3D render: before vs after"), (T4, "12  DRC + schematic parity"), (T5, "13  SPICE: I²C + JTAG clock"), (T_END, "")]

# ------------------------------------------------------------------ drawing helpers
def font(c, size, bold=False, mono=False):
    c.select_font_face("DejaVu Sans Mono" if mono else "DejaVu Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL); c.set_font_size(size)
def text(c, s, x, y, size, col=INK, bold=False, mono=False, align="left", alpha=1.0):
    font(c, size, bold, mono); e = c.text_extents(s)
    xx = x - (e.x_advance / 2 if align == "center" else e.x_advance if align == "right" else 0)
    c.set_source_rgba(*col, alpha); c.move_to(xx, y); c.show_text(s); return e.x_advance
def rrect(c, x, y, w, h, r):
    c.new_sub_path(); c.arc(x + w - r, y + r, r, -math.pi / 2, 0); c.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    c.arc(x + r, y + h - r, r, math.pi / 2, math.pi); c.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2); c.close_path()
def badge(c, s, x, y, size, col, alpha=1.0, align="left", bg=(0, 0, 0, .75)):
    font(c, size, True); e = c.text_extents(s)
    xx = x - (e.x_advance / 2 if align == "center" else 0)
    c.set_source_rgba(bg[0], bg[1], bg[2], bg[3] * alpha); rrect(c, xx - 8, y - size - 6, e.x_advance + 16, size + 16, 6); c.fill()
    c.set_source_rgba(*col, alpha); c.move_to(xx, y); c.show_text(s)

# camera: (cx, cy, zoom) in mm; zoom 1 = full crop fits viewport
FULL = ((X0 + X1) / 2, (Y0 + Y1) / 2, 1.0)
LEFT = (104.8, 94.3, 1.4)
CAM = [(0, FULL), (T1 + 0.2, FULL), (T1 + 1.0, LEFT), (T2 - 0.1, LEFT), (T2 + 0.6, FULL), (T_FIX + 0.2, FULL), (T_FIX + 1.0, LEFT),
       (R1, LEFT), (R1 + 0.8, FULL), (T_TOTAL, FULL)]
def cam(t):
    for (a, ca), (b, cb) in zip(CAM, CAM[1:]):
        if t <= b:
            u = ease(ramp(t, a, b)); return tuple(ca[i] + (cb[i] - ca[i]) * u for i in range(3))
    return CAM[-1][1]
def view_tf(c, t):
    vx, vy, vw, vh = VIEW; cx, cy, z = cam(t)
    s = min(vw / (X1 - X0), vh / (Y1 - Y0)) * z
    c.translate(vx + vw / 2, vy + vh / 2); c.scale(s, s); c.translate(-cx, -cy); return s
def to_px(t, x, y):
    vx, vy, vw, vh = VIEW; cx, cy, z = cam(t); s = min(vw / (X1 - X0), vh / (Y1 - Y0)) * z
    return vx + vw / 2 + (x - cx) * s, vy + vh / 2 + (y - cy) * s

DIM_F, DIM_B = (.48, .27, .23), (.20, .32, .50)
def seg(c, x1, y1, x2, y2, w, col, a=1.0):
    c.move_to(x1, y1); c.line_to(x2, y2); c.set_line_width(w); c.set_source_rgba(*col, a); c.stroke()
def pads(c, plist, layer, col, a=1.0, dy=0.0, scale=1.0):
    for ln, pts, ref, net, hole in plist:
        if ln != layer: continue
        if scale != 1.0:
            mx = sum(p[0] for p in pts) / len(pts); my = sum(p[1] for p in pts) / len(pts)
            pts = [(mx + (p[0] - mx) * scale, my + (p[1] - my) * scale) for p in pts]
        c.move_to(pts[0][0], pts[0][1] + dy); [c.line_to(p[0], p[1] + dy) for p in pts[1:]]; c.close_path()
    c.set_source_rgba(*col, a); c.fill()

def draw_board(c, t, dim=1.0):
    c.save(); vx, vy, vw, vh = VIEW; c.rectangle(vx, vy, vw, vh); c.clip()
    s = view_tf(c, t)
    o = G["outline"]; c.move_to(*o[0]); [c.line_to(*p) for p in o[1:]]; c.close_path()
    c.set_source_rgba(.10, .16, .12, dim); c.fill_preserve(); c.set_source_rgba(.8, .75, .35, dim); c.set_line_width(0.07); c.stroke()
    c.set_line_cap(cairo.LINE_CAP_ROUND)
    rem_a = 1 - ramp(t, P1["leds"] + 0.8, P1["leds"] + 1.3)          # removed copper fades with the LEDs
    pink = ramp(t, P1["j2"], P1["j2"] + 0.25)
    for layer, dc, nc in (("B.Cu", DIM_B, NB), ("F.Cu", DIM_F, NF)):
        lw_a = .8 if layer == "B.Cu" else 1.0
        for tr in G["base_tracks"]:
            if tr[5] == layer: c.move_to(tr[0], tr[1]); c.line_to(tr[2], tr[3])
        c.set_line_width(0.127); c.set_source_rgba(*dc, lw_a * dim); c.stroke()
        # removed copper: highlighted, then gone
        if rem_a > 0:
            for tr in G["removed"]:
                if tr[5] != layer or tr[6] in ("/PORT_A0", "/PORT_A4"): continue
                is_j = "FPGA Config" in tr[6]
                mt = P1["j2"] if is_j else P1["leds"]
                hl = ramp(t, mt, mt + 0.25); gone = ramp(t, mt + 0.8, mt + 1.3)
                col = tuple(dc[i] + (PINK[i] - dc[i]) * hl for i in range(3))
                seg(c, tr[0], tr[1], tr[2], tr[3], 0.127 + 0.08 * hl, col, (1 - gone) * dim)
        # PORT_A0 / A4 nudge
        u = ease(ramp(t, P1["shift"] + 0.2, P1["shift"] + 0.9))
        for old, new in zip(G["nudge_old"], G["nudge"]):
            if new[5] != layer: continue
            p = [old[i] + (new[i] - old[i]) * u for i in range(4)]
            glow = ramp(t, P1["shift"], P1["shift"] + 0.3) * (1 - ramp(t, T2, T2 + 0.6))
            col = tuple(dc[i] + (NF[i] - dc[i]) * glow for i in range(3))
            seg(c, *p, 0.127 + 0.06 * glow, col, dim)
        # new routing
        for a, b, sg in SEG_T:
            if sg[4] != layer or t < a: continue
            f = clip((t - a) / max(b - a, 1e-6)); x2 = sg[0] + (sg[2] - sg[0]) * f; y2 = sg[1] + (sg[3] - sg[1]) * f
            seg(c, sg[0], sg[1], x2, y2, 0.15, nc, dim)
    # pads
    for layer, col in (("B.Cu", (.42, .40, .33)), ("F.Cu", (.66, .62, .48))):
        pads(c, G["base_pads"], layer, col, dim)
        for r in ("D4", "D5", "D6", "D7", "D8"):
            dy = -0.20 * (1 - ease(ramp(t, P1["shift"], P1["shift"] + 0.9)))
            pads(c, G["pads_after"][r], layer, col, dim, dy=dy)
        for r in ("FID5", "FID2"):
            u = ease(ramp(t, P1["fid"], P1["fid"] + 0.7))
            if u < 1: pads(c, G["pads_before"][r], layer, col, (1 - u) * dim)
            if u > 0: pads(c, G["pads_after"][r], layer, col, u * dim)
        for r, mt in (("J2", P1["j2"]), ("D9", P1["leds"]), ("D10", P1["leds"]), ("D11", P1["leds"])):
            hl = ramp(t, mt, mt + 0.25); gone = ramp(t, mt + 0.8, mt + 1.3)
            if gone < 1:
                cc = tuple(col[i] + (PINK[i] - col[i]) * hl for i in range(3)); pads(c, G["pads_before"][r], layer, cc, (1 - gone) * dim)
        for r, mt in (("J6", P1["j6"]), ("R31", P1["bot"]), ("R32", P1["bot"]), ("J2", P1["bot"] + 0.35)):
            u = ramp(t, mt, mt + 0.35)
            if u > 0:
                fresh = 1 - ramp(t, T3, T3 + 1.0)
                cc = tuple(col[i] + ((1, .92, .3)[i] - col[i]) * fresh for i in range(3))
                pads(c, G["pads_after"][r], layer, cc, u * dim, scale=1 + 0.6 * (1 - ease(u)))
    # vias
    for v in G["base_vias"]:
        c.new_sub_path(); c.arc(v[0], v[1], v[2] / 2, 0, 2 * math.pi)
    c.set_source_rgba(.55, .55, .55, dim); c.fill()
    for v in G["rem_vias"]:
        mt = P1["j2"] if "FPGA Config" in v[4] else P1["leds"]
        g_ = ramp(t, mt + 0.8, mt + 1.3)
        if g_ < 1: c.new_sub_path(); c.arc(v[0], v[1], v[2] / 2, 0, 2 * math.pi); c.set_source_rgba(*PINK, (1 - g_) * dim); c.fill()
    for tt, v in VIA_T:
        if t >= tt:
            pop = 1 + 0.8 * (1 - ease(ramp(t, tt, tt + 0.25)))
            c.new_sub_path(); c.arc(v[0], v[1], v[2] / 2 * pop, 0, 2 * math.pi); c.set_source_rgba(1, 1, 1, dim); c.fill()
    for v in G["base_vias"] + [v for tt, v in VIA_T if t >= tt]:
        c.new_sub_path(); c.arc(v[0], v[1], v[3] / 2, 0, 2 * math.pi)
    c.set_source_rgba(.08, .08, .08, dim); c.fill()
    # part 2: ball scan + fix
    if SCAN0 - 0.3 < t < T3 + 0.5:
        a2 = ramp(t, SCAN0 - 0.3, SCAN0) * (1 - ramp(t, T_FIX + 0.6, T_FIX + 1.2))
        for k, (x, y) in enumerate(G["balls"]):
            tk = SCAN0 + (SCAN1 - SCAN0) * k / 45
            if t < tk: continue
            p = ease(ramp(t, tk, tk + 0.15)); r = 0.42
            c.new_sub_path(); c.arc(x, y, r * (1.6 - 0.6 * p), 0, 2 * math.pi); c.set_source_rgba(*RED, 0.85 * a2); c.set_line_width(0.09); c.stroke()
            d = 0.25; c.move_to(x - d, y - d); c.line_to(x + d, y + d); c.move_to(x + d, y - d); c.line_to(x - d, y + d); c.set_line_width(0.08); c.stroke()
        if t > T_FIX:                                  # H0/H1 straight down to J6
            u = ease(ramp(t, T_FIX, T_FIX + 0.7)); a3 = 1 - ramp(t, T3 + 0.2, T3 + 0.6)
            for (x0, y0), (x1, y1) in (((97.71, 83.5), (101.53, 90.53)), ((100.25, 83.5), (101.53, 89.53))):
                c.move_to(x0, y0); c.line_to(x0 + (x1 - x0) * u, y0 + (y1 - y0) * u)
                c.set_source_rgba(*GRN, a3); c.set_line_width(0.12); c.set_dash([0.35, 0.2]); c.stroke(); c.set_dash([])
                c.new_sub_path(); c.arc(x0, y0, 0.95, 0, 2 * math.pi); c.set_source_rgba(*GRN, a3); c.set_line_width(0.14); c.stroke()
    # ratsnest of nets still to route
    if T3 < t < R1:
        for (name, ss) in nets:
            first = next(a for a, b, sg in SEG_T if sg[5] == name)
            if t >= first: continue
            p0, p1 = ss[0][:2], ss[-1][2:4]
            c.move_to(*p0); c.line_to(*p1); c.set_source_rgba(1, .95, .3, 0.8 * ramp(t, T3, T3 + 0.4)); c.set_line_width(0.06); c.set_dash([0.25, 0.15]); c.stroke(); c.set_dash([])
    c.restore()
    return s

# ------------------------------------------------------------------ labels on the board (pixel space, follow the camera)
def board_labels(c, t):
    L = []
    if P1["j2"] < t < P1["j2"] + 1.5: L.append(("JTAG header: too big", 96.9, 87.6, PINK, ramp(t, P1["j2"], P1["j2"] + .2) * (1 - ramp(t, P1["j2"] + 1.2, P1["j2"] + 1.5))))
    if P1["leds"] < t < P1["leds"] + 1.5: L.append(("D9–D11 go", 103.4, 86.6, PINK, ramp(t, P1["leds"], P1["leds"] + .2) * (1 - ramp(t, P1["leds"] + 1.2, P1["leds"] + 1.5))))
    if P1["shift"] < t < P1["shift"] + 1.5: L.append(("D4–D8 ↓ 0.20 mm", 103.6, 97.5, NF, ramp(t, P1["shift"], P1["shift"] + .2) * (1 - ramp(t, P1["shift"] + 1.2, P1["shift"] + 1.5))))
    if P1["j6"] < t < T2 + 0.3: L.append(("Qwiic J6", 96.5, 93.4, (1, .92, .3), ramp(t, P1["j6"], P1["j6"] + .2) * (1 - ramp(t, T2, T2 + .3))))
    if P1["bot"] < t < T2 + 0.3: L.append(("TC2050 pads (bottom)", 99.8, 101.6, (1, .92, .3), ramp(t, P1["bot"], P1["bot"] + .2) * (1 - ramp(t, T2, T2 + .3))))
    if SCAN0 < t < T_FIX + 0.8:
        n = min(45, int((t - SCAN0) / (SCAN1 - SCAN0) * 45) + 1)
        L.append((f"free FPGA balls checked: {n}/45  ·  reachable: 0", 99.0, 107.4, RED, ramp(t, SCAN0, SCAN0 + .2) * (1 - ramp(t, T_FIX + .5, T_FIX + .8))))
    if T_FAIL < t < T_FIX + 0.8: L.append(("dense fan-out blocks every path", 99.0, 105.3, RED, ramp(t, T_FAIL, T_FAIL + .2) * (1 - ramp(t, T_FIX + .5, T_FIX + .8))))
    if T_FIX < t < T3 + 0.5: L.append(("J4 pins H0/H1 sit right above J6", 99.2, 86.9, GRN, ramp(t, T_FIX + .3, T_FIX + .5) * (1 - ramp(t, T3 + .2, T3 + .5))))
    for s, x, y, col, a in L:
        if a <= 0: continue
        px, py = to_px(t, x, y); badge(c, s, px, py, 20 if SQ else 26, col, a)

# ------------------------------------------------------------------ side panel / stats
def stats(t):
    nseg = sum(1 for a, b, s in SEG_T if t >= b); nvia = sum(1 for tt, v in VIA_T if t >= tt)
    rem = (1 if t > P1["j2"] + 0.8 else 0) + (3 if t > P1["leds"] + 0.8 else 0)
    add = (1 if t > P1["j6"] else 0) + (2 if t > P1["bot"] else 0) + (1 if t > P1["bot"] + 0.35 else 0)
    return [("parts removed", str(rem), PINK), ("parts added", str(add), (1, .92, .3)), ("new tracks", str(nseg + (6 if t > P1["shift"] + 0.9 else 0)), NF), ("new vias", str(nvia), INK)]
def side(c, t, a):
    if a <= 0: return
    x, y, w, h = SIDE; st = stats(t)
    if SQ:
        for k, (lab, val, col) in enumerate(st):
            yy = y + k * 112
            c.set_source_rgba(1, 1, 1, .06 * a); rrect(c, x, yy, w, 96, 12); c.fill()
            text(c, val, x + 22, yy + 62, 46, col, True, True, alpha=a); text(c, lab, x + 130, yy + 56, 22, SUB, alpha=a)
        yy = y + 4 * 112 + 20
        for k, (col, s) in enumerate(((NF, "new track, top"), (NB, "new track, bottom"), ((1, 1, 1), "new via"), (PINK, "removed"))):
            c.set_source_rgba(*col, a); c.rectangle(x + 4, yy + k * 36 - 12, 26, 8 if k < 2 else 8); c.fill()
            text(c, s, x + 44, yy + k * 36, 19, MUT, alpha=a)
    else:
        cw = (w - 3 * 16) / 4
        for k, (lab, val, col) in enumerate(st):
            xx = x + k * (cw + 16)
            c.set_source_rgba(1, 1, 1, .06 * a); rrect(c, xx, y, cw, 130, 14); c.fill()
            text(c, val, xx + cw / 2, y + 72, 52, col, True, True, "center", a); text(c, lab, xx + cw / 2, y + 112, 22, SUB, align="center", alpha=a)
        xx = x
        for col, s in ((NF, "new top"), (NB, "new bottom"), ((1, 1, 1), "new via"), (PINK, "removed")):
            c.set_source_rgba(*col, a); c.rectangle(xx, y + 168, 26, 8); c.fill(); xx += 36 + text(c, s, xx + 34, y + 178, 21, MUT, alpha=a) + 40

# ------------------------------------------------------------------ scopes (SPICE)
I2C = json.load(open(D + "i2c_results.json")); TCK = json.load(open(D + "tck_results.json"))
I2C_D = [np.loadtxt(D + f"fpga_{i}.dat") for i in range(4)]; TCK_D = [np.loadtxt(D + f"tck_{i}_1.dat") for i in range(3)]
CAT = [(.16, .47, .84), (.92, .41, .20), (.11, .69, .48), (.93, .63, .0)]
def scope(c, rect, title, xr, yr, curves, prog, hlines, band, xlabel, verdict, a, legend):
    x, y, w, h = rect
    c.set_source_rgba(.11, .12, .15, a); rrect(c, x, y, w, h, 14); c.fill()
    text(c, title, x + 20, y + 36, 24 if SQ else 30, INK, True, alpha=a)
    px0, py0, pw, ph = x + 70, y + 56, w - 90, h - 110
    fx = lambda v: px0 + (v - xr[0]) / (xr[1] - xr[0]) * pw; fy = lambda v: py0 + ph - (v - yr[0]) / (yr[1] - yr[0]) * ph
    c.set_line_width(1)
    for gy in np.arange(math.ceil(yr[0]), yr[1] + 1e-6, 1.0):
        c.move_to(px0, fy(gy)); c.line_to(px0 + pw, fy(gy)); c.set_source_rgba(1, 1, 1, .08 * a); c.stroke()
        text(c, f"{gy:.0f} V", px0 - 10, fy(gy) + 6, 15 if SQ else 19, MUT, align="right", alpha=a)
    if band:
        c.rectangle(px0, fy(band[1]), pw, fy(band[0]) - fy(band[1])); c.set_source_rgba(1, .3, .3, .10 * a); c.fill()
        text(c, band[2], px0 + pw - 8, fy(band[1]) + 22, 15 if SQ else 19, (1, .6, .6), align="right", alpha=a)
    for v, lab, vert in hlines:
        if vert: c.move_to(fx(v), py0); c.line_to(fx(v), py0 + ph)
        else: c.move_to(px0, fy(v)); c.line_to(px0 + pw, fy(v))
        c.set_source_rgba(1, .45, .45, .7 * a); c.set_dash([5, 4]); c.stroke(); c.set_dash([])
        if lab: text(c, lab, (fx(v) + 6) if vert else (px0 + 6), (py0 + 18) if vert else (fy(v) - 6), 15 if SQ else 19, (1, .65, .65), alpha=a)
    text(c, xlabel, px0 + pw / 2, y + h - 16, 15 if SQ else 19, MUT, align="center", alpha=a)
    c.save(); c.rectangle(px0, py0 - 4, pw * clip(prog), ph + 8); c.clip()
    for (tt, vv), col in curves:
        m = (tt >= xr[0]) & (tt <= xr[1]); first = True
        for xv, yv in zip(tt[m], vv[m]):
            (c.move_to if first else c.line_to)(fx(xv), fy(yv)); first = False
        c.set_source_rgba(*col, a); c.set_line_width(3); c.stroke()
    c.restore()
    la = ramp(prog, 0.6, 1.0) * a
    for k, (s, col) in enumerate(legend or []):
        lx, ly = (px0 + pw - 10, py0 + ph - 14 - (len(legend) - 1 - k) * (24 if SQ else 30)) if legend is not None else (0, 0)
        font(c, 16 if SQ else 20, True); e = c.text_extents(s)
        c.set_source_rgba(.11, .12, .15, .85 * la); c.rectangle(lx - e.x_advance - 34, ly - 17, e.x_advance + 40, 24); c.fill()
        c.set_source_rgba(*col, la); c.rectangle(lx - e.x_advance - 28, ly - 8, 18, 5); c.fill()
        text(c, s, lx, ly, 16 if SQ else 20, INK, True, align="right", alpha=la)
    if verdict:
        va = ramp(prog, 1.0, 1.15) * a
        badge(c, verdict, x + w - 20 - (c.text_extents(verdict).x_advance if False else 0), y + 38, 18 if SQ else 23, GRN, va, bg=(.05, .2, .1, .95))

def spice(c, t):
    a = ramp(t, T5 + 0.2, T5 + 0.7) * (1 - ramp(t, T_END - 0.2, T_END + 0.4))
    if a <= 0: return
    short = ["board only", "1 sensor", "3 SparkFun", "5 boards, 1 m"]
    cur = [((d[:, 0] - 4.255e-6) * 1e9, d[:, 1]) for d in I2C_D]
    leg = [(f"{short[i]}: {r['fpga_trise'] * 1e9:.0f} ns", CAT[i]) for i, r in enumerate(I2C)]
    font(c, 18 if SQ else 23, True); vw = c.text_extents("400 kHz OK up to ~75 pF").x_advance
    scope(c, SCOPES[0], "I²C rise on PORT_H0/H1 (4k7)", (-100, 1100), (-0.2, 3.7), list(zip(cur, CAT)), ramp(t, S_I2C, S_I2C + 3.0),
          [(300, "400 kHz limit", True)], None, "time after release (ns)", None, a, leg)
    if t > S_I2C + 3.1:
        x, y, w, h = SCOPES[0]; badge(c, "400 kHz OK up to ~75 pF", x + w - 24 - vw, y + 38, 18 if SQ else 23, GRN, ramp(t, S_I2C + 3.1, S_I2C + 3.3) * a, bg=(.05, .2, .1, .95))
    tk = [(d[:, 0] * 1e9 - 55, d[:, 1]) for d in TCK_D]
    leg2 = [("no series R: peak 4.3 V", CAT[0]), ("33 Ω series", CAT[1]), ("100 Ω series", CAT[2])]
    scope(c, SCOPES[1], "JTAG TCK through 25 cm TC2050 cable", (-3, 45), (-1.4, 4.7), list(zip(tk, CAT[:3])), ramp(t, S_TCK, S_TCK + 3.0),
          [], (0.8, 2.0, "undefined 0.8–2.0 V"), "time (ns), 1 ns probe edges", None, a, None)
    for k, (s, col) in enumerate(leg2):
        x, y, w, h = SCOPES[1]; la = ramp(t, S_TCK + 1.8, S_TCK + 2.4) * a
        lx, ly = x + w - 30, y + 90 + k * (26 if SQ else 32)
        font(c, 16 if SQ else 20, True); e = c.text_extents(s)
        c.set_source_rgba(*col, la); c.rectangle(lx - e.x_advance - 28, ly - 8, 18, 5); c.fill(); text(c, s, lx, ly, 16 if SQ else 20, INK, True, align="right", alpha=la)
    if t > S_TCK + 3.1:
        x, y, w, h = SCOPES[1]; s = "no double clocking"; font(c, 18 if SQ else 23, True); e = c.text_extents(s)
        badge(c, s, x + w - 24 - e.x_advance, y + 38, 18 if SQ else 23, GRN, ramp(t, S_TCK + 3.1, S_TCK + 3.3) * a, bg=(.05, .2, .1, .95))

# ------------------------------------------------------------------ cards
def card(c, t, t0, title, sub, cy):
    a = ramp(t, t0, t0 + 0.25) * (1 - ramp(t, T5 - 0.3, T5 + 0.1)); s = 0.85 + 0.15 * ease(ramp(t, t0, t0 + 0.25))
    if a <= 0: return
    vx, vy, vw, vh = VIEW; cw, ch = (620 if SQ else 900), (120 if SQ else 150)
    c.save(); c.translate(vx + vw / 2, cy); c.scale(s, s)
    c.set_source_rgba(.07, .45, .22, .96 * a); rrect(c, -cw / 2, -ch / 2, cw, ch, 16); c.fill()
    text(c, title, 0, -6, 34 if SQ else 44, INK, True, align="center", alpha=a); text(c, sub, 0, 34 if SQ else 44, 19 if SQ else 25, (.85, 1, .9), align="center", alpha=a)
    c.restore()

def intro(c, t):
    a = 1 - ramp(t, T_GO + 0.2, T1)
    if a <= 0: return
    c.set_source_rgba(*BG, .82 * a); c.paint()
    n = int(max(0, t - T_HEAD) * 28); hs = HEAD[:n]
    hy = (250 if SQ else 640)
    fs = 38 if SQ else 46
    font(c, fs, True)
    words = hs.split(" "); lines = [""]
    for wd in words:
        trial = (lines[-1] + " " + wd).strip()
        if c.text_extents(trial).x_advance > W - 120: lines.append(wd)
        else: lines[-1] = trial
    for k, l in enumerate(lines): text(c, l, 60, hy + k * (fs + 12), fs, YEL, True, alpha=a)
    cx, cy, cw = 50, hy + 2 * (fs + 12) + 30, W - 100; lh = 44 if SQ else 56; ch = 70 + lh * len(TYPE_LINES)
    if t > LINE_T[0] - 0.4:
        ca = ramp(t, LINE_T[0] - 0.4, LINE_T[0]) * a
        c.set_source_rgba(.11, .12, .15, .97 * ca); rrect(c, cx, cy, cw, ch, 16); c.fill()
        for k, col in enumerate(((1, .37, .34), (1, .74, .2), (.2, .8, .3))):
            c.new_sub_path(); c.arc(cx + 30 + k * 26, cy + 26, 8, 0, 2 * math.pi); c.set_source_rgba(*col, ca); c.fill()
        text(c, "task.txt", cx + cw / 2, cy + 33, 20 if SQ else 24, MUT, mono=True, align="center", alpha=ca)
        fs2 = 25 if SQ else 31
        for k, (lab, body) in enumerate(TYPE_LINES):
            if t < LINE_T[k]: break
            n = int((t - LINE_T[k]) * CPS); full = lab + body; s = full[:n]
            yy = cy + 80 + k * lh
            w1 = text(c, "> ", cx + 26, yy, fs2, GRN, True, True, alpha=a)
            sl = s[:len(lab)]; sb = s[len(lab):]
            w2 = text(c, sl, cx + 26 + w1, yy, fs2, (.55, .75, 1), True, True, alpha=a)
            w3 = text(c, sb, cx + 26 + w1 + w2, yy, fs2, INK, False, True, alpha=a)
            last = k == len(TYPE_LINES) - 1 or t < LINE_T[k + 1]
            if last and (int(t * 2.5) % 2 == 0 or n < len(full)):
                c.set_source_rgba(*GRN, a); c.rectangle(cx + 26 + w1 + w2 + w3 + 3, yy - fs2 + 4, fs2 * 0.55, fs2); c.fill()
    if t > T_GO - 0.1:
        u = ramp(t, T_GO, T_GO + 0.5); s = 1 + 0.4 * u
        c.save(); c.translate(W / 2, (cy + ch + 110) if True else 0); c.scale(s, s)
        text(c, "GO ▶", 0, 0, 64 if SQ else 80, GRN, True, align="center", alpha=a * (1 - 0.6 * u)); c.restore()

def endcard(c, t):
    a = ramp(t, T_END, T_END + 0.5)
    if a <= 0: return
    lines = [("✓ Qwiic I²C port (shares PORT_H0/H1)", GRN), ("✓ JTAG → TC2050 pads, ARM 10-pin", GRN), ("✓ 0 new DRC errors, 0 unconnected", GRN),
             ("✓ schematic = PCB (parity check)", GRN), ("✓ SPICE: I²C + TCK fine", GRN), ("concept change, not built yet", MUT)]
    if SQ:
        x, y = SIDE[0] - 10, SIDE[1] + 10
        c.set_source_rgba(*BG, .92 * a); c.rectangle(SIDE[0] - 20, SIDE[1] - 10, SIDE[2] + 40, SIDE[3] + 20); c.fill()
        for k, (s, col) in enumerate(lines):
            # wrap to the column
            font(c, 21, True); words = s.split(" "); ls = [""]
            for wd in words:
                tr = (ls[-1] + " " + wd).strip()
                if c.text_extents(tr).x_advance > SIDE[2] + 10: ls.append("   " + wd)
                else: ls[-1] = tr
            for l in ls:
                if ramp(t, T_END + 0.3 + k * 0.35, T_END + 0.5 + k * 0.35) > 0: text(c, l, x, y + 30, 21, col, k < 5, alpha=a * ramp(t, T_END + 0.3 + k * 0.35, T_END + 0.5 + k * 0.35))
                y += 30
            y += 22
    else:
        x, y = SIDE[0], SIDE[1] - 10
        c.set_source_rgba(*BG, .95 * a); c.rectangle(0, SIDE[1] - 40, W, SIDE[3] + 60); c.fill()
        for k, (s, col) in enumerate(lines):
            aa = a * ramp(t, T_END + 0.3 + k * 0.35, T_END + 0.5 + k * 0.35)
            text(c, s, x + (k % 2) * 520 if False else x, y + 34 + k * 40, 27, col, k < 5, alpha=aa)


# ------------------------------------------------------------------ exploded layer view
Z = json.load(open(D + "zones.json"))
EX0, EX1, EY0, EY1 = 95.6, 113.8, 80.9, 109.1
RES = 24.0; LW_, LH_ = int((EX1 - EX0) * RES), int((EY1 - EY0) * RES)
CU = (.80, .53, .24)
NEW_F = sum(1 for s_ in G["route"] if s_[4] == "F.Cu") + 6; NEW_B = sum(1 for s_ in G["route"] if s_[4] == "B.Cu")
def _layer(kind):
    sf = cairo.ImageSurface(cairo.FORMAT_ARGB32, LW_, LH_); c = cairo.Context(sf)
    c.scale(RES, RES); c.translate(-EX0, -EY0)
    o = G["outline"]; c.move_to(*o[0]); [c.line_to(*p) for p in o[1:]]; c.close_path()
    c.set_source_rgba(.07, .30, .17, .80); c.fill_preserve(); c.set_source_rgba(.85, .8, .4, .9); c.set_line_width(0.12); c.stroke()
    c.set_line_cap(cairo.LINE_CAP_ROUND)
    if kind in ("In1", "In2"):
        c.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        for z in Z.get(kind, []):
            for ring in z["rings"]:
                c.move_to(*ring[0]); [c.line_to(*p) for p in ring[1:]]; c.close_path()
        c.set_source_rgba(*CU, .78); c.fill()
    else:
        L = "F.Cu" if kind == "F" else "B.Cu"
        for z in Z.get(kind, []):
            c.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
            for ring in z["rings"]: c.move_to(*ring[0]); [c.line_to(*p) for p in ring[1:]]; c.close_path()
            c.set_source_rgba(*CU, .8); c.fill()
        for tr in G["base_tracks"]:
            if tr[5] == L: c.move_to(tr[0], tr[1]); c.line_to(tr[2], tr[3])
        c.set_line_width(0.13); c.set_source_rgba(*CU, .85); c.stroke()
        for r in list(G["pads_after"]) + ["_base"]:
            pl = G["base_pads"] if r == "_base" else G["pads_after"][r]
            new = r in ("J6", "R31", "R32", "J2")
            pads(c, pl, L, (1, .92, .3) if new else (.86, .62, .32), 1.0)
        for s_ in G["route"] + [n_[:4] + [n_[5], n_[6]] for n_ in G["nudge"]]:
            if s_[4] == L: c.move_to(s_[0], s_[1]); c.line_to(s_[2], s_[3])
        c.set_line_width(0.34); c.set_source_rgba(*(NF if kind == "F" else NB)); c.stroke()
    for v in G["base_vias"]:
        c.new_sub_path(); c.arc(v[0], v[1], v[2] / 2, 0, 2 * math.pi)
    c.set_source_rgba(.6, .6, .6, .9); c.fill()
    for v in G["new_vias"]:
        c.new_sub_path(); c.arc(v[0], v[1], v[2] / 2 + 0.05, 0, 2 * math.pi)
    c.set_source_rgba(1, 1, 1, 1); c.fill()
    return sf
LAYERS = [("B", _layer("B")), ("In2", _layer("In2")), ("In1", _layer("In1")), ("F", _layer("F"))]
LAB = {"F": ("TOP copper", f"+{NEW_F} new tracks (orange)", NF), "In1": ("inner 1: GND plane", "untouched", SUB),
       "In2": ("inner 2: 3.3 V plane", "untouched", SUB), "B": ("BOTTOM copper", f"+{NEW_B} new tracks (cyan)", NB)}
def _basis(k):
    vx, vy, vw, vh = VIEW; s0 = min(vw / (X1 - X0), vh / (Y1 - Y0))
    s1 = 19.0 if SQ else 25.0
    a = math.radians(28 * k); tt = 1 - 0.58 * k; s_ = s0 + (s1 - s0) * k
    return (s_ * math.cos(a), s_ * math.sin(a) * tt), (-s_ * math.sin(a), s_ * math.cos(a) * tt)
def exploded(c, t):
    a = ramp(t, TX, TX + 0.25) * (1 - ramp(t, TA - 0.4, TA + 0.1))
    if a <= 0: return
    k = ease(ramp(t, TX + 0.1, TX + 1.3))
    sep = (112 if SQ else 235) * k
    ex, ey = _basis(k)
    vx, vy, vw, vh = VIEW
    cx0, cy0 = vx + vw / 2, vy + vh / 2
    cx1, cy1 = (335, 488) if SQ else (375, 830)
    cx, cy = cx0 + (cx1 - cx0) * k, cy0 + (cy1 - cy0) * k
    mx, my = (EX1 - EX0) / 2, (EY1 - EY0) / 2
    O = (cx - mx * ex[0] - my * ey[0], cy - mx * ex[1] - my * ey[1])
    def P(x, y, z): return (O[0] + (x - EX0) * ex[0] + (y - EY0) * ey[0], O[1] + (x - EX0) * ex[1] + (y - EY0) * ey[1] - z)
    zs = [(i - 1.5) * sep for i in range(4)]
    for i, (name, sf) in enumerate(LAYERS):
        c.save(); ox, oy = P(EX0, EY0, zs[i])
        c.transform(cairo.Matrix(ex[0] / RES, ex[1] / RES, ey[0] / RES, ey[1] / RES, ox, oy))
        c.set_source_surface(sf, 0, 0); c.get_source().set_filter(cairo.FILTER_GOOD)
        lay_a = a if name in ("F", "B") or k > 0.05 else a * k
        c.paint_with_alpha(lay_a); c.restore()
        if i < 3 and k > 0.3:                                       # new vias: white pins through the stack
            for v in G["new_vias"]:
                p0 = P(v[0], v[1], zs[i]); p1 = P(v[0], v[1], zs[i + 1])
                c.move_to(*p0); c.line_to(*p1)
            c.set_source_rgba(1, 1, 1, .75 * a * ramp(k, 0.3, 0.8)); c.set_line_width(1.6 if SQ else 2.2); c.stroke()
    la = a * ramp(t, TX + 1.3, TX + 1.7) * (1 - ramp(t, TA - 0.8, TA - 0.4))
    if la > 0:
        lx = 712 if SQ else 752
        fs1, fs2 = (21, 16) if SQ else (27, 21)
        for i, (name, sf) in enumerate(LAYERS):
            x, y = P(EX1, (EY0 + EY1) / 2, zs[i])
            ly = y
            c.move_to(x + 6, y); c.line_to(lx - 12, ly); c.set_source_rgba(1, 1, 1, .5 * la); c.set_line_width(1.2); c.stroke()
            c.new_sub_path(); c.arc(x + 4, y, 4, 0, 2 * math.pi); c.set_source_rgba(*YEL, la); c.fill()
            t1, t2, col = LAB[name]
            text(c, t1, lx, ly - 4, fs1, col if name in ("F", "B") else INK, True, alpha=la)
            text(c, t2, lx, ly + fs2 + 2, fs2, SUB, alpha=la)
        cap_y = (vy + vh + 6) if SQ else (vy + vh + 40)
        text(c, "white pins = 26 new vias drilled through all 4 layers", W / 2, cap_y, 18 if SQ else 24, INK, True, align="center", alpha=la)


# ------------------------------------------------------------------ 3D renders: before -> after
R3 = {k: cairo.ImageSurface.create_from_png(D + f"{k}.png") for k in ("before_top", "after_top", "before_bot", "after_bot")}
RA = (20, 140, 1040, 712) if SQ else (20, 290, 1040, 1040)
def _crop(cx, cy, w):
    h = w * RA[3] / RA[2]; return cx - w / 2, cy - h / 2, w
FULLC = {"top": _crop(905, 755, 1560), "bot": _crop(885, 750, 1560)}
ZOOMC = {"top": _crop(470, 520, 820 if SQ else 700), "bot": _crop(1440, 790, 820 if SQ else 700)}
CALL = {"top": [("NEW: Qwiic I²C connector", 468, 392, (1, .92, .3), -1), ("JTAG header gone (moved to bottom)", 318, 545, PINK, 1)],
        "bot": [("NEW: TC2050 JTAG test pads", 1453, 866, (1, .92, .3), -1), ("NEW: I²C pull-ups", 1491, 684, (1, .92, .3), -1)]}
def assembled(c, t):
    a = ramp(t, TA - 0.1, TA + 0.4) * (1 - ramp(t, T4 - 0.4, T4))
    if a <= 0: return
    side_ = "top" if t < TA + 4.0 else "bot"
    t0 = TA if side_ == "top" else TA + 3.6
    wipe = ease(ramp(t, t0 + 1.0, t0 + 1.8))
    z = ease(ramp(t, t0 + 1.9, t0 + 3.2))
    fc, zc = FULLC[side_], ZOOMC[side_]
    cr = tuple(fc[i] + (zc[i] - fc[i]) * z for i in range(3))
    x0, y0, w0 = cr; s = RA[2] / w0
    sa = a * (ramp(t, TA + 3.6, TA + 4.1) if side_ == "bot" else (1 - ramp(t, TA + 3.6, TA + 4.0)))
    c.save(); c.rectangle(*RA); c.clip()
    for which, cl in (("before", None), ("after", wipe)):
        if cl is not None and cl <= 0: continue
        c.save()
        if cl is not None and cl < 1: c.rectangle(RA[0], RA[1], RA[2] * cl, RA[3]); c.clip()
        c.translate(RA[0], RA[1]); c.scale(s, s); c.translate(-x0, -y0)
        c.set_source_surface(R3[f"{which}_{side_}"], 0, 0); c.get_source().set_filter(cairo.FILTER_GOOD); c.paint_with_alpha(sa)
        c.restore()
    if 0 < wipe < 1:
        wx = RA[0] + RA[2] * wipe; c.move_to(wx, RA[1]); c.line_to(wx, RA[1] + RA[3]); c.set_source_rgba(1, 1, 1, .9 * sa); c.set_line_width(3); c.stroke()
    c.restore()
    fs = 22 if SQ else 28
    lab = "BEFORE" if wipe < 0.5 else "AFTER"
    badge(c, f"{lab} · {'top side' if side_ == 'top' else 'bottom side'}", RA[0] + 16, RA[1] + 40, fs, PINK if lab == "BEFORE" else GRN, sa)
    ca = sa * ramp(t, t0 + 2.4, t0 + 2.7)
    if ca > 0:
        for k, (txt_, rx, ry, col, dirn) in enumerate(CALL[side_]):
            px, py = RA[0] + (rx - x0) * s, RA[1] + (ry - y0) * s
            c.new_sub_path(); c.arc(px, py, 7, 0, 2 * math.pi); c.set_source_rgba(*col, ca); c.fill()
            c.new_sub_path(); c.arc(px, py, 16 + 4 * math.sin(t * 6), 0, 2 * math.pi); c.set_source_rgba(*col, .7 * ca); c.set_line_width(2.5); c.stroke()
            font(c, fs, True); e = c.text_extents(txt_)
            lx = min(max(px + (60 if dirn < 0 else -40), RA[0] + 12), RA[0] + RA[2] - e.x_advance - 24)
            ly = py - 60 if dirn < 0 else py + 80
            ly = min(max(ly, RA[1] + 80), RA[1] + RA[3] - 20)
            ex_ = min(max(px, lx), lx + e.x_advance); ey_ = (ly - fs - 6) if ly > py else (ly + 10)
            c.move_to(px, py); c.line_to(ex_, ey_); c.set_source_rgba(*col, .8 * ca); c.set_line_width(2); c.stroke()
            badge(c, txt_, lx, ly, fs, col, ca)

def frame(t):
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H); c = cairo.Context(surf)
    c.set_source_rgb(*BG); c.paint()
    dimb = 0.25 + 0.75 * ramp(t, T_GO, T1)
    dimb *= 1 - 0.85 * ramp(t, T5, T5 + 0.5) * (1 - ramp(t, T_END - 0.2, T_END + 0.4))
    xa = ramp(t, TX, TX + 0.25) * (1 - ramp(t, T4 - 0.35, T4))            # exploded view replaces the flat board
    dimb *= 1 - xa
    draw_board(c, t, dimb)
    board_labels(c, t)
    sa = ramp(t, T1, T1 + 0.4) * (1 - ramp(t, T5, T5 + 0.3) * (1 - ramp(t, T_END - 0.2, T_END + 0.3)))
    side(c, t, (sa if t < T_END else sa * (1 - ramp(t, T_END, T_END + 0.4))) * (1 - xa))
    exploded(c, t)
    assembled(c, t)
    card(c, t, T_DRC, "DRC: 0 new errors", "0 unconnected · baseline errors in the original untouched", VIEW[1] + VIEW[3] * 0.38)
    card(c, t, T_PAR, "Schematic = PCB", "parity check: 0 new mismatches", VIEW[1] + VIEW[3] * 0.62)
    spice(c, t)
    endcard(c, t)
    intro(c, t)
    # header + timer
    ha = ramp(t, T_GO - 0.2, T1)
    text(c, "PCB SPEEDRUN", W / 2, TITLE_Y, 50 if SQ else 64, YEL, True, align="center", alpha=max(ha, 0.0))
    part = [p for p in PARTS if t >= p[0]][-1][1]
    text(c, part, W / 2, SUB_Y, 26 if SQ else 34, INK, True, align="center", alpha=ha)
    if not SQ: text(c, "AI changes a finished 4-layer FPGA board", W / 2, SUB_Y + 50, 26, SUB, align="center", alpha=ha)
    if t > T_GO:
        el = min(t, T_END) - T_GO
        text(c, f"{int(el // 60)}:{el % 60:05.2f}", W / 2, TIMER_Y, 66 if SQ else 90, GRN, True, True, "center", ha)
        st = [s for s in STEPS if t >= s[0]]
        if st: text(c, st[-1][1], W / 2, STEP_Y, 24 if SQ else 32, INK, True, align="center", alpha=ha)
        text(c, "ECP5 Mini (open source) · KiCad 9 · Claude Opus 5.5", W / 2, CAP_Y, 17 if SQ else 23, MUT, align="center", alpha=ha * 0.9)
    return surf

if __name__ == "__main__":
    if "--test" in sys.argv:
        ts = [float(x) for x in sys.argv[sys.argv.index("--test") + 1].split(",")]
        for tt in ts: frame(tt).write_to_png(f"{OUT}test_{tt:.1f}.png")
        print("T_GO", round(T_GO, 2), "T1", round(T1, 2), "T2", round(T2, 2), "T3", round(T3, 2), "T4", round(T4, 2), "T5", round(T5, 2), "END", round(T_END, 2), "TOTAL", round(T_TOTAL, 2)); sys.exit()
    json.dump(dict(total=T_TOTAL, events=sorted(EV), marks=dict(go=T_GO, t1=T1, t2=T2, fail=T_FAIL, fix=T_FIX, t3=T3, r1=R1, t4=T4, t5=T5, end=T_END, s_i2c=S_I2C, s_tck=S_TCK)), open(OUT + "events.json", "w"))
    n = int(T_TOTAL * FPS); tmp = OUT + "video_tmp.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for k in range(n):
        p.stdin.write(bytes(frame(k / FPS).get_data()))
        if k % 150 == 0: print(k, "/", n, flush=True)
    p.stdin.close(); rc = p.wait()
    if rc == 0: os.replace(tmp, OUT + "video.mp4")
    print("done", rc)
