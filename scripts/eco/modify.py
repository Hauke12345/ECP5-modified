"""ECO on ECP5 Mini: JTAG header -> Tag-Connect TC2050 (ARM 10-pin pinout, bottom), add Qwiic I2C port (top-left),
drop RGB LEDs D9-D11, shift D4-D8 down 0.25 mm. Rips up the nets that need rerouting; routing is done separately."""
import pcbnew, json
FM = pcbnew.FromMM; MM = pcbnew.ToMM
b = pcbnew.LoadBoard("/work/route/k9/ecp5.kicad_pcb")
fps = {str(f.GetReference()): f for f in b.GetFootprints()}
nets = b.GetNetsByName()
JTAG = ["/FPGA Config/TCK", "/FPGA Config/TDO", "/FPGA Config/TDI", "/FPGA Config/TMS"]
LED = ["/LEDs/CAT_R", "/LEDs/CAT_G", "/LEDs/CAT_B"] + [f"Net-(D{i}-Pad3)" for i in range(4, 12)]
# 1. rip up copper of nets that will be rerouted
rip = set(LED)
# JTAG: keep the human fan-out (F.Cu + vias near x 103.3); only the B.Cu runs to the old header are removed
gone = [t for t in b.GetTracks() if str(t.GetNetname()) in rip or
        (str(t.GetNetname()) in JTAG and t.GetClass() == "PCB_TRACK" and t.GetLayer() == pcbnew.B_Cu
         and max(MM(t.GetStart().x), MM(t.GetEnd().x)) < 104.5)]
for t in gone: b.Remove(t)
# 2. remove old JTAG header and three LEDs
for r in ("J2", "D9", "D10", "D11"): b.Remove(fps[r])
# 3. shift remaining LED column down
for r in ("D4", "D5", "D6", "D7", "D8"):                         # keep 2.2 mm pitch, shift the column down 0.21 mm
    f = fps[r]; f.SetPosition(f.GetPosition() + pcbnew.VECTOR2I(0, FM(0.20)))
import os
fid = json.loads(os.environ.get("FID", "{}"))
for r, (x, y) in fid.items(): fps[r].SetPosition(pcbnew.VECTOR2I(FM(x), FM(y)))
# 3b. nudge PORT_A0 / PORT_A4 diagonals (0.16 / 0.07 mm to the right) where they pass under the shifted D4
def P(x, y): return pcbnew.VECTOR2I(FM(x), FM(y))
def near(p, q): return abs(MM(p.x) - q[0]) < 0.002 and abs(MM(p.y) - q[1]) < 0.002
def move_pt(netname, old, new):
    n = 0
    for t in b.GetTracks():
        if t.GetClass() != "PCB_TRACK" or str(t.GetNetname()) != netname: continue
        if near(t.GetStart(), old): t.SetStart(P(*new)); n += 1
        if near(t.GetEnd(), old): t.SetEnd(P(*new)); n += 1
    assert n == 2, (netname, old, n)
move_pt("/PORT_A0", (103.577, 103.023), (103.737, 103.023)); move_pt("/PORT_A0", (102.577, 104.023), (102.737, 104.023))
move_pt("/PORT_A4", (103.792, 103.3), (103.86, 103.3));      move_pt("/PORT_A4", (102.792, 104.3), (102.86, 104.3))
# 4. new nets
def net(name):
    if name in nets: return nets[name]
    n = pcbnew.NETINFO_ITEM(b, name); b.Add(n); nets[name] = n; return n
# Qwiic shares two existing header GPIOs (J4 pins 1/3, right above the connector) - no new FPGA fan-out needed
SDA, SCL = "/PORT_H1", "/PORT_H0"
LIB = "/usr/share/kicad/footprints/"
def add(lib, name, ref, value, x, y, rot, back, pinnets):
    f = pcbnew.FootprintLoad(LIB + lib + ".pretty", name)
    f.SetReference(ref); f.SetValue(value); b.Add(f)
    f.SetPosition(pcbnew.VECTOR2I(FM(x), FM(y))); f.SetOrientationDegrees(rot)
    if back: f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT if hasattr(pcbnew, "FLIP_DIRECTION_LEFT_RIGHT") else False)
    for p in f.Pads():
        n = pinnets.get(str(p.GetNumber()))
        if n: p.SetNet(nets[n] if isinstance(n, str) else n)
    return f
G, V = "GND", "+3V3"
# Qwiic / STEMMA QT: 1 GND, 2 3V3, 3 SDA, 4 SCL; opening towards the left board edge
add("Connector_JST", "JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal", "J6", "Qwiic I2C", 99.53, 89.03, -90, False,
    {"1": G, "2": V, "3": SDA, "4": SCL, "MP": G})
# pull-ups under the connector (bottom side)
add("Resistor_SMD", "R_0402_1005Metric", "R31", "4k7", 97.3, 88.2, 90, True, {"1": SCL, "2": V})
add("Resistor_SMD", "R_0402_1005Metric", "R32", "4k7", 98.7, 88.2, 90, True, {"1": SDA, "2": V})
# JTAG: Tag-Connect TC2050 pads, ARM Cortex 10-pin pinout (1 VTref, 2 TMS, 3 GND, 4 TCK, 5 GND, 6 TDO, 7 key, 8 TDI, 9 GND, 10 nRESET)
add("Connector", "Tag-Connect_TC2050-IDC-NL_2x05_P1.27mm_Vertical", "J2", "JTAG TC2050 (ARM-10)", 98.3, 97.0, 90, True,
    {"1": V, "2": JTAG[3], "3": G, "4": JTAG[0], "5": G, "6": JTAG[1], "8": JTAG[2], "9": G})
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard("/work/route/eco/ecp5.kicad_pcb", b)
print("ripped", len(gone), "track/via items; footprints now", len(b.GetFootprints()))
for r in ("J6", "R31", "R32", "J2"):
    f = next(f for f in b.GetFootprints() if str(f.GetReference()) == r)
    cy = f.GetCourtyard(pcbnew.B_CrtYd if f.IsFlipped() else pcbnew.F_CrtYd).BBox()
    print(r, "B" if f.IsFlipped() else "F", "courtyard x", round(MM(cy.GetLeft()), 2), round(MM(cy.GetRight()), 2), "y", round(MM(cy.GetTop()), 2), round(MM(cy.GetBottom()), 2))
