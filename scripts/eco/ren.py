import pcbnew
P = "/work/route/eco/ecp5_routed.kicad_pcb"; b = pcbnew.LoadBoard(P)
m = {"Net-(D9-Pad3)": "Net-(RN3-Pad2)", "Net-(D10-Pad3)": "Net-(RN3-Pad3)", "Net-(D11-Pad3)": "Net-(RN3-Pad4)"}
new = {}
for o, n in m.items():
    ni = pcbnew.NETINFO_ITEM(b, n); b.Add(ni); new[o] = ni
cnt = 0
for f in list(b.GetFootprints()):
    for p in list(f.Pads()):
        if str(p.GetNetname()) in new: p.SetNet(new[str(p.GetNetname())]); cnt += 1
for t in list(b.GetTracks()):
    if str(t.GetNetname()) in new: print("track", t.GetNetname())
pcbnew.SaveBoard(P, b); print("pads", cnt)
