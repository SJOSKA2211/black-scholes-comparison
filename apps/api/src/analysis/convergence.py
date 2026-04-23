"""Convergence analysis logic for numerical experiments."""

from __future__ import annotations

from typing import Any

import numpy as np


def analyze_convergence_order(results: list[dict[str, Any]]) -> dict[str, float]:
    """
    Estimates the empirical convergence order from a series of runs.
    Calculates the slope of log(error) vs log(1/resolution).
    """
    if len(results) < 2:
        return {"convergence_order": 0.0}

    # Extract resolution and error
    # results should have 'parameter_set' with 'num_steps' or 'num_paths'
    # and 'error' (abs diff from analytical)
    resolutions = []
    errors = []

    for result in results:
        param_set = result.get("parameter_set", {})
        # Try to get resolution
        resolution = (
            param_set.get("num_steps")
            or param_set.get("num_paths")
            or param_set.get("num_replications")
            or result.get("num_steps")
        )

        # If no resolution, try to get delta_t and use 1/delta_t
        if not resolution:
            delta_t = (
                param_set.get("dt")
                or param_set.get("time_step")
                or result.get("dt")
                or result.get("time_step")
            )
            if delta_t and delta_t > 0:
                resolution = 1.0 / delta_t

        error_val = result.get("error")

        if resolution and error_val and error_val > 0:
            resolutions.append(resolution)
            errors.append(error_val)

    if len(resolutions) < 2:
        return {"convergence_order": 0.0}

    # log-log regression
    log_resolution = np.log(resolutions)
    log_error = np.log(errors)

    # slope of log(error) vs log(resolution)
    # error ~ C * resolution^(-order)  => log(error) ~ log(C) - order * log(resolution)
    # slope = -order
    slope, _ = np.polyfit(log_resolution, log_error, 1)

    return {"convergence_order": float(-slope)}
