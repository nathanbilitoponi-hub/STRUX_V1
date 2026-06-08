"""
STRUX AWDTM Synthetic Weight Diagnostic 01

Purpose
-------
Build a controlled synthetic void-like point cloud with known ground truth and
visualize the validated STRUX AWDTM V5 weight component:

    W_V5 = rho_hat^2 * omni_inv^4

Scope
-----
This is a synthetic diagnostic only. It makes no claims about real cosmology,
universal geometry, porous materials, or real-world datasets.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.ndimage import gaussian_filter
from scipy.spatial import cKDTree
from skimage import measure


HERE = Path(__file__).resolve().parent
RESULTS_DIR = HERE / "results"


def make_void_like_cloud(seed=7, contamination=0.30, n_shell=1400):
    """Create a 2D annular point cloud plus uniform contaminating points."""
    rng = np.random.default_rng(seed)

    theta = rng.uniform(0.0, 2.0 * np.pi, n_shell)
    radius = rng.normal(loc=1.0, scale=0.045, size=n_shell)
    shell = np.column_stack((radius * np.cos(theta), radius * np.sin(theta)))

    n_noise = int(round(n_shell * contamination / max(1.0 - contamination, 1e-9)))
    noise = rng.uniform(low=-1.35, high=1.35, size=(n_noise, 2))

    points = np.vstack((shell, noise))
    labels = np.concatenate((np.ones(n_shell, dtype=int), np.zeros(n_noise, dtype=int)))
    return points, labels


def local_density_hat(points, k=40):
    """Estimate normalized local density from k-nearest-neighbor radius."""
    tree = cKDTree(points)
    distances, _ = tree.query(points, k=min(k + 1, len(points)))
    kth = distances[:, -1]
    density = 1.0 / (kth * kth + 1e-9)
    lo, hi = np.percentile(density, [5, 95])
    return np.clip((density - lo) / (hi - lo + 1e-9), 0.0, 1.0)


def omni_inverse(points):
    """Estimate inverse omni-directional spread from radial consistency."""
    radius = np.linalg.norm(points, axis=1)
    target = np.median(radius)
    residual = np.abs(radius - target)
    scale = np.percentile(residual, 90) + 1e-9
    return np.clip(1.0 - residual / scale, 0.0, 1.0)


def awdtm_v5_weights(points):
    """Compute the validated synthetic STRUX AWDTM V5 weights."""
    rho_hat = local_density_hat(points)
    omni_inv = omni_inverse(points)
    return rho_hat * rho_hat * np.power(omni_inv, 4), rho_hat, omni_inv


def render_weight_field(points, weights, out_path):
    """Render a diagnostic weight field and save it as a PNG."""
    grid_size = 220
    extent = (-1.45, 1.45, -1.45, 1.45)

    hist, xedges, yedges = np.histogram2d(
        points[:, 0],
        points[:, 1],
        bins=grid_size,
        range=[[extent[0], extent[1]], [extent[2], extent[3]]],
        weights=weights,
    )
    counts, _, _ = np.histogram2d(
        points[:, 0],
        points[:, 1],
        bins=grid_size,
        range=[[extent[0], extent[1]], [extent[2], extent[3]]],
    )

    field = hist / (counts + 1e-9)
    field = gaussian_filter(field, sigma=1.4)
    mask = field > np.percentile(field[field > 0], 70)
    components = measure.label(mask)

    plt.figure(figsize=(7, 6))
    plt.imshow(
        field.T,
        origin="lower",
        extent=extent,
        cmap="magma",
        interpolation="nearest",
    )
    plt.contour(
        components.T > 0,
        levels=[0.5],
        colors="cyan",
        linewidths=0.8,
        extent=extent,
    )
    plt.scatter(points[:, 0], points[:, 1], s=2, c="white", alpha=0.12)
    plt.title("STRUX AWDTM V5 Synthetic Weight Diagnostic")
    plt.xlabel("x")
    plt.ylabel("y")
    plt.tight_layout()
    plt.savefig(out_path, dpi=180)
    plt.close()


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    points, labels = make_void_like_cloud(seed=7, contamination=0.30)
    weights, rho_hat, omni_inv = awdtm_v5_weights(points)

    df = pd.DataFrame(
        {
            "x": points[:, 0],
            "y": points[:, 1],
            "ground_truth_shell": labels,
            "rho_hat": rho_hat,
            "omni_inv": omni_inv,
            "w_v5": weights,
        }
    )

    csv_path = RESULTS_DIR / "strux_weight_diagnostic_01.csv"
    png_path = RESULTS_DIR / "strux_weight_diagnostic_01.png"

    df.to_csv(csv_path, index=False)
    render_weight_field(points, weights, png_path)

    print("Saved:")
    print(csv_path)
    print(png_path)


if __name__ == "__main__":
    main()
