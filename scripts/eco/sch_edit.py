"""Apply the Rev-1.1 ECO to the schematic: J2 -> TC2050 (ARM-10), Qwiic J6 + pull-ups on root (shares PORT_H0/H1), D9-D11 not on board."""
import re, uuid, shutil, os
D = "/home/claude/route/sch/"; O = "/home/claude/route/sch_eco/"
os.makedirs(O, exist_ok=True)
for f in os.listdir(D):
    if f.endswith((".kicad_sch", ".kicad_pro", "-lib-table", ".lib")): shutil.copy(D + f, O + f)
def end(s, i):
    d = 0
    for k in range(i, len(s)):
        if s[k] == '(': d += 1
        elif s[k] == ')':
            d -= 1
            if d == 0: return k + 1
def libsym(lib, name):
    s = open(f"/usr/share/kicad/symbols/{lib}.kicad_sym").read(); i = s.find(f'(symbol "{name}"')
    b = s[i:end(s, i)]
    return b.replace(f'(symbol "{name}"', f'(symbol "{lib}:{name}"', 1)
def add_lib(s, blk):
    i = s.find("(lib_symbols") + len("(lib_symbols"); return s[:i] + "\n    " + blk + s[i:]
U = lambda: str(uuid.uuid4())
def prop(n, k, v, x, y, a=0, hide=False, just=None):
    e = "(effects (font (size 1.27 1.27))" + (f" (justify {just})" if just else "") + (" hide" if hide else "") + ")"
    return f'    (property "{k}" "{v}" (id {n}) (at {x} {y} {a})\n      {e}\n    )\n'
def sym(lib_id, x, y, a, ref, val, fp, u, refxy, valxy, mirror="", extra=(), fa=0, vjust=None, rjust=None):
    s = f'  (symbol (lib_id "{lib_id}") (at {x} {y} {a}){mirror} (unit 1)\n    (in_bom yes) (on_board yes)\n    (uuid "{u}")\n'
    pw = ref.startswith("#")
    s += prop(0, "Reference", ref, *refxy, a=fa, hide=pw, just=rjust) + prop(1, "Value", val, *valxy, a=fa, just=vjust) + prop(2, "Footprint", fp, x, y, hide=True) + prop(3, "Datasheet", "~" if not pw else "", x, y, hide=True)
    for n, (k, v) in enumerate(extra, 4): s += prop(n, k, v, x, y, hide=True)
    return s + "  )\n"
def wire(x1, y1, x2, y2): return f"  (wire (pts (xy {x1} {y1}) (xy {x2} {y2}))\n    (stroke (width 0) (type solid) (color 0 0 0 0))\n  )\n"
def label(t, x, y, a): return f'  (label "{t}" (at {x} {y} {a})\n    (effects (font (size 1.27 1.27)) (justify {"right" if a == 180 else "left"} bottom))\n  )\n'
def nc(x, y): return f"  (no_connect (at {x} {y}) (uuid {U()}))\n"
def text(t, x, y, size=1.27): return f'  (text "{t}" (at {x} {y} 0)\n    (effects (font (size {size} {size})) (justify left bottom))\n  )\n'
def insert_body(s, blk):              # before (sheet_instances / symbol_instances or final paren
    for key in ("  (sheet_instances", "  (symbol_instances"):
        i = s.find(key)
        if i >= 0: return s[:i] + blk + "\n" + s[i:]
    i = s.rstrip().rfind(")"); return s[:i] + blk + s[i:]
inst = []                              # (path, ref, value, footprint)
CFG = "/dc977d07-e2f1-4e46-a04d-d09b8b7fb491/"
# ---------- FPGA Config sheet: replace J2
p = O + "fpga-config.kicad_sch"; s = open(p).read()
i = s.find('  (symbol (lib_id "Connector:Conn_01x06_Male") (at 44.45 106.68 0)'); s = s[:i] + s[end(s, i) + 1:]
old_j2_uuid = "9dfb4246-b4cb-4377-881b-69939aa2d4a9"
def drop_wire(s, x1, y1, x2, y2):
    pat = f"(wire (pts (xy {x1} {y1}) (xy {x2} {y2}))"; i = s.find(pat); assert i >= 0, pat
    i = s.rfind("\n", 0, i) + 1; return s[:i] + s[end(s, s.find("(wire", i)) + 1:]
