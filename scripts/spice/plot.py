import json, numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
C = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]; INK, MUTED, GRID, SURF = "#1f1f1e", "#6b6a63", "#e6e5e0", "#fcfcfb"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED})
I = json.load(open("i2c_results.json")); T = json.load(open("tck_results.json"))
fig, (a, b) = plt.subplots(1, 2, figsize=(15, 6.6), facecolor=SURF, gridspec_kw=dict(wspace=0.22))
for ax in (a, b):
    ax.set_facecolor(SURF); ax.grid(True, color=GRID, lw=0.8); ax.spines[["top", "right"]].set_visible(False)
short = ["Board alone", "1 sensor, 10k, 100 mm", "3 SparkFun, 2.2k each, 600 mm", "5 boards, 1 m, only our 4k7"]
for i, r in enumerate(I):
    d = np.loadtxt(f"fpga_{i}.dat"); t = (d[:, 0] - 4.255e-6) * 1e9; m = (t > -100) & (t < 1100)
    a.plot(t[m], d[m, 1], color=C[i], lw=2, label=f"{short[i]}: rise {r['fpga_trise']*1e9:.0f} ns, {r['C']:.0f} pF")
for y, txt in ((0.3 * 3.3, "30 %"), (0.7 * 3.3, "70 %")):
    a.axhline(y, color=MUTED, lw=1, ls="--"); a.text(1095, y + 0.05, txt, color=MUTED, ha="right", fontsize=10)
a.axvline(300, color="#e34948", lw=1.2, ls=":"); a.text(308, 3.48, "400 kHz limit (300 ns)", color=INK, fontsize=10)
a.set_xlim(-100, 1100); a.set_ylim(-0.1, 3.7); a.set_xlabel("time after the line is released (ns)"); a.set_ylabel("SDA / SCL voltage (V)")
a.set_title("I²C on PORT_H0/H1: rising edge (4k7 pull-ups)", loc="left", color=INK, fontsize=14, fontweight="bold")
a.legend(loc="lower right", frameon=False, fontsize=9.5, bbox_to_anchor=(1.0, 0.03))
lab = {20: "probe, no series R", 53: "probe + 33 Ω series", 120: "probe + 100 Ω series"}
k = 0
for r in T:
    if r["tr"] != 1.0: continue
    i = [20, 53, 120].index(r["rs"]); d = np.loadtxt(f"tck_{i}_1.dat"); t = d[:, 0] * 1e9; m = (t > 52) & (t < 100)
    b.plot(t[m] - 55, d[m, 1], color=C[k], lw=2, label=f"{lab[r['rs']]}: peak {r['vmax']:.1f} V, ring stays ≥ {r['dip']:.1f} V"); k += 1
b.axhspan(0.8, 2.0, color="#e34948", alpha=0.08); b.text(44.5, 1.35, "undefined zone\n0.8–2.0 V", color=INK, ha="right", va="center", fontsize=10)
b.set_xlim(-3, 45); b.set_ylim(-1.3, 4.6); b.set_xlabel("time (ns), 1 ns edges from the probe"); b.set_ylabel("TCK at the FPGA ball (V)")
b.set_title("JTAG TCK through a 25 cm TC2050 cable", loc="left", color=INK, fontsize=14, fontweight="bold")
b.legend(loc="upper right", frameon=False, fontsize=9.5)
fig.text(0.07, 0.015, "ngspice transient · board values from the routed Rev 1.1 PCB (trace lengths, 0.17 mm dielectric microstrip 72 Ω / 0.083 pF/mm) · ECP5 pin 7 pF with ESD clamps · cable/device values typical, not measured",
         color=MUTED, fontsize=9)
fig.savefig("/home/claude/route/deliver/eco_spice_checks.png", dpi=110, bbox_inches="tight", facecolor=SURF); print("ok")
