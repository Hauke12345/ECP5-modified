// Two-layer octilinear A* for negotiated-congestion routing.
// State = (layer, y, x, dir). Moves: 8 directions in-layer; layer change only on via cells of the net.
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <stdint.h>

typedef struct { float f; int32_t s; } node;
static node *heap; static int hn, hcap;
static void hpush(float f, int32_t s) {
    if (hn >= hcap) { hcap = hcap ? hcap * 2 : 1 << 20; heap = realloc(heap, sizeof(node) * hcap); }
    int i = hn++; while (i > 0) { int p = (i - 1) / 2; if (heap[p].f <= f) break; heap[i] = heap[p]; i = p; }
    heap[i].f = f; heap[i].s = s;
}
static node hpop(void) {
    node top = heap[0], last = heap[--hn]; int i = 0;
    for (;;) { int c = 2 * i + 1; if (c >= hn) break; if (c + 1 < hn && heap[c + 1].f < heap[c].f) c++; if (heap[c].f >= last.f) break; heap[i] = heap[c]; i = c; }
    heap[i] = last; return top;
}
static const int DX[8] = {1, 1, 0, -1, -1, -1, 0, 1}, DY[8] = {0, 1, 1, 1, 0, -1, -1, -1};

/* owner: [2][H][W] int32 (0 free, n = only net n, -1 blocked)
   usage: [2][H][W] int16 other nets' keep-out coverage, hist: [2][H][W] float
   src/tgt: [2][H][W] uint8, via: [H][W] uint8 (layer change allowed)
   out: path as (layer,y,x) triples, returns length (or -1)   */
int route(int W, int H, int net, const int32_t *owner, const int16_t *usage, const float *hist,
          const uint8_t *src, const uint8_t *tgt, const uint8_t *via, float pres, float turn45, float turn90, float viacost,
          int tx0, int ty0, int tx1, int ty1, int32_t *out, int maxout, float *gbuf, int32_t *pbuf, uint8_t *closed,
          int wx0, int wy0, int wx1, int wy1) {
    int WW = wx1 - wx0 + 1, WH = wy1 - wy0 + 1;
    long N = 2L * WH * WW * 9;
    for (long i = 0; i < N; i++) { gbuf[i] = 1e30f; }
    memset(closed, 0, N);
    hn = 0;
    #define IDX(l, y, x, d) ((((long)(l) * WH + ((y) - wy0)) * WW + ((x) - wx0)) * 9 + (d))
    #define CELL(l, y, x) (((long)(l) * H + (y)) * W + (x))
    for (int l = 0; l < 2; l++) for (int y = wy0; y <= wy1; y++) for (int x = wx0; x <= wx1; x++)
        if (src[CELL(l, y, x)]) { long s = IDX(l, y, x, 8); gbuf[s] = 0; pbuf[s] = -1; hpush(0, (int32_t)s); }
    while (hn) {
        node nd = hpop(); long s = nd.s; if (closed[s]) continue; closed[s] = 1;
        int d = s % 9; long c = s / 9; int x = c % WW + wx0; int y = (c / WW) % WH + wy0; int l = c / ((long)WW * WH);
        if (tgt[CELL(l, y, x)]) {                      // reconstruct
            int n = 0; long k = s;
            while (k >= 0 && n < maxout) { long cc = k / 9; out[3 * n] = cc / ((long)WW * WH); out[3 * n + 1] = (cc / WW) % WH + wy0; out[3 * n + 2] = cc % WW + wx0; n++; k = pbuf[k]; }
            return n;
        }
        float g = gbuf[s];
        for (int nd2 = 0; nd2 < 8; nd2++) {
            int nx = x + DX[nd2], ny = y + DY[nd2];
            if (nx < wx0 || ny < wy0 || nx > wx1 || ny > wy1) continue;
            long cc = CELL(l, ny, nx); int32_t o = owner[cc];
            if (o != 0 && o != net) continue;
            if (nd2 & 1) {                              // diagonal: both orthogonal neighbours must be usable (no corner cutting)
                int32_t a = owner[CELL(l, y, nx)], b = owner[CELL(l, ny, x)];
                if ((a != 0 && a != net) || (b != 0 && b != net)) continue;
            }
            float step = (nd2 & 1) ? 1.41421356f : 1.0f;
            float cost = step * (1.0f + hist[cc] + pres * usage[cc]);
            if (d != 8 && d != nd2) { int t = abs(d - nd2); if (t > 4) t = 8 - t; cost += (t == 1) ? turn45 : (t == 2 ? turn90 : 1e6f); }
            long ns = IDX(l, ny, nx, nd2); float ng = g + cost;
            if (ng < gbuf[ns]) {
                gbuf[ns] = ng; pbuf[ns] = s;
                int hx = nx < tx0 ? tx0 - nx : (nx > tx1 ? nx - tx1 : 0), hy = ny < ty0 ? ty0 - ny : (ny > ty1 ? ny - ty1 : 0);
                float h = (hx > hy) ? (hx - hy) + 1.41421356f * hy : (hy - hx) + 1.41421356f * hx;
                hpush(ng + h, (int32_t)ns);
            }
        }
        if (via[(long)y * W + x]) {                    // layer change through an existing via / THT pad of this net
            int nl = 1 - l; long cc = CELL(nl, y, x); int32_t o = owner[cc];
            if (o == 0 || o == net) {
                long ns = IDX(nl, y, x, 8); float ng = g + (via[(long)y * W + x] == 1 ? 2.0f : viacost);
                if (ng < gbuf[ns]) { gbuf[ns] = ng; pbuf[ns] = s; hpush(ng, (int32_t)ns); }
            }
        }
    }
    return -1;
}
