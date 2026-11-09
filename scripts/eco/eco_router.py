"""ECO router: strict sequential routing with rip-up-and-reroute, new vias allowed (cost-penalised),
power pins tied to the inner planes with a short stub + via. Reads geom_eco.json, writes eco_result.json."""
import json, math, ctypes, time, os, random
import numpy as np
from matplotlib.path import Path
import scipy.ndimage as ndi
from scipy.ndimage import binary_erosion

G = json.load(open("/home/claude/route/geom_eco.json"))
g = 0.02
xs = [p[0] for o in G["outline"] for p in o]; ys = [p[1] for o in G["outline"] for p in o]
X0, Y0 = math.floor(min(xs) / g) * g - g, math.floor(min(ys) / g) * g - g
Wd, Hd = int(round((max(xs) - X0) / g)) + 3, int(round((max(ys) - Y0) / g)) + 3
LI = {"F.Cu": 0, "B.Cu": 1}; cx = X0 + np.arange(Wd) * g; cy = Y0 + np.arange(Hd) * g
NET = dict(G["netcode"]); NET.update(G["pwrnet"])
W_TR, CLR = G["width"], G["ioclr"]
VIA_D, VIA_DRILL = 0.45, 0.25

def cells_in_poly(poly):
    poly = np.asarray(poly); x0, y0 = poly.min(0); x1, y1 = poly.max(0)
    i0, i1 = max(0, int(math.floor((x0 - X0) / g))), min(Wd - 1, int(math.ceil((x1 - X0) / g)))
    j0, j1 = max(0, int(math.floor((y0 - Y0) / g))), min(Hd - 1, int(math.ceil((y1 - Y0) / g)))
    if i1 < i0 or j1 < j0: return None
    II, JJ = np.meshgrid(np.arange(i0, i1 + 1), np.arange(j0, j1 + 1))
    m = Path(poly).contains_points(np.c_[X0 + II.ravel() * g, Y0 + JJ.ravel() * g])
    return JJ.ravel()[m], II.ravel()[m]
def cells_in_circle(x, y, r):
    i0, i1 = max(0, int((x - r - X0) / g) - 1), min(Wd - 1, int((x + r - X0) / g) + 1)
    j0, j1 = max(0, int((y - r - Y0) / g) - 1), min(Hd - 1, int((y + r - Y0) / g) + 1)
    II, JJ = np.meshgrid(np.arange(i0, i1 + 1), np.arange(j0, j1 + 1))
    m = (X0 + II * g - x) ** 2 + (Y0 + JJ * g - y) ** 2 <= r * r
    return JJ[m], II[m]

# ---------------- static obstacles (same as the IO router)
owner = np.zeros((2, Hd, Wd), np.int32); bynet = {}
for o in G["obst"]: bynet.setdefault(o["net"], []).append(o)
for net, obs in bynet.items():
    m = np.zeros((2, Hd, Wd), bool)
    for o in obs:
        l = LI[o["layer"]]
        if "circle" in o: m[l][cells_in_circle(*o["circle"])] = True
        else:
            for p in o["polys"]:
                r = cells_in_poly(p)
                if r is not None: m[l][r] = True
    tag = net if net > 0 else -1
    owner[m & (owner == 0)] = tag; owner[m & (owner != tag)] = -1
poly = np.asarray(G["outline"][0]); PX, PY = np.meshgrid(cx, cy)
inside = Path(poly).contains_points(np.c_[PX.ravel(), PY.ravel()]).reshape(Hd, Wd)
dmin = np.full((Hd, Wd), 1e9)
for a, b in zip(poly, np.roll(poly, -1, 0)):
    ab = b - a; L2 = max(ab @ ab, 1e-12); tt = np.clip(((PX - a[0]) * ab[0] + (PY - a[1]) * ab[1]) / L2, 0, 1)
    dmin = np.minimum(dmin, np.hypot(PX - (a[0] + tt * ab[0]), PY - (a[1] + tt * ab[1])))
edge_block = (~inside) | (dmin < G["edge"] + W_TR / 2)
via_edge_block = (~inside) | (dmin < 0.3 + VIA_D / 2)
for pz in G.get("novia", []):                                          # footprint keep-outs (no vias)
    m = Path(np.asarray(pz)).contains_points(np.c_[PX.ravel(), PY.ravel()]).reshape(Hd, Wd)
    rk = int(np.ceil((VIA_D / 2 + 0.02) / g)); yy, xx = np.mgrid[-rk:rk + 1, -rk:rk + 1]
    via_edge_block |= ndi.binary_dilation(m, structure=(xx * xx + yy * yy) <= rk * rk)
