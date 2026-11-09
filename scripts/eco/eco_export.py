import math
import pcbnew, json
import os
b = pcbnew.LoadBoard(os.environ["BOARD"])
ROUTE = json.load(open(os.environ["NETS"]))
ds = b.GetDesignSettings(); MM = pcbnew.ToMM
W = 0.127; IOCLR = 0.15; HOLECLR = MM(ds.m_HoleClearance); MARGIN = 0.0
LAY = {"F.Cu": pcbnew.F_Cu, "B.Cu": pcbnew.B_Cu}
def poly_pts(ps):
    out = []
    for i in range(ps.OutlineCount()):
        o = ps.Outline(i); out.append([(MM(o.CPoint(k).x), MM(o.CPoint(k).y)) for k in range(o.PointCount())])
    return out
def shape(item, lname, grow):
    ps = pcbnew.SHAPE_POLY_SET()
    item.TransformShapeToPolygon(ps, LAY[lname], pcbnew.FromMM(grow), pcbnew.FromMM(0.002), pcbnew.ERROR_OUTSIDE)
    return poly_pts(ps)
obst = []; terms = {}; vias = {}
def own_clr(item, lname):
    try: return MM(item.GetOwnClearance(LAY[lname]))
    except Exception: return 0.127
io_nets = {n.GetNetCode(): str(name) for name, n in b.GetNetsByName().items() if str(name) in ROUTE["nets"]}
pwr_pads = {(r, str(p)) for r, p in ROUTE["power_pads"]}
items = list(b.GetTracks()) + [p for fp in b.GetFootprints() for p in fp.Pads()]
for it in items:
    net = it.GetNetCode()
    for ln in LAY:
        if not it.IsOnLayer(LAY[ln]): continue
        clr = max(IOCLR, own_clr(it, ln))
        obst.append(dict(net=net, layer=ln, polys=shape(it, ln, clr + W / 2 + MARGIN)))
        is_pwr = it.GetClass() == "PAD" and (str(it.GetParentFootprint().GetReference()), str(it.GetNumber())) in pwr_pads
        if is_pwr:
            terms.setdefault("PWR:" + str(it.GetParentFootprint().GetReference()) + "." + str(it.GetNumber()), []).append(dict(layer=ln, ref=str(it.GetParentFootprint().GetReference()), pad=str(it.GetNumber()), polys=shape(it, ln, 0.0),
                                                  c=(MM(it.GetPosition().x), MM(it.GetPosition().y)), tht=it.HasHole(), net=net, netname=str(it.GetNetname())))
        if net in io_nets and it.GetClass() == "PAD" and not (io_nets[net] in ROUTE.get("partial", []) and str(it.GetParentFootprint().GetReference()) == "U1"):
            terms.setdefault(net, []).append(dict(layer=ln, ref=str(it.GetParentFootprint().GetReference()), pad=str(it.GetNumber()), polys=shape(it, ln, 0.0),
                                                  c=(MM(it.GetPosition().x), MM(it.GetPosition().y)), tht=it.HasHole()))
    # holes (vias + THT + NPTH): hole clearance on both outer layers
    if it.GetClass() in ("PCB_VIA",) or (it.GetClass() == "PAD" and it.HasHole()):
        d = MM(it.GetDrillValue() if it.GetClass() == "PCB_VIA" else min(it.GetDrillSize().x, it.GetDrillSize().y))
        p = it.GetPosition()
        for ln in LAY: obst.append(dict(net=net, layer=ln, circle=(MM(p.x), MM(p.y), d / 2 + HOLECLR + W / 2 + MARGIN)))
    if it.GetClass() == "PCB_VIA" and net in io_nets and io_nets[net] in ROUTE.get("partial", []) and MM(it.GetPosition().x) < 105:   # kept fan-out via = terminal
        p = it.GetPosition(); r = MM(it.GetWidth(pcbnew.F_Cu)) / 2
        poly = [[MM(p.x) + r * math.cos(a * math.pi / 12), MM(p.y) + r * math.sin(a * math.pi / 12)] for a in range(24)]
        terms.setdefault(net, []).append(dict(layer="F.Cu", ref="VIA", pad="", polys=[poly], c=(MM(p.x), MM(p.y)), tht=True))
    if it.GetClass() == "PCB_VIA" and net in io_nets:
        vias.setdefault(net, []).append((MM(it.GetPosition().x), MM(it.GetPosition().y), MM(it.GetWidth(pcbnew.F_Cu))))
# other copper: drawings + footprint graphics/text on copper layers (no net)
for d_ in list(b.GetDrawings()) + [g for fp in b.GetFootprints() for g in fp.GraphicalItems()] + [fp.Reference() for fp in b.GetFootprints()] + [fp.Value() for fp in b.GetFootprints()]:
    for ln in LAY:
        if d_.GetLayer() == LAY[ln] and d_.IsVisible() if hasattr(d_, "IsVisible") else d_.GetLayer() == LAY[ln]:
            try: obst.append(dict(net=0, layer=ln, polys=shape(d_, ln, IOCLR + W / 2 + MARGIN)))
            except Exception as e: print("skip", d_.GetClass(), e)
# footprint keep-out areas that forbid vias
novia = []
for fp in b.GetFootprints():
    for z in fp.Zones():
        if z.GetIsRuleArea() and z.GetDoNotAllowVias(): novia += poly_pts(z.Outline())
# board outline
ol = pcbnew.SHAPE_POLY_SET(); b.GetBoardPolygonOutlines(ol)
edge = max(MM(ds.m_CopperEdgeClearance), 0.01)
fpga = max(b.GetFootprints(), key=lambda f: len(f.Pads()))
balls = [(MM(p.GetPosition().x), MM(p.GetPosition().y)) for p in fpga.Pads()]
json.dump(dict(novia=novia, width=W, ioclr=IOCLR, holeclr=HOLECLR, margin=MARGIN, edge=edge, outline=poly_pts(ol), obst=obst,
               terms={(io_nets[k] if k in io_nets else k): v for k, v in terms.items()}, pwrnet={k: v[0]["net"] for k, v in terms.items() if isinstance(k, str)}, vias={io_nets[k]: v for k, v in vias.items()},
               netcode={v: k for k, v in io_nets.items()}, fpga=str(fpga.GetReference()), ball=balls[0]),
          open(os.environ["OUT"], "w"))
print("obstacles", len(obst), "io nets", len(terms), "nets with vias", len(vias), "fpga", fpga.GetReference(), len(fpga.Pads()), "edge", edge)
