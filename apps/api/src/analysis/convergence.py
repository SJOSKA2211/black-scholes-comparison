from typing import Any, Dict, List

import numpy as np
import structlog
from scipy import stats

logger = structlog.get_logger(__name__)


class ConvergenceAnalyzer:
    """
    Analyzes numerical method convergence using log-log regression.
    """

    def estimate_convergence_order(
        self, experiment_results: List[Dict[str, Any]]
    ) -> tuple:
        """
        Estimates the order of convergence 'p' using log-log OLS regression.
        Expects a list of results where 'parameter_set' contains the discretization step.
        """
        try:
            steps = []
            errors = []

            for res in experiment_results:
                params = res.get("parameter_set", {})
                # Extract discretization step based on method family
                # For FDM: dt or num_time
                # For Trees: n or num_steps
                # For MC: num_paths (Step = 1/sqrt(N))

                step = None
                if "num_steps" in params:
                    step = 1.0 / params["num_steps"]
                elif "num_paths" in params:
                    step = 1.0 / np.sqrt(params["num_paths"])
                elif "num_time" in params:
                    step = 1.0 / params["num_time"]

                # Error against analytical if available, else market mid
                error = res.get("absolute_error")

                if step and error and error > 0:
                    steps.append(step)
                    errors.append(error)

            steps = np.array(steps)
            errors = np.array(errors)

            mask = (steps > 0) & (errors > 0)
            x = np.log(steps[mask])
            y = np.log(errors[mask])

            if len(x) < 2:
                return 0.0, {"error": "Insufficient data for regression"}

            slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

            regression_data = {
                "r_squared": float(r_value**2),
                "intercept": float(intercept),
                "std_err": float(std_err),
                "points": [
                    {"step": float(s), "error": float(e)} for s, e in zip(steps, errors)
                ],
            }

            return float(slope), regression_data

        except Exception as e:
            logger.error("convergence_analysis_failed", error=str(e))
            return 0.0, {"error": str(e)}
