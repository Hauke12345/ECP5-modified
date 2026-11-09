import pcbnew
P = "/work/route/eco/ecp5_routed.kicad_pcb"; b = pcbnew.LoadBoard(P)
for f in list(b.GetFootprints()):
    if str(f.GetReference()) == "FID5": f.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(136.2), pcbnew.FromMM(92.4)))
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(P, b); print("ok")
