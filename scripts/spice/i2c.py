"""I2C on the shared PORT_H0/H1 lines: rise time, fall time and V_OL for realistic Qwiic set-ups (ngspice)."""
import subprocess, re, json
VDD = 3.3
# board-side capacitance of PORT_H0 (worst of H0/H1): 24.9 mm of 0.127 mm microstrip @ 0.083 pF/mm, 2 vias,
# ECP5 I/O pin (~7 pF, datasheet range 5-8 pF), J4 header pad + J6 pad + R pad (~1.5 pF)
C_board = 24.9 * 0.083 + 2 * 0.3 + 7 + 1.5
def par(*r): return 1 / sum(1 / x for x in r)
CABLE = 0.05  # pF per mm, 28 AWG 4-wire Qwiic cable (~50 pF/m)
S = [  # name, extra pull-ups on the bus, cable mm, devices
    ("Board alone (nothing plugged in)", [], 0, 0),
    ("1 Adafruit STEMMA QT sensor, 100 mm cable (10k on board)", [10e3], 100, 1),
    ("3 SparkFun Qwiic boards, 3 x 200 mm (2.2k each, default on)", [2.2e3] * 3, 600, 3),
    ("5 boards, 1 m cable, extra pull-ups cut (only our 4k7)", [], 1000, 5),
]
DEV_C = 10.0  # pF per device (pin + its board)
res = []
for name, pu, cab, ndev in S:
    Rp = par(4.7e3, *pu); C = C_board + cab * CABLE + ndev * DEV_C
    out = {}
    for who, ron in (("fpga", 40.0), ("slave", 133.0)):     # FPGA LVCMOS33 8 mA driver vs a 3 mA-class I2C slave (0.4 V @ 3 mA)
        net = f"""* {name}
VDD vdd 0 {VDD}
Rp vdd bus {Rp}
Cb bus 0 {C}p
Vc ctl 0 PULSE(0 1 0.5u 5n 5n 1.25u 2.5u)
S1 bus 0 ctl 0 sw
.model sw SW(Ron={ron} Roff=1e9 Vt=0.5 Vh=0.01)
.tran 1n 6u
.control
run
meas tran tfall TRIG v(bus) VAL={0.7*VDD} FALL=2 TARG v(bus) VAL={0.3*VDD} FALL=2
meas tran trise TRIG v(bus) VAL={0.3*VDD} RISE=2 TARG v(bus) VAL={0.7*VDD} RISE=2
meas tran vol MIN v(bus) FROM=3u TO=4.2u
meas tran vhigh MAX v(bus) FROM=4.3u TO=5.5u
wrdata {who}_{len(res)}.dat v(bus)
quit
.endc
.end
"""
        open("i2c_tmp.cir", "w").write(net)
        o = subprocess.run(["ngspice", "-b", "i2c_tmp.cir"], capture_output=True, text=True).stdout
        for k in ("tfall", "trise", "vol", "vhigh"):
            m = re.search(rf"^{k}\s*=\s*([-\d.eE+]+)", o, re.M); out[f"{who}_{k}"] = float(m.group(1)) if m else None
        open(f"i2c_{len(res)}_{who}.cir", "w").write(net)
    out.update(name=name, Rp=Rp, C=C, Isink=VDD / Rp * 1e3)
    res.append(out)
    print(f"{name}\n   Rp {Rp:.0f} ohm  Cbus {C:.0f} pF  rise {out['fpga_trise']*1e9:.0f} ns  fall {out['fpga_tfall']*1e9:.1f} ns  "
          f"VOL fpga {out['fpga_vol']:.3f} V  VOL weak slave {out['slave_vol']:.3f} V  sink {out['Isink']:.2f} mA")
json.dump(res, open("i2c_results.json", "w"), indent=1)
print("C_board", round(C_board, 1), "pF")
