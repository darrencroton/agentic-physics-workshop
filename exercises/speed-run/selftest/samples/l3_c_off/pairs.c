/* Cell-list pair counter in C, called from fast.py through ctypes.
 *
 * Same contract as paircount/reference.py: unique pairs i < j,
 * r = sqrt(dx*dx + dy*dy + dz*dz) in double, half-open bins
 * edges[k] <= r < edges[k+1]. Build with -ffp-contract=off so the compiler
 * does not fuse the multiply-adds into FMA (that changes a few counts).
 *
 * The box is cut into cells of side >= edges[nbins], so every pair that can
 * be counted lies in the same or a neighbouring cell. Each cell is compared
 * with itself and with its 13 "forward" neighbours, so each pair is seen once.
 */
#include <math.h>
#include <stdlib.h>

static inline int bin_of(double r, const double *edges, int nbins)
{
    if (r < edges[0] || r >= edges[nbins]) return -1;
    int lo = 0, hi = nbins;
    while (hi - lo > 1) {
        int mid = (lo + hi) / 2;
        if (r >= edges[mid]) lo = mid; else hi = mid;
    }
    return lo;
}

static void count_block(const double *p, long long a0, long long a1,
                        long long b0, long long b1, int same,
                        const double *edges, int nbins, long long *out)
{
    for (long long i = a0; i < a1; i++) {
        const double xi = p[3 * i], yi = p[3 * i + 1], zi = p[3 * i + 2];
        for (long long j = same ? i + 1 : b0; j < b1; j++) {
            double dx = xi - p[3 * j];
            double dy = yi - p[3 * j + 1];
            double dz = zi - p[3 * j + 2];
            int k = bin_of(sqrt(dx * dx + dy * dy + dz * dz), edges, nbins);
            if (k >= 0) out[k]++;
        }
    }
}

void count(const double *pos, long long n, const double *edges, int nbins,
           long long *out)
{
    for (int k = 0; k < nbins; k++) out[k] = 0;
    if (n < 2) return;

    double lo[3], hi[3];
    for (int d = 0; d < 3; d++) lo[d] = hi[d] = pos[d];
    for (long long i = 0; i < n; i++)
        for (int d = 0; d < 3; d++) {
            if (pos[3 * i + d] < lo[d]) lo[d] = pos[3 * i + d];
            if (pos[3 * i + d] > hi[d]) hi[d] = pos[3 * i + d];
        }
    double span = 0.0;
    for (int d = 0; d < 3; d++)
        if (hi[d] - lo[d] > span) span = hi[d] - lo[d];

    double rmax = edges[nbins] * (1.0 + 1e-9);
    long long nc = (long long)(span / rmax);
    if (nc < 1) nc = 1;
    if (nc > 128) nc = 128;
    double side = span / (double)nc;
    if (side < rmax) side = rmax;
    long long ncell = nc * nc * nc;

    long long *cell = malloc(sizeof(long long) * n);
    long long *start = calloc(ncell + 1, sizeof(long long));
    double *p = malloc(sizeof(double) * 3 * n);
    if (!cell || !start || !p) { free(cell); free(start); free(p); out[0] = -1; return; }

    for (long long i = 0; i < n; i++) {
        long long c[3];
        for (int d = 0; d < 3; d++) {
            c[d] = (long long)((pos[3 * i + d] - lo[d]) / side);
            if (c[d] >= nc) c[d] = nc - 1;
        }
        cell[i] = (c[0] * nc + c[1]) * nc + c[2];
        start[cell[i] + 1]++;
    }
    for (long long c = 0; c < ncell; c++) start[c + 1] += start[c];
    long long *fill = malloc(sizeof(long long) * ncell);
    if (!fill) { free(cell); free(start); free(p); out[0] = -1; return; }
    for (long long c = 0; c < ncell; c++) fill[c] = start[c];
    for (long long i = 0; i < n; i++) {
        long long dst = fill[cell[i]]++;
        p[3 * dst] = pos[3 * i];
        p[3 * dst + 1] = pos[3 * i + 1];
        p[3 * dst + 2] = pos[3 * i + 2];
    }
    free(fill);
    free(cell);

    for (long long ix = 0; ix < nc; ix++)
    for (long long iy = 0; iy < nc; iy++)
    for (long long iz = 0; iz < nc; iz++) {
        long long c = (ix * nc + iy) * nc + iz;
        if (start[c] == start[c + 1]) continue;
        count_block(p, start[c], start[c + 1], 0, start[c + 1], 1, edges, nbins, out);
        for (int ox = 0; ox <= 1; ox++)
        for (int oy = -1; oy <= 1; oy++)
        for (int oz = -1; oz <= 1; oz++) {
            if (ox == 0 && (oy < 0 || (oy == 0 && oz <= 0))) continue;
            long long jx = ix + ox, jy = iy + oy, jz = iz + oz;
            if (jx >= nc || jy < 0 || jy >= nc || jz < 0 || jz >= nc) continue;
            long long b = (jx * nc + jy) * nc + jz;
            count_block(p, start[c], start[c + 1], start[b], start[b + 1], 0,
                        edges, nbins, out);
        }
    }
    free(start);
    free(p);
}
