"""
STRUX Transport Diagnosis V1

PURPOSE:
Classify transport behavior in geometry-constrained systems.

This module separates:
- completion: do rays reach the target?
- coherence: do rays maintain directional organization?
- branching: how many transport channels cross a diagnostic gate?

VALIDATED SYNTHETIC CLASSES:
- SINGLE COHERENT CHANNEL
- MULTI-CHANNEL / BRAIDED
- TRAPPED / INCOMPLETE

WORKING OBSERVABLE:
Gate mode count / output branching.

DOES NOT MEASURE:
- universal transport topology
- physical flux
- energy transport
- full TDA persistence

STATUS:
Experimental, validated on synthetic benchmark STRUX_SINGLE_TRAPPED_TEST_05.
Not yet validated on real-world systems.
"""

import numpy as np
from scipy.signal import find_peaks


def count_gate_modes(
    gate_values,
    height=180,
    sigma=2.5,
    peak_height_ratio=0.25,
    min_peak_distance=8,
):
    """
    Count coherent transport modes crossing a diagnostic gate.

    Parameters
    ----------
    gate_values:
        1D array of gate crossing coordinates.
    height:
        Size of the gate axis.
    sigma:
        Gaussian smoothing scale.
    peak_height_ratio:
        Minimum peak height relative to maximum density.
    min_peak_distance:
        Minimum distance between detected peaks.

    Returns
    -------
    dict with:
        n_modes
        hist_axis
        hist_density
        peaks
    """

    gate_values = np.asarray(gate_values, dtype=float)
    gate_values = gate_values[np.isfinite(gate_values)]

    if len(gate_values) < 5:
        return {
            "n_modes": 0,
            "hist_axis": None,
            "hist_density": None,
            "peaks": [],
            "reason": "insufficient_samples",
        }

    bins = np.arange(0, height + 1, 1)
    hist, edges = np.histogram(gate_values, bins=bins)
    hist = hist.astype(float)

    radius = int(3 * sigma)
    xs = np.arange(-radius, radius + 1)

    kernel = np.exp(-(xs**2) / (2 * sigma * sigma))
    kernel /= kernel.sum()

    smooth = np.convolve(hist, kernel, mode="same")

    max_density = smooth.max()

    if max_density <= 0:
        return {
            "n_modes": 0,
            "hist_axis": edges[:-1],
            "hist_density": smooth,
            "peaks": [],
            "reason": "empty_density",
        }

    peaks, _ = find_peaks(
        smooth,
        height=max_density * peak_height_ratio,
        distance=min_peak_distance,
    )

    return {
        "n_modes": int(len(peaks)),
        "hist_axis": edges[:-1],
        "hist_density": smooth,
        "peaks": peaks,
        "reason": "ok",
    }


def classify_transport(success_rate, n_modes, success_threshold=0.1):
    """
    Classify transport behavior from completion and gate modes.
    """

    if success_rate < success_threshold:
        return "TRAPPED / INCOMPLETE"

    if n_modes <= 1:
        return "SINGLE COHERENT CHANNEL"

    return "MULTI-CHANNEL / BRAIDED"


def diagnose_transport(
    success_rate,
    direction_coherence,
    gate_values,
    height=180,
):
    """
    Complete transport diagnosis helper.

    Returns a compact diagnostic dictionary.
    """

    mode_info = count_gate_modes(
        gate_values=gate_values,
        height=height,
    )

    transport_class = classify_transport(
        success_rate=success_rate,
        n_modes=mode_info["n_modes"],
    )

    return {
        "success_rate": float(success_rate),
        "direction_coherence": float(direction_coherence),
        "n_modes": mode_info["n_modes"],
        "transport_class": transport_class,
        "mode_info": mode_info,
    }