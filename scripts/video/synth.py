"""Tiny numpy synthesiser: instruments, drums and sound effects for the Boili film soundtrack."""
import numpy as np
from scipy import signal

SR = 48000
rng = np.random.default_rng(7)

def mtof(m): return 440.0 * 2 ** ((m - 69) / 12)
def t_(n): return np.arange(n) / SR

def adsr(n, a=0.01, d=0.1, s=0.7, r=0.2):
    a, d, r = int(a * SR), int(d * SR), int(r * SR)
    s_len = max(n - a - d - r, 0)
    env = np.concatenate([np.linspace(0, 1, a, endpoint=False), np.linspace(1, s, d, endpoint=False),
                          np.full(s_len, s), np.linspace(s, 0, r)])
    return np.pad(env, (0, max(0, n - len(env))))[:n]

def lp(x, fc, order=2):
    sos = signal.butter(order, min(fc, SR * 0.45), "low", fs=SR, output="sos"); return signal.sosfilt(sos, x)
def hp(x, fc, order=2):
    sos = signal.butter(order, fc, "high", fs=SR, output="sos"); return signal.sosfilt(sos, x)
def bp(x, f0, f1, order=2):
    sos = signal.butter(order, [f0, min(f1, SR * 0.45)], "band", fs=SR, output="sos"); return signal.sosfilt(sos, x)

def saw(f, n, phase=0.0):
    ph = (phase + np.cumsum(np.broadcast_to(f, (n,)) / SR)) % 1.0
    return 2 * ph - 1
def sq(f, n): return np.sign(saw(f, n))
def sine(f, n, phase=0.0):
    return np.sin(2 * np.pi * (phase + np.cumsum(np.broadcast_to(f, (n,)) / SR)))

# ------------------------------------------------------------------ instruments (return stereo [n,2])
def pan(x, p):                                   # p in [-1, 1]
    l, r = np.cos((p + 1) * np.pi / 4), np.sin((p + 1) * np.pi / 4)
    return np.stack([x * l, x * r], 1)

def pad(midis, dur, bright=1200, vol=0.12):
    n = int(dur * SR); out = np.zeros((n, 2))
    for k, m in enumerate(midis):
        for det, p in ((-0.11, -0.7), (0.0, 0.0), (0.12, 0.7)):
            x = saw(mtof(m + det), n, rng.random())
            out += pan(x, p * (0.6 + 0.1 * k))
    out[:, 0] = hp(lp(out[:, 0], bright), 160); out[:, 1] = hp(lp(out[:, 1], bright), 160)
    return out * adsr(n, 0.6, 0.3, 0.85, 0.8)[:, None] * vol / len(midis)

def pluck(m, dur=0.45, vol=0.18, bright=5000, p=0.0):
    n = int(dur * SR)
    x = 0.6 * saw(mtof(m), n) + 0.4 * sq(mtof(m) * 1.002, n)
    env = np.exp(-t_(n) * 7)
    y = lp(x, 500) * (1 - env) * 0.6 + lp(x, bright) * env      # filter envelope by crossfade
    return pan(y * adsr(n, 0.003, 0.05, 0.9, 0.08) * env * vol, p)

def bell(m, dur=1.2, vol=0.15, p=0.0):
    n = int(dur * SR); t = t_(n); f = mtof(m)
    mod = np.sin(2 * np.pi * f * 3.5 * t) * 2.2 * np.exp(-t * 6)
    x = np.sin(2 * np.pi * f * t + mod) * np.exp(-t * 3.2)
    return pan(x * vol * adsr(n, 0.002, 0.05, 1, 0.1), p)

def bass(m, dur, vol=0.10):
    n = int(dur * SR); f = mtof(m)
    x = 0.7 * saw(f, n) + 0.5 * sine(f / 2, n)
    env = adsr(n, 0.005, 0.12, 0.65, 0.05)
    y = hp(lp(x, 900, 2), 38) * env
    return pan(y * vol, 0)

def kick(vol=0.42):
    n = int(0.42 * SR); t = t_(n)
    f = 45 + 110 * np.exp(-t * 28)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 11)
    x += 0.25 * hp(rng.standard_normal(n), 3000) * np.exp(-t * 180)
    return pan(np.tanh(x * 1.6) * vol, 0)

def clap(vol=0.22):
    n = int(0.3 * SR); t = t_(n)
    env = np.zeros(n)
    for o in (0, 0.011, 0.022): env += np.exp(-np.clip(t - o, 0, None) * 60) * (t >= o)
    env += 0.5 * np.exp(-t * 12)
    x = bp(rng.standard_normal(n), 900, 5200) * env
    return pan(x * vol, 0.1)

