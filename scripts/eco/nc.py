import pcbnew
P = "/work/route/eco/ecp5_routed.kicad_pcb"; b = pcbnew.LoadBoard(P)
j2 = next(f for f in b.GetFootprints() if str(f.GetReference()) == "J2")
for p in list(j2.Pads()):
    if str(p.GetNumber()) in ("7", "10"):
        n = pcbnew.NETINFO_ITEM(b, f"unconnected-(J2-Pin_{p.GetNumber()}-Pad{p.GetNumber()})"); b.Add(n); p.SetNet(n)
pcbnew.SaveBoard(P, b); print("ok")
