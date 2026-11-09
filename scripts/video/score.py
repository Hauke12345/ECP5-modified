"""Soundtrack for the ECO speedrun film (same synth + style as the schematic speedrun).
usage: score.py DIR  (reads DIR/events.json, writes DIR/mix.wav)"""
import sys, json, numpy as np
from scipy.io import wavfile
from scipy.signal import fftconvolve
sys.path.insert(0, "/home/claude/boili_youtube")
import synth as S
from synth import SR

DIR = sys.argv[1]; J = json.load(open(f"{DIR}/events.json")); M = J["marks"]; EV = J["events"]; DUR = J["total"]
N = int(DUR * SR) + SR
music = np.zeros((N, 2)); sfx = np.zeros((N, 2)); send = np.zeros((N, 2)); duck = np.ones(N)
rng = np.random.default_rng(5)
def put(buf, t, x, g=1.0):
    o = int(t * SR); a = max(0, -o); m = min(len(x), N - o)
    if m > a: buf[o + a:o + m] += x[a:m] * g
def fx(t, x, g=1.0, rev=0.25): put(sfx, t, x, g); put(send, t, x, g * rev)
BEAT = 0.5
A_MIN = [(57, [57, 60, 64]), (53, [53, 57, 60]), (48, [55, 60, 64]), (55, [55, 59, 62])]
B_MIN = [(59, [59, 62, 66]), (55, [55, 59, 62]), (50, [57, 62, 66]), (57, [57, 61, 64])]
def drums(t0, t1, kick=True, clap=True, hat_vol=0.06, open_hats=False):
    b = 0
    while t0 + b * 2 < t1 - 0.1:
        for q in range(4):
            tb = t0 + (b * 4 + q) * BEAT
            if tb >= t1: break
            if kick:
                put(music, tb, S.kick()); i = int(tb * SR); L = int(0.25 * SR); duck[i:i + L] = np.minimum(duck[i:i + L], np.linspace(0.45, 1, L))
            if clap and q in (1, 3): put(music, tb, S.clap())
            put(music, tb + BEAT / 2, S.hat(hat_vol * 2.0, open_=open_hats)); put(music, tb + BEAT / 4, S.hat(hat_vol * 0.9)); put(music, tb + 3 * BEAT / 4, S.hat(hat_vol * 0.9, p=-0.25))
        b += 1
def harmony(t0, t1, prog, pad_vol=0.10, bright=1400, bass_pat="half", arp=None, arp_vol=0.10):
    b = 0
    while t0 + b * 2 < t1 - 0.1:
        root, chord = prog[b % 4]; tb = t0 + b * 2
        put(music, tb, S.pad(chord + [chord[0] + 12], min(2.6, t1 - tb + 0.6), bright, pad_vol))
        if bass_pat == "half":
            for h in range(2):
                if tb + h < t1: put(music, tb + h, S.bass(root - 12, 0.95))
        else:
            for e in range(8):
                if e % 2 == 1 and tb + e * 0.25 < t1: put(music, tb + e * 0.25, S.bass(root - 12, 0.225, 0.24))
        if arp:
            notes = sorted(chord) + [chord[0] + 12, chord[1] + 12]
            steps, order = {"8": (8, [0, 2, 1, 3, 2, 4, 3, 1]), "16": (16, [0, 2, 4, 2, 1, 3, 5, 3, 0, 2, 4, 5, 3, 2, 1, 2])}[arp]
            for k in range(steps):
                tk = tb + k * 2 / steps
                if tk < t1: put(music, tk, S.pluck(notes[order[k] % len(notes)] + 12, 0.32, arp_vol, 5500, p=0.35 * np.sin(k)))
        b += 1
def motif(t0, notes, vol=0.12):
    for bt, m, d in notes: put(music, t0 + bt * BEAT, S.pluck(m, d * BEAT + 0.3, vol, 4500, 0.1))

GO, T2, FAIL, FIX, T3, R1, T4, T5, END = (M[k] for k in ("go", "t2", "fail", "fix", "t3", "r1", "t4", "t5", "end"))
# intro: soft pad + typing
put(music, 0.0, S.pad([57, 64, 71, 76], GO + 0.3, 900, 0.09)); fx(0.05, S.impact(0.25), rev=0.5)
for t, k in EV:
    if k == "type": fx(t, S.ui_click(0.07, 2400 + rng.integers(0, 900), rng.uniform(-0.3, 0.3)), rev=0.05)