# ---------------- terminals
tasks = sorted(G["terms"]); groups = {}; padmask = {}
for name in tasks:
    cells = []
    for t in G["terms"][name]:
        s = set()
        for p in t["polys"]:
            r = cells_in_poly(p)
            if r is not None:
                for j, i in zip(*r):
                    if t["tht"]: s.add((0, j, i)); s.add((1, j, i))
                    else: s.add((LI[t["layer"]], j, i))
        cells.append((s, t))
    gr = []
    for s, t in cells:
        hit = [x for x in gr if x[0] & s]
        new = [set(s), [t]]
        for x in hit: new[0] |= x[0]; new[1] += x[1]; gr.remove(x)
        gr.append(new)
    groups[name] = gr
    pm = np.zeros((Hd, Wd), bool)
    for s, t in cells:
        if not t["tht"]:
            for p in t["polys"]:
                q = np.asarray(p); c0 = q.mean(0); big = c0 + (q - c0) * 1.0
                r = cells_in_circle(c0[0], c0[1], max(np.hypot(*(q - c0).T)) + 0.3)
                pm[r] = True
    padmask[name] = pm
owner[:, edge_block] = -1
for name in tasks:
    n = NET[name]
    for gr in groups[name]:
        for l, j, i in gr[0]:
            if edge_block[j, i]: owner[l, j, i] = n
print("grid", Wd, Hd, "tasks", len(tasks), flush=True)

# ---------------- A*
lib = ctypes.CDLL("/home/claude/route/astar_eco.so"); P = ctypes.c_void_p
lib.route.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, P, P, P, P, P, P, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float,
                      ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, P, ctypes.c_int, P, P, P, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
NS = 2 * Hd * Wd * 9
gbuf = np.empty(NS, np.float32); pbuf = np.empty(NS, np.int32); closed = np.empty(NS, np.uint8); outb = np.empty(3 * 300000, np.int32)
usage = np.zeros((2, Hd, Wd), np.int16); hist = np.zeros((2, Hd, Wd), np.float32)
def disk(r):
    k = int(math.ceil(r / g)); yy, xx = np.mgrid[-k:k + 1, -k:k + 1]; return k, (xx * xx + yy * yy) * g * g <= r * r
KT, DT = disk(W_TR + CLR)                         # track keep-out for others
KV, DV = disk(VIA_D / 2 + CLR + W_TR / 2 + float(os.environ.get("VM", 0)))  # via keep-out for others' tracks (+ margin)
EK, EV_ = disk(VIA_D / 2 - W_TR / 2 + float(os.environ.get("VM", 0)))       # erosion: track-free space -> via-free space (+ margin)
def stamp(m, l, j, i, k, D):
    j0, j1, i0, i1 = j - k, j + k + 1, i - k, i + k + 1
    dj0, di0 = max(0, -j0), max(0, -i0); dj1, di1 = D.shape[0] - max(0, j1 - Hd), D.shape[1] - max(0, i1 - Wd)
    m[l, max(0, j0):min(Hd, j1), max(0, i0):min(Wd, i1)] |= D[dj0:dj1, di0:di1]
def keepout(sol):
    m = np.zeros((2, Hd, Wd), bool)
    for path in sol["paths"]:
        for l, j, i in path: stamp(m, l, j, i, KT, DT)
    for j, i in sol["vias"]:
        stamp(m, 0, j, i, KV, DV); stamp(m, 1, j, i, KV, DV)
    return m
def viaok(n):
    free = np.ones((Hd, Wd), bool)
    for l in (0, 1): free &= ((owner[l] == 0) | (owner[l] == n)) & (usage[l] == 0)
    ok = binary_erosion(free, structure=EV_) & ~via_edge_block
    return ok
VIACOST = float(os.environ.get("VIACOST", 25))
def astar(n, src, tgt, vm, pres, window=None):
    ty, tx = np.nonzero(tgt.any(0)); sy, sx = np.nonzero(src.any(0))
    tx0, tx1, ty0, ty1 = tx.min(), tx.max(), ty.min(), ty.max()
    pad = int(4.0 / g)
    w = (max(0, min(sx.min(), tx0) - pad), max(0, min(sy.min(), ty0) - pad), min(Wd - 1, max(sx.max(), tx1) + pad), min(Hd - 1, max(sy.max(), ty1) + pad)) if window is None else window
    L = lib.route(Wd, Hd, n, owner.ctypes.data, usage.ctypes.data, hist.ctypes.data, src.ctypes.data, tgt.ctypes.data, vm.ctypes.data,
                  pres, 0.6, 2.5, VIACOST, int(tx0), int(ty0), int(tx1), int(ty1), outb.ctypes.data, 300000, gbuf.ctypes.data, pbuf.ctypes.data,
                  closed.ctypes.data, *map(int, w))
    if L < 0 and window is None: return astar(n, src, tgt, vm, pres, (0, 0, Wd - 1, Hd - 1))
    return None if L < 0 else [tuple(outb[3 * k:3 * k + 3]) for k in range(L)][::-1]
