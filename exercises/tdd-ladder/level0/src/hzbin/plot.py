"""Plot the H(z) data and its binned weighted means."""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from hzbin.binning import binned_weighted_mean  # noqa: E402
from hzbin.data import load_hz  # noqa: E402

DEFAULT_EDGES = [0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0]
H0_FID, OM_FID = 70.0, 0.3


def fiducial(z, h0=H0_FID, om=OM_FID):
    """Flat LCDM Hubble rate H(z) in km/s/Mpc."""
    return h0 * np.sqrt(om * (1.0 + z) ** 3 + 1.0 - om)


def workshop_level(state_path=".workshop/state.json"):
    """Level from the workshop state file, or 0 if it cannot be read."""
    try:
        with open(state_path, encoding="utf-8") as fh:
            return int(json.load(fh)["level"])
    except (OSError, ValueError, KeyError, TypeError):
        return 0


def main(data_path="data/hz_mock.csv", out_path="results/hz_binned.png"):
    """Write the H(z) plot, plus a copy named for the current level."""
    z, h, sigma = load_hz(data_path)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.errorbar(z, h, yerr=sigma, fmt="o", ms=3, color="0.55",
                ecolor="0.75", label="data")
    zz = np.linspace(0.0, 2.0, 200)
    ax.plot(zz, fiducial(zz), "k--", lw=1,
            label=r"fiducial ($H_0=70$, $\Omega_m=0.3$)")
    try:
        res = binned_weighted_mean(z, h, sigma, DEFAULT_EDGES)
    except NotImplementedError:
        print("Note: binned_weighted_mean is not implemented yet, "
              "so only the data and fiducial curve are plotted.")
    else:
        ax.errorbar(res.x_eff, res.mean, yerr=res.err, fmt="s", ms=5,
                    color="C3", capsize=3, label="binned weighted mean")
    ax.set_xlabel("redshift z")
    ax.set_ylabel("H(z) [km/s/Mpc]")
    ax.legend(loc="upper left")
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150, bbox_inches="tight")
    print(f"Wrote {out}")
    backup = out.with_name(f"{out.stem}_L{workshop_level()}{out.suffix}")
    try:
        fig.savefig(backup, dpi=150, bbox_inches="tight")
        print(f"Wrote {backup} (kept for comparing levels)")
    except OSError as exc:
        print(f"Note: could not write {backup}: {exc}")
    plt.close(fig)


if __name__ == "__main__":
    main()