fx(GO - 1.2, S.riser(1.2, 0.16)); fx(GO, S.impact(0.42), rev=0.5)
# part 1 + 2 (until the dead end): driving A minor groove
put(music, GO, S.kick(0.5))
harmony(GO, FAIL, A_MIN, pad_vol=0.09, bright=3000, bass_pat="drive", arp="16", arp_vol=0.10); drums(GO, FAIL)
# the dead end: stop, buzz, tension pad, then the fix
put(music, FAIL, S.pad([57, 60, 63, 66], FIX - FAIL + 0.4, 1100, 0.10))
fx(FAIL, S.beep(330, 0.07, 0.14, 0)); fx(FAIL + 0.17, S.beep(247, 0.07, 0.25, 0))
fx(FIX, S.ding(88, 0.10)); fx(FIX + 0.12, S.ding(93, 0.08))
fx(T3 - 1.3, S.riser(1.3, 0.16)); fx(T3 - 0.03, S.impact(0.4), rev=0.5)
# part 3 + 4: routing in B minor, open hats
put(music, T3, S.kick(0.5))
harmony(T3, T5, B_MIN, pad_vol=0.09, bright=3200, bass_pat="drive", arp="16", arp_vol=0.10); drums(T3, T5, open_hats=True)
for t, k in EV:
    p = rng.uniform(-0.4, 0.4)
    if k == "mark": fx(t, S.beep(1320, 0.05, 0.06, p))
    elif k == "remove": fx(t, S.drill(0.35, 0.10)); fx(t + 0.05, S.whoosh(0.4, 0.07, up=False, p=p))
    elif k == "shift": fx(t, S.ratchet(5, 0.07))
    elif k == "place": fx(t, S.clack(0.10, p)); fx(t + 0.03, S.pop(0.08, 420, 980, p))
    elif k == "move": fx(t, S.whoosh(0.4, 0.06, up=True, p=p))
    elif k == "scan": fx(t, S.tick(0.06, p))
    elif k == "wire": fx(t, S.zip_(0.045, 0.12, p))
    elif k == "via": fx(t, S.pop(0.07, 600, 1200, p))
    elif k == "explode": fx(t - 0.1, S.whoosh(0.9, 0.12, up=True, p=0.0)); fx(t + 0.9, S.ding(86, 0.07)); fx(t + 1.25, S.ding(90, 0.06)); fx(t + 1.6, S.ding(93, 0.06)); fx(t + 1.95, S.ding(98, 0.06))
    elif k == "wipe": fx(t, S.whoosh(0.8, 0.10, up=True, p=-0.3))
    elif k == "callout": fx(t, S.pop(0.10, 500, 1100, -0.2)); fx(t + 0.25, S.pop(0.09, 560, 1250, 0.2))
    elif k == "check": fx(t, S.success(79, 0.10), rev=0.4)
    elif k == "check2": fx(t, S.fanfare(71, 0.13), rev=0.4)
# part 5: SPICE, calm
put(music, T5, S.pad([59, 66, 71, 74], 1.4, 2500, 0.11)); fx(T5, S.impact(0.3), rev=0.5)
harmony(T5 + 0.5, END, A_MIN, pad_vol=0.09, bright=1500, arp="8", arp_vol=0.08); drums(T5 + 0.5, END, clap=False, hat_vol=0.04)
fx(M["s_i2c"], S.power_up(0.10, 200, 900, 0.6)); fx(M["s_tck"], S.data_chirps(1.6, 0.04))
fx(M["s_i2c"] + 3.1, S.ding(86, 0.08)); fx(M["s_tck"] + 3.1, S.ding(89, 0.08))
# end card
fx(END, S.impact(0.3), rev=0.6)
put(music, END, S.pad([59, 66, 71, 74, 78], DUR - END + 0.5, 1600, 0.13))
motif(END + 0.3, [(0, 78, 2), (2, 81, 1), (3, 83, 1), (4, 81, 2)], 0.10)

ir = S.reverb_ir(2.4, 2.8)
wet = np.stack([fftconvolve(music[:, c] * 0.22 + send[:, c], ir[:, c])[:N] for c in range(2)], 1)
music = music * duck[:, None] + wet * 0.9
fade = np.ones(N); fs_ = int((DUR - 1.2) * SR); fade[fs_:] = np.linspace(1, 0, N - fs_).clip(0, 1)
g = lambda db: 10 ** (db / 20)
mix = (music * g(12.0) + sfx * g(13.5)) * fade[:, None]
mix = mix[: int(DUR * SR)] / 4
pk = np.max(np.abs(mix)); mix = mix / max(pk, 1e-9) * 0.89
wavfile.write(f"{DIR}/mix.wav", SR, mix.astype(np.float32))
print("ok", round(DUR, 1), "peak was", round(pk, 3))