def route_task(name, pres):
    n = NET[name]; gr = groups[name]
    vm = viaok(n).astype(np.uint8) * 2
    for gg in gr:
        if any(t["tht"] for t in gg[1]):
            for l, j, i in gg[0]: vm[j, i] = 1
    vm[padmask[name] & (vm == 2)] = 0                # no via-in-pad for SMD pads
    sol = dict(paths=[], vias=[])
    if name.startswith("PWR:"):                      # pad -> short stub -> new via into the plane
        for gg in gr:
            src = np.zeros((2, Hd, Wd), np.uint8)
            for l, j, i in gg[0]: src[l, j, i] = 1
            tgt = np.zeros((2, Hd, Wd), np.uint8)
            ok = (vm == 2)
            jj, ii = np.nonzero(src.any(0)); cj, ci = int(jj.mean()), int(ii.mean())
            win = np.zeros((Hd, Wd), bool); r = int(2.5 / g); win[max(0, cj - r):cj + r, max(0, ci - r):ci + r] = True
            for l in (0, 1):
                if src[l].any(): tgt[l] = ok & win
            if not tgt.any(): return None
            p = astar(n, src, tgt, np.zeros((Hd, Wd), np.uint8), pres)
            if p is None: return None
            sol["paths"].append(p); sol["vias"].append((p[-1][1], p[-1][2]))
        return sol
    tree = np.zeros((2, Hd, Wd), np.uint8)
    for l, j, i in gr[0][0]: tree[l, j, i] = 1
    left = list(range(1, len(gr)))
    while left:
        tgt = np.zeros((2, Hd, Wd), np.uint8)
        for k in left:
            for l, j, i in gr[k][0]: tgt[l, j, i] = 1
        p = astar(n, tree, tgt, vm, pres)
        if p is None: return None
        for a, b in zip(p, p[1:]):
            if a[0] != b[0] and vm[a[1], a[2]] == 2: sol["vias"].append((a[1], a[2]))
        sol["paths"].append(p)
        end = p[-1]; k = next(k for k in left if end in gr[k][0]); left.remove(k)
        for l, j, i in gr[k][0]: tree[l, j, i] = 1
        for l, j, i in p: tree[l, j, i] = 1
    return sol

# ---------------- strict sequential + rip-up-and-reroute
sol, kos = {}, {}
def conflicts(name, s):
    others = usage - (kos[name].astype(np.int16) if name in kos else 0)
    bad = [(l, j, i) for path in s["paths"] for l, j, i in path if others[l, j, i] > 0]
    for j, i in s["vias"]:
        if others[0, j, i] > 0 or others[1, j, i] > 0: bad.append((0, j, i))
    return bad
def place(name, s): sol[name] = s; kos[name] = keepout(s); usage[kos[name]] += 1
def rip(name): usage[kos[name]] -= 1; del kos[name]; del sol[name]
def strict(name):
    s = route_task(name, 1e5)
    if s is not None and not conflicts(name, s): place(name, s); return True
    return False
prio = ["/FPGA Config/TCK", "/FPGA Config/TDO", "/FPGA Config/TDI", "/FPGA Config/TMS", "/PORT_H1", "/PORT_H0"]
order = prio + [t for t in tasks if t not in prio and not t.startswith("PWR:")] + [t for t in tasks if t.startswith("PWR:")]
if os.environ.get("CANDS"):
    import sys
    n = NET["/I2C_SDA"]; base = groups["/I2C_SDA"]; base_owner = owner.copy()
    keep = [x for x in base if not any(t["ref"] == "U1" for t in x[1])]
    print("groups", [[t["ref"] for t in x[1]] for x in base], flush=True)
    groups["/I2C_SDA"] = keep; s = route_task("/I2C_SDA", 1e5); print("J6<->R31 only:", None if s is None else len(s["vias"]), flush=True)
    if os.environ.get("DUMP"):
        from PIL import Image
        vm = viaok(n)
        img = np.zeros((Hd, Wd, 3), np.uint8)
        f0 = (owner[0] == 0) | (owner[0] == n); f1 = (owner[1] == 0) | (owner[1] == n)
        img[..., 0] = f0 * 200; img[..., 2] = f1 * 200; img[..., 1] = vm * 255
        for x in base:
            for l, j, i in x[0]: img[j, i] = (255, 255, 255)
        Image.fromarray(img).save("/home/claude/route/passmap.png"); print("dumped", X0, Y0, g, flush=True); sys.exit()
    jj6 = [x for x in keep if any(t["ref"] == "J6" for t in x[1])]
    for line in open(os.environ["CANDS"]):
        ball, x, y = line.split(); x, y = float(x), float(y)
        owner[:] = base_owner
        jj, ii = cells_in_circle(x, y, 0.16 + 0.127 + W_TR / 2 + 0.005)
        sel = owner[0, jj, ii] != 0; owner[0, jj[sel], ii[sel]] = n
        bj, bi = cells_in_circle(x, y, 0.15)
        groups["/I2C_SDA"] = [[{(0, j, i) for j, i in zip(bj, bi)}, [dict(ref="U1", tht=False)]]] + jj6
        s = route_task("/I2C_SDA", 1e5)
        print("CAND", ball, x, y, None if s is None else (sum(len(p) for p in s["paths"]), len(s["vias"])), flush=True)
    sys.exit()