def hat(vol=0.07, open_=False, p=0.25):
    n = int((0.25 if open_ else 0.06) * SR); t = t_(n)
    x = hp(rng.standard_normal(n), 7500) * np.exp(-t * (14 if open_ else 70))
    return pan(x * vol, p)

# ------------------------------------------------------------------ sound effects
def ui_click(vol=0.25, f=2600, p=0.0):
    n = int(0.05 * SR); t = t_(n)
    x = np.sin(2 * np.pi * f * t) * np.exp(-t * 160) + 0.4 * hp(rng.standard_normal(n), 4000) * np.exp(-t * 400)
    return pan(x * vol, p)

def tick(vol=0.12, p=0.0): return ui_click(vol, 3600, p)

def pop(vol=0.25, f0=420, f1=900, p=0.0):          # a feature appears
    n = int(0.16 * SR); t = t_(n)
    f = f0 + (f1 - f0) * (1 - np.exp(-t * 40))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 22)
    return pan(x * vol, p)

def whoosh(dur=0.6, vol=0.22, up=True, p=0.0):
    n = int(dur * SR); t = t_(n) / dur
    x = rng.standard_normal(n)
    fc = (300 + 4500 * t ** 1.5) if up else (4800 - 4400 * t ** 0.7)
    # time-varying lowpass via short blocks
    y = np.zeros(n); blk = 1024
    zi = None
    for i in range(0, n, blk):
        sos = signal.butter(2, [max(80, fc[i] * 0.35), min(fc[i], SR * 0.45)], "band", fs=SR, output="sos")
        if zi is None: zi = signal.sosfilt_zi(sos) * 0
        y[i:i + blk], zi = signal.sosfilt(sos, x[i:i + blk], zi=zi)
    env = np.sin(np.pi * np.clip(t, 0, 1)) ** (0.8 if up else 1.4)
    out = np.stack([y * env, np.roll(y, 240) * env], 1) * vol
    return out * np.array([np.cos((p + 1) * np.pi / 4), np.sin((p + 1) * np.pi / 4)]) * 1.4

def riser(dur=1.8, vol=0.22):
    n = int(dur * SR); t = t_(n) / dur
    f = 200 * 2 ** (t * 3.2)
    tone = 0.35 * saw(f, n) + 0.35 * saw(f * 1.007, n)
    noise = rng.standard_normal(n)
    y = lp(tone, 2500) * t ** 2 + hp(noise, 1500) * t ** 3 * 0.8
    return np.stack([y, np.roll(y, 300)], 1) * vol

def impact(vol=0.5):
    n = int(1.6 * SR); t = t_(n)
    f = 38 + 70 * np.exp(-t * 10)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 3.0)
    crash = hp(rng.standard_normal(n), 2500) * np.exp(-t * 3.5) * 0.35
    y = np.tanh(sub * 1.4) + crash
    return np.stack([y, y * 0.96 + np.roll(crash, 400) * 0.1], 1) * vol

def ding(m=84, vol=0.12, p=0.3): return bell(m, 0.9, vol, p)

def success(root=76, vol=0.13):
    out = np.zeros((int(1.8 * SR), 2))
    for k, iv in enumerate((0, 4, 7, 12)):
        b = bell(root + iv, 1.4, vol, -0.3 + 0.2 * k); o = int(k * 0.09 * SR)
        out[o:o + len(b)] += b[: len(out) - o]
    return out

def fanfare(root=69, vol=0.16):
    out = np.zeros((int(3.0 * SR), 2))
    for k, (iv, d) in enumerate(((0, 0.12), (7, 0.12), (12, 0.12), (16, 2.4))):
        o = int(sum(x[1] for x in ((0, 0.12), (7, 0.12), (12, 0.12), (16, 2.4))[:k]) * SR)
        b = bell(root + iv, d + 0.6, vol, 0); pl = pluck(root + iv, d + 0.4, vol * 0.8); b[:len(pl)] += pl
        out[o:o + len(b)] += b[: len(out) - o]
    return out

def relay_click(vol=0.35, heavy=False):
    n = int((0.25 if heavy else 0.08) * SR); t = t_(n)
    out = np.zeros(n)
    for o, a in ((0.0, 1.0), (0.006, 0.5), (0.017, 0.3)):
        k = int(o * SR); m = n - k
        out[k:] += a * bp(rng.standard_normal(m), 1500 if heavy else 2500, 9000) * np.exp(-t_(m) * (90 if heavy else 260))
    if heavy:
        out += 0.8 * np.sin(2 * np.pi * 95 * t) * np.exp(-t * 22)
    return pan(out * vol, -0.1)

