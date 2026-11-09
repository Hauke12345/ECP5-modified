import json, cairo, math
B = json.load(open("d_before.json")); A = json.load(open("d_after.json"))
key = lambda t: (t[0], t[1], t[2], t[3], t[5], t[6])
kb = {key(t) for t in B["tracks"]}; ka = {key(t) for t in A["tracks"]}
vb = {(v[0], v[1], v[4]) for v in B["vias"]}; va = {(v[0], v[1], v[4]) for v in A["vias"]}
X0, X1, Y0, Y1 = 95.6, 115.0, 80.9, 109.0
S = 32.0; PW, PH = int((X1 - X0) * S), int((Y1 - Y0) * S)
M, HDR, TOP = 40, 70, 150
W, H = M * 3 + PW * 2, TOP + (HDR + PH) * 2 + M + 60
surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H); c = cairo.Context(surf)
c.set_source_rgb(.07, .08, .1); c.paint()
def txt(s, x, y, size, col=(1, 1, 1), bold=False):
    c.select_font_face("DejaVu Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    c.set_font_size(size); c.set_source_rgb(*col); c.move_to(x, y); c.show_text(s)
NEWF, NEWB = (1.0, .55, .15), (.25, .85, 1.0)
def panel(D, ox, oy, side, mode):
    L = "F.Cu" if side == "F" else "B.Cu"
    c.save(); c.rectangle(ox, oy, PW, PH); c.clip(); c.translate(ox, oy); c.scale(S, S); c.translate(-X0, -Y0)
    c.move_to(*D["outline"][0]); [c.line_to(*p) for p in D["outline"][1:]]; c.close_path()
    c.set_source_rgb(.10, .17, .13); c.fill_preserve(); c.set_source_rgb(.8, .75, .35); c.set_line_width(0.08); c.stroke()
    c.set_line_cap(cairo.LINE_CAP_ROUND)
    hl = []
    for t in D["tracks"]:
        if t[5] != L and t[5] in ("F.Cu", "B.Cu"):
            continue
        if t[5] not in ("F.Cu", "B.Cu"): continue
        changed = (mode == "before" and key(t) not in ka) or (mode == "after" and key(t) not in kb)
        if changed: hl.append(t); continue
        c.move_to(t[0], t[1]); c.line_to(t[2], t[3]); c.set_line_width(t[4])
        c.set_source_rgb(*((.45, .25, .22) if side == "F" else (.2, .3, .45))); c.stroke()
    newrefs = {"J6", "R31", "R32", "J2"} if mode == "after" else set()
    gone = {"J2", "D9", "D10", "D11"} if mode == "before" else set()
    for ln, pts, ref, net, hole in D["pads"]:
        if ln != L: continue
        c.move_to(*pts[0]); [c.line_to(*p) for p in pts[1:]]; c.close_path()
        if ref in newrefs: col = (1, .92, .3)
        elif ref in gone: col = (1, .3, .55)
        else: col = (.62, .58, .45)
        c.set_source_rgb(*col); c.fill()
    for t in hl:
        c.move_to(t[0], t[1]); c.line_to(t[2], t[3]); c.set_line_width(max(t[4], 0.13))
        c.set_source_rgb(*((1, .3, .55) if mode == "before" else (NEWF if side == "F" else NEWB))); c.stroke()
    for x, y, d, dr, net in D["vias"]:
        new = (mode == "after" and (x, y, net) not in vb) or (mode == "before" and (x, y, net) not in va)
        c.new_sub_path(); c.arc(x, y, d / 2, 0, 2 * math.pi)
        c.set_source_rgb(*((1, 1, 1) if new and mode == "after" else ((1, .3, .55) if new else (.55, .55, .55)))); c.fill()
        c.new_sub_path(); c.arc(x, y, dr / 2, 0, 2 * math.pi); c.set_source_rgb(.1, .1, .1); c.fill()
    c.restore()
def label(s, x, y, ox, oy, col=(1, 1, 1), size=17):
    px, py = ox + (x - X0) * S, oy + (y - Y0) * S
    c.select_font_face("DejaVu Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); c.set_font_size(size)
    e = c.text_extents(s); c.set_source_rgba(0, 0, 0, .7); c.rectangle(px - 4, py - e.height - 6, e.width + 8, e.height + 10); c.fill()
    c.set_source_rgb(*col); c.move_to(px, py); c.show_text(s)
txt("ECP5 Mini, Rev 1.1 board change (AI-made)", M, 52, 34, bold=True)
txt("JTAG header → Tag-Connect TC2050 pads (ARM-10) · new Qwiic I²C port · 3 RGB LEDs dropped  ·  DRC: 0 new errors, 0 unconnected", M, 92, 19, (.75, .8, .9))
txt("highlighted = copper that changed; everything else on the board is untouched", M, 122, 17, (.6, .65, .75))
for row, (D, mode, title) in enumerate(((B, "before", "BEFORE (original)"), (A, "after", "AFTER (Rev 1.1)"))):
    oy = TOP + row * (HDR + PH)
    for col, side in enumerate(("F", "B")):
        ox = M + col * (PW + M)
        txt(f"{title}: {'top (F.Cu)' if side == 'F' else 'bottom (B.Cu), seen from top'}", ox, oy + 45, 21, bold=True)
        panel(D, ox, oy + HDR, side, mode)
        Y = oy + HDR
        if mode == "before" and side == "F":
            label("D9–D11 (removed)", 104.0, 86.0, ox, Y, (1, .45, .65)); label("J2 JTAG header (removed)", 96.2, 87.4, ox, Y, (1, .45, .65))
        if mode == "before" and side == "B": label("old JTAG runs (removed)", 98.6, 101.2, ox, Y, (1, .45, .65))
        if mode == "after" and side == "F":
            label("J6 Qwiic", 98.0, 85.6, ox, Y, (1, .92, .3)); label("D4–D8", 103.0, 95.6, ox, Y, (1, .92, .3))
        if mode == "after" and side == "B":
            label("R31/R32 4k7", 99.6, 86.3, ox, Y, (1, .92, .3)); label("J2 TC2050 pads", 99.6, 103.0, ox, Y, (1, .92, .3))
txt("orange / cyan = new tracks (top / bottom) · white = new vias · yellow = new parts · pink = removed", M, H - 25, 18, (.7, .75, .85))
surf.write_to_png("eco_before_after.png"); print(W, H)