if os.environ.get("SOLO"):
    import sys
    for t in prio + ["/LEDs/CAT_R"]:
        s = route_task(t, 1e5); print("SOLO", t, None if s is None else (sum(len(p) for p in s["paths"]), len(s["vias"])), flush=True)
    sys.exit()
queue = [t for t in order if not strict(t)]
print("first pass: placed", len(sol), "of", len(tasks), "queue", queue, flush=True)
random.seed(3); tries = {}; step = 0
while queue and step < int(os.environ.get("STEPS", 500)):
    step += 1; name = queue.pop(0); tries[name] = tries.get(name, 0) + 1
    if strict(name): continue
    q = route_task(name, 3.0)
    victims = []
    if q:
        bad = conflicts(name, q); cnt = {}
        for l, j, i in bad:
            for k, m in kos.items():
                if m[l, j, i]: cnt[k] = cnt.get(k, 0) + 1
        victims = sorted(cnt, key=lambda k: -cnt[k])[:1 + (tries[name] > 3)]
    for v in victims: rip(v); queue.append(v)
    if not strict(name): queue.append(name)
    if tries[name] > 8: random.shuffle(queue)
print("done after", step, "steps: placed", len(sol), "unplaced", queue, flush=True)
# ---------------- output
segs, vias = [], []
inv = {v: k for k, v in NET.items()}
for name, s in sol.items():
    netname = name if not name.startswith("PWR:") else G["terms"][name][0]["netname"]
    for path in s["paths"]:
        run = [path[0]]
        def flush(run):
            if len(run) < 2: return
            pts = [run[0]]
            for a, b, c in zip(run, run[1:], run[2:]):
                if (b[1] - a[1], b[2] - a[2]) != (c[1] - b[1], c[2] - b[2]): pts.append(b)
            pts.append(run[-1])
            for a, b in zip(pts, pts[1:]):
                segs.append(dict(net=netname, layer=["F.Cu", "B.Cu"][a[0]], x1=X0 + a[2] * g, y1=Y0 + a[1] * g, x2=X0 + b[2] * g, y2=Y0 + b[1] * g))
        for c in path[1:]:
            if c[0] != run[-1][0]: flush(run); run = [c]
            else: run.append(c)
        flush(run)
    for j, i in s["vias"]: vias.append(dict(net=netname, x=X0 + i * g, y=Y0 + j * g))
# split at T-junctions (same net, same layer)
from collections import defaultdict
byk = defaultdict(list)
for s in segs: byk[(s["net"], s["layer"])].append(s)
out = []
for (net, layer), ss in byk.items():
    ends = {(round(s["x1"], 4), round(s["y1"], 4)) for s in ss} | {(round(s["x2"], 4), round(s["y2"], 4)) for s in ss}
    for s in ss:
        n = int(round(max(abs(s["x2"] - s["x1"]), abs(s["y2"] - s["y1"])) / g)); pts = [0]
        for k in range(1, n):
            p = (round(s["x1"] + (s["x2"] - s["x1"]) * k / n, 4), round(s["y1"] + (s["y2"] - s["y1"]) * k / n, 4))
            if p in ends: pts.append(k)
        pts.append(n)
        for a, b in zip(pts, pts[1:]):
            out.append(dict(net=net, layer=layer, x1=s["x1"] + (s["x2"] - s["x1"]) * a / max(n, 1), y1=s["y1"] + (s["y2"] - s["y1"]) * a / max(n, 1),
                            x2=s["x1"] + (s["x2"] - s["x1"]) * b / max(n, 1), y2=s["y1"] + (s["y2"] - s["y1"]) * b / max(n, 1)))
json.dump(dict(segs=out, vias=vias, unplaced=queue, sol={k: dict(paths=[[list(map(int, c)) for c in p] for p in v["paths"]], vias=[list(map(int, x)) for x in v["vias"]]) for k, v in sol.items()},
               grid=dict(X0=X0, Y0=Y0, g=g)), open("/home/claude/route/eco_result.json", "w"))
print("segments", len(out), "new vias", len(vias))