def hum(dur, vol=0.05, f=50):
    n = int(dur * SR); t = t_(n)
    x = sum(np.sin(2 * np.pi * f * h * t) / h ** 1.2 for h in (1, 2, 3, 4, 6))
    x += 0.15 * bp(rng.standard_normal(n), 2000, 6000) * (0.5 + 0.5 * np.sin(2 * np.pi * 100 * t))
    return pan(x * vol * adsr(n, 0.4, 0.1, 1, 0.6), 0)

def sizzle(dur, vol=0.05):
    n = int(dur * SR)
    x = bp(rng.standard_normal(n), 3000, 9000) * (0.6 + 0.4 * lp(rng.standard_normal(n), 8) * 20).clip(0, 2)
    return pan(x * vol * adsr(n, 1.0, 0.1, 1, 1.0), 0.2)

def power_up(vol=0.18, f0=180, f1=1400, dur=0.7):
    n = int(dur * SR); t = t_(n) / dur
    f = f0 * (f1 / f0) ** t
    x = sine(f, n) * 0.7 + 0.3 * sine(f * 2.01, n)
    return pan(x * vol * np.sin(np.pi * t) ** 0.6, 0)

def beep(f=1760, vol=0.07, dur=0.07, p=0.4):
    n = int(dur * SR); t = t_(n)
    return pan(np.sin(2 * np.pi * f * t) * adsr(n, 0.004, 0.01, 0.8, 0.02) * vol, p)

def data_chirps(dur, vol=0.05):
    n = int(dur * SR); out = np.zeros((n, 2)); t = 0.0
    while t < dur - 0.1:
        f = rng.choice([2093, 2349, 2637, 3136, 3520])
        b = beep(f, vol * rng.uniform(0.5, 1.0), 0.035, rng.uniform(-0.6, 0.6)); o = int(t * SR)
        out[o:o + len(b)] += b[: n - o]; t += rng.uniform(0.04, 0.13)
    return out * adsr(n, 0.2, 0.1, 1, 0.3)[:, None]

def zap(vol=0.12, dur=0.35):
    n = int(dur * SR); t = t_(n)
    x = np.sign(np.sin(2 * np.pi * (60 + 40 * rng.random()) * t)) * (rng.random(n) > 0.92) * rng.standard_normal(n)
    return pan(bp(x, 1500, 9000) * np.exp(-t * 9) * vol, -0.3)

def scribble(dur, vol=0.05):
    n = int(dur * SR); t = t_(n)
    am = 0.5 + 0.5 * np.sin(2 * np.pi * 7 * t + 3 * np.sin(2 * np.pi * 1.3 * t))
    return pan(bp(rng.standard_normal(n), 2500, 7000) * am * vol * adsr(n, 0.05, 0.05, 1, 0.1), 0.2)

def clack(vol=0.16, p=0.0):                       # part dropped into place
    n = int(0.07 * SR); t = t_(n)
    x = bp(rng.standard_normal(n), 1200, 6000) * np.exp(-t * 120) + 0.5 * np.sin(2 * np.pi * 720 * t) * np.exp(-t * 90)
    return pan(x * vol, p)

def zip_(vol=0.06, dur=0.22, p=0.0):              # a track being routed
    n = int(dur * SR); t = t_(n) / dur
    x = bp(rng.standard_normal(n), 2500, 8000) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 70 * t * dur)))
    return pan(x * np.sin(np.pi * t) * vol, p)

def drill(dur=0.5, vol=0.16):                     # material removed
    n = int(dur * SR); t = t_(n)
    f = 180 + 60 * np.sin(2 * np.pi * 6 * t)
    x = 0.6 * saw(f, n) + 0.4 * bp(rng.standard_normal(n), 1500, 6000)
    return pan(lp(x, 3500) * adsr(n, 0.02, 0.05, 0.9, 0.12) * vol, 0.15)

def thud(vol=0.4):
    n = int(0.5 * SR); t = t_(n)
    f = 60 + 90 * np.exp(-t * 25)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 11) + 0.3 * lp(rng.standard_normal(n), 900) * np.exp(-t * 30)
    return pan(np.tanh(x * 1.3) * vol, 0)

def ratchet(n_clicks=6, vol=0.09):
    out = np.zeros((int((n_clicks * 0.045 + 0.1) * SR), 2))
    for k in range(n_clicks):
        c = ui_click(vol, 1800 + 100 * k, 0.3); o = int(k * 0.045 * SR); out[o:o + len(c)] += c
    return out

def reverb_ir(dur=2.2, decay=3.2):
    n = int(dur * SR); t = t_(n)
    ir = rng.standard_normal((n, 2)) * np.exp(-t * decay)[:, None]
    ir[:, 0] = lp(ir[:, 0], 6000); ir[:, 1] = lp(ir[:, 1], 6000)
    ir[: int(0.012 * SR)] = 0
    return ir / np.sqrt(np.sum(ir ** 2, 0))
