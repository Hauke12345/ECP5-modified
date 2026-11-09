import pcbnew
P = "/work/route/eco/ecp5_routed.kicad_pcb"; b = pcbnew.LoadBoard(P)
libs = {"J6": "Connector_JST", "R31": "Resistor_SMD", "R32": "Resistor_SMD", "J2": "Connector"}
for f in list(b.GetFootprints()):
    r = str(f.GetReference())
    if r in libs:
        f.SetFPID(pcbnew.LIB_ID(libs[r], str(f.GetFPID().GetLibItemName())))
        if r == "J2": f.SetValue("JTAG TC2050 (ARM-10)")
pcbnew.SaveBoard(P, b); print("ok")