for w in [(24.13, 97.79, 24.13, 101.6), (24.13, 101.6, 39.37, 101.6), (24.13, 104.14, 24.13, 105.41), (24.13, 104.14, 39.37, 104.14),
          (27.94, 106.68, 39.37, 106.68), (27.94, 109.22, 39.37, 109.22), (27.94, 111.76, 39.37, 111.76), (27.94, 114.3, 39.37, 114.3)]:
    s = drop_wire(s, *w)
for t, y in (("TCK", 106.68), ("TDO", 109.22), ("TDI", 111.76), ("TMS", 114.3)):
    i = s.find(f'  (label "{t}" (at 27.94 {y} 0)'); assert i >= 0; s = s[:i] + s[end(s, i) + 1:]
removed_pwr = []
for lid, x, y in (("power:+3V3", 24.13, 97.79), ("power:GND", 24.13, 105.41)):
    i = s.find(f'  (symbol (lib_id "{lid}") (at {x} {y}'); assert i >= 0
    removed_pwr.append(re.search(r'\(uuid "?([0-9a-f-]+)', s[i:i + 300]).group(1)); s = s[:i] + s[end(s, i) + 1:]
s = add_lib(s, libsym("Connector_Generic", "Conn_02x05_Odd_Even"))
JX, JY = 33.02, 106.68; L, R = 27.94, 40.64
uj = U(); blk = sym("Connector_Generic:Conn_02x05_Odd_Even", JX, JY, 0, "J2", "JTAG TC2050 (ARM-10)", "Connector:Tag-Connect_TC2050-IDC-NL_2x05_P1.27mm_Vertical", uj, (34.29, 99.06), (34.29, 116.84))
blk = blk.replace("(in_bom yes) (on_board yes)\n    (uuid \"" + uj, "(in_bom no) (on_board yes)\n    (uuid \"" + uj)
inst.append((CFG + uj, "J2", "JTAG TC2050 (ARM-10)", "Connector:Tag-Connect_TC2050-IDC-NL_2x05_P1.27mm_Vertical"))
up = U(); blk += sym("power:+3V3", 22.86, 101.6, 90, "#PWR0201", "+3V3", "", up, (19.05, 101.6), (16.51, 101.6), fa=90, vjust="right"); inst.append(("/".join(["", CFG.strip("/"), up]), "#PWR0201", "+3V3", ""))
blk += wire(L, 101.6, 22.86, 101.6)
for k, y in enumerate((104.14, 106.68, 111.76)):
    ug = U(); r_ = f"#PWR020{2 + k}"
    blk += sym("power:GND", 22.86, y, 270, r_, "GND", "", ug, (16.51, y), (18.415, y), fa=90, vjust="right"); inst.append(("/".join(["", CFG.strip("/"), ug]), r_, "GND", ""))
    blk += wire(L, y, 22.86, y)
blk += nc(L, 109.22) + nc(R, 111.76)
for t, y in (("TMS", 101.6), ("TCK", 104.14), ("TDO", 106.68), ("TDI", 109.22)): blk += label(t, R, y, 0)
blk += text("Tag-Connect TC2050 pads (bottom), ARM 10-pin pinout. 7 = key, 10 = nRESET (n.c.)", 15.24, 121.92)
s = insert_body(s, blk); open(p, "w").write(s)
# ---------- LEDs sheet: D9-D11 not on board
p = O + "leds.kicad_sch"; s = open(p).read(); r = open(O + "ecp5-mini.kicad_sch").read()
dnp = []
for ref in ("D9", "D10", "D11"):
    m = re.search(r'\(path "/[0-9a-f-]+/([0-9a-f-]+)"\s+\(reference "' + ref + '"', r); u = m.group(1); dnp.append(u)
    i = s.find(f'(uuid "{u}")') if f'(uuid "{u}")' in s else s.find(f"(uuid {u})")
    j = s.rfind("(in_bom yes) (on_board yes)", 0, i); s = s[:j] + "(in_bom no) (on_board no) (dnp yes)" + s[j + len("(in_bom yes) (on_board yes)"):]
