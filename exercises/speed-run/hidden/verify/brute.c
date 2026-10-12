/* Independent brute-force pair counter (same ABI as the level 3 solution).
 *
 * count(): every unique pair i < j, r = sqrt(dx*dx + dy*dy + dz*dz) in double,
 * half-open bins edges[k] <= r < edges[k+1]. Compile with -ffp-contract=off to
 * match the Python reference; the default build lets clang fuse into FMA.
 *
 * pair_bins(): bin index of a[m] - b[m] with the same arithmetic as count();
 * -1 below edges[0], nbins at or above edges[nbins]. Used to find FMA straddlers.
 */
#include <math.h>

static inline double separation(const double *p, const double *q)
{
    double dx = p[0] - q[0];
    double dy = p[1] - q[1];
    double dz = p[2] - q[2];
    return sqrt(dx * dx + dy * dy + dz * dz);
}

static inline int bin_of(double r, const double *edges, int nbins)
{
    if (r < edges[0]) return -1;
    if (r >= edges[nbins]) return nbins;
    int lo = 0, hi = nbins;
    while (hi - lo > 1) {
        int mid = (lo + hi) / 2;
        if (r >= edges[mid]) lo = mid; else hi = mid;
    }
    return lo;
}

void count(const double *pos, long long n, const double *edges, int nbins,
           long long *out)
{
    for (int k = 0; k < nbins; k++) out[k] = 0;
    for (long long i = 0; i < n; i++) {
        for (long long j = i + 1; j < n; j++) {
            int k = bin_of(separation(pos + 3 * i, pos + 3 * j), edges, nbins);
            if (k >= 0 && k < nbins) out[k]++;
        }
    }
}

void pair_bins(const double *a, const double *b, long long m,
               const double *edges, int nbins, int *out)
{
    for (long long i = 0; i < m; i++)
        out[i] = bin_of(separation(a + 3 * i, b + 3 * i), edges, nbins);
}
