"""TCK through a Tag-Connect TC2050 cable into the ECP5: overshoot / ringing / double-clock risk (ngspice, lossless lines)."""
import subprocess, re, json
VDD = 3.3
# board: TC2050 pad -> 8.3 mm B.Cu -> via -> 11.7 mm F.Cu -> ball T10 (ECP5 ~7 pF), R8 10k pull-down, 3 vias ~0.3 pF
cases = [("probe driver, no series R (~20 ohm)", 20), ("probe with 33 ohm series", 53), ("probe with 100 ohm series", 120)]
res = []
for i, (name, rs) in enumerate(cases):
    for tr in (1.0, 3.0):
        net = f"""* TCK {name} tr={tr}ns
Vs src 0 PULSE(0 {VDD} 5n {tr}n {tr}n 22n 50n)
Rs src a {rs}
* TC2050-IDC-NL cable, ~250 mm 0.05in ribbon, signal next to GND (ARM-10): Z0 ~110 ohm, ~4.8 ns/m
T1 a 0 b 0 Z0=110 TD=1.2n
Lpogo b c 2n
Cpad c 0 0.4p
T2 c 0 d 0 Z0=72 TD=0.049n
Cvia d 0 0.9p
T3 d 0 e 0 Z0=72 TD=0.070n
Cin e 0 7p
R8 e 0 10k
* ESD clamp diodes of the FPGA pin
Vio vio 0 {VDD}
D1 e vio dclamp
D2 0 e dclamp
.model dclamp D(Is=1e-14 N=1.2 Rs=5)
.tran 0.01n 110n
.control
run
meas tran vmax MAX v(e) FROM=55n TO=75n
meas tran vmin MIN v(e) FROM=80n TO=100n
meas tran t1 WHEN v(e)=2.0 RISE=2
let f1 = t1 + 0.3e-9
meas tran dip MIN v(e) FROM=$&f1 TO=75n
meas tran t2 WHEN v(e)=0.8 FALL=2
let f2 = t2 + 0.3e-9
meas tran bump MAX v(e) FROM=$&f2 TO=100n
wrdata tck_{i}_{int(tr)}.dat v(e) v(a)
quit
.endc
.end
"""
        open(f"tck_{i}_{int(tr)}.cir", "w").write(net)
        o = subprocess.run(["ngspice", "-b", f"tck_{i}_{int(tr)}.cir"], capture_output=True, text=True).stdout
        r = {k: float(re.search(rf"^{k}\s*=\s*([-\d.eE+]+)", o, re.M).group(1)) for k in ("vmax", "vmin", "dip", "bump")}
        r.update(name=name, rs=rs, tr=tr); res.append(r)
        print(f"{name:38s} tr {tr} ns | peak {r['vmax']:.2f} V  dip after rise {r['dip']:.2f} V | undershoot {r['vmin']:.2f} V  bump after fall {r['bump']:.2f} V")
json.dump(res, open("tck_results.json", "w"), indent=1)