s = insert_body(s, text("Rev 1.1: D9-D11 removed (not on board) to make room for the Qwiic port and TC2050 JTAG pads.\\nLED_5..LED_7 remain routed to RN3 for reuse.", 101.6, 60.96))
open(p, "w").write(s)
# ---------- root: Qwiic J6 + pull-ups
p = O + "ecp5-mini.kicad_sch"; s = open(p).read()
s = add_lib(s, libsym("Connector_Generic_MountingPin", "Conn_01x04_MountingPin"))
blk = text("Qwiic / STEMMA QT (I2C, 3.3 V)", 251.46, 63.5, 1.778) + text("shares PORT_H1 (SDA) and PORT_H0 (SCL) with J4", 251.46, 67.31)
JX, JY = 297.18, 78.74; px = JX - 5.08
uj = U(); blk += sym("Connector_Generic_MountingPin:Conn_01x04_MountingPin", JX, JY, 0, "J6", "Qwiic I2C", "Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal", uj, (297.18, 73.66), (300.99, 78.74), vjust="left")
inst.append(("/" + uj, "J6", "Qwiic I2C", "Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal"))
ys = {1: JY - 2.54, 2: JY, 3: JY + 2.54, 4: JY + 5.08}
pw = []
def pwr(lid, x, y, a, val):
    u = U(); n = 210 + len(pw); pw.append(u); inst.append(("/" + u, f"#PWR0{n}", val, ""))
    if a: return sym(lid, x, y, a, f"#PWR0{n}", val, "", u, (x - 3.81, y), (x - 6.35 if lid.endswith("3V3") else x - 4.445, y), fa=90, vjust="right")
    return sym(lid, x, y, a, f"#PWR0{n}", val, "", u, (x, y), (x, y + (3.81 if lid.endswith("GND") else -3.81)))
blk += wire(px, ys[1], 287.02, ys[1]) + pwr("power:GND", 287.02, ys[1], 270, "GND")
blk += wire(px, ys[2], 287.02, ys[2]) + pwr("power:+3V3", 287.02, ys[2], 90, "+3V3")
blk += label("PORT_H1", px, ys[3], 180) + label("PORT_H0", px, ys[4], 180)
blk += pwr("power:GND", JX, JY + 10.16, 0, "GND")
for ref, x, net in (("R31", 254.0, "PORT_H0"), ("R32", 271.78, "PORT_H1")):
    u = U(); y = 78.74
    blk += sym("Device:R", x, y, 180, ref, "4k7", "Resistor_SMD:R_0402_1005Metric", u, (x + 2.54, y - 1.27), (x + 2.54, y + 1.27), rjust="right", vjust="right")
    blk = blk.replace(f'(property "Reference" "{ref}" (id 0) (at {x + 2.54} {y - 1.27} 0)\n      (effects (font (size 1.27 1.27)))', f'(property "Reference" "{ref}" (id 0) (at {x + 2.54} {y - 1.27} 0)\n      (effects (font (size 1.27 1.27)) (justify left))')
    blk = blk.replace(f'(property "Value" "4k7" (id 1) (at {x + 2.54} {y + 1.27} 0)\n      (effects (font (size 1.27 1.27)))', f'(property "Value" "4k7" (id 1) (at {x + 2.54} {y + 1.27} 0)\n      (effects (font (size 1.27 1.27)) (justify left))')
    inst.append(("/" + u, ref, "4k7", "Resistor_SMD:R_0402_1005Metric"))
    blk += pwr("power:+3V3", x, y - 3.81, 0, "+3V3") + wire(x, y + 3.81, x, y + 7.62) + label(net, x, y + 7.62, 0)
s = insert_body(s, blk)
# instances: drop old J2 + removed power symbols, add new
for u in [old_j2_uuid] + removed_pwr:
    m = re.search(r'\n    \(path "/[0-9a-f-]+/' + u + r'"\s+\(reference[^\n]*\n    \)', s); assert m, u; s = s[:m.start()] + s[m.end():]
add = "".join(f'\n    (path "{pth}"\n      (reference "{ref}") (unit 1) (value "{val}") (footprint "{fp}")\n    )' for pth, ref, val, fp in inst)
i = s.find("(symbol_instances") + len("(symbol_instances"); s = s[:i] + add + s[i:]
for u in dnp: pass
open(p, "w").write(s)
print("ok", len(inst), "instances added")
