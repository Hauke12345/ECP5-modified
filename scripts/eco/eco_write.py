import pcbnew, json, sys
b = pcbnew.LoadBoard("/work/route/eco/ecp5.kicad_pcb")
R = json.load(open("/work/route/eco_result.json")); nets = b.GetNetsByName(); FM = pcbnew.FromMM
for s in R["segs"]:
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(pcbnew.VECTOR2I(FM(s["x1"]), FM(s["y1"]))); t.SetEnd(pcbnew.VECTOR2I(FM(s["x2"]), FM(s["y2"])))
    t.SetWidth(FM(0.127)); t.SetLayer(b.GetLayerID(s["layer"])); t.SetNet(nets[s["net"]]); b.Add(t)
for v in R["vias"]:
    via = pcbnew.PCB_VIA(b); via.SetPosition(pcbnew.VECTOR2I(FM(v["x"]), FM(v["y"])))
    via.SetViaType(pcbnew.VIATYPE_THROUGH); via.SetWidth(FM(0.45)); via.SetDrill(FM(0.25))
    via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); via.SetNet(nets[v["net"]]); b.Add(via)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard("/work/route/eco/ecp5_routed.kicad_pcb", b)
print("added", len(R["segs"]), "segments and", len(R["vias"]), "vias; unplaced", R["unplaced"])
