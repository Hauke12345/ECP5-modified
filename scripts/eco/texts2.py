import pcbnew
P = "/work/route/eco/ecp5_routed.kicad_pcb"; b = pcbnew.LoadBoard(P); MM, FM = pcbnew.ToMM, pcbnew.FromMM
for d in list(b.GetDrawings()):
    if d.GetClass() != "PCB_TEXT": continue
    t, x = d.GetText(), MM(d.GetPosition().x)
    if t in ("3V3", "GND", "TCK", "TDO", "TDI", "TMS") and abs(x - 99.1) < 0.01: b.Remove(d)
    elif t == "7" and abs(x - 101.4) < 0.01: d.SetText("4"); d.SetPosition(pcbnew.VECTOR2I(FM(101.4), FM(92.45)))
pcbnew.SaveBoard(P, b); print("ok")
