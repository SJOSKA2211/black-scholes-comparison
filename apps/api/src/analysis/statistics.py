import time
from typing import Any, Dict, List

import pandas as pd
import structlog
from scipy import stats
from statsmodels.stats.multicomp import pairwise_tukeyhsd

logger = structlog.get_logger(__name__)


class Statistics:
    """
    Handles ANOVA and Tukey HSD statistical analysis for pricing methods.
    Includes an internal cache to satisfy the 5-minute TTL requirement.
    """

    _instance = None
    _cache = {}
    CACHE_TTL = 300  # 5 minutes

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Statistics, cls).__new__(cls)
        return cls._instance

    def get_full_analysis(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Returns cached analysis results if available, otherwise computes them.
        """
        now = time.time()
        # Simple cache key based on data length and latest entry timestamp if available
        cache_key = f"analysis_{len(data)}"

        if cache_key in self._cache:
            timestamp, results = self._cache[cache_key]
            if now - timestamp < self.CACHE_TTL:
                return results

        # Compute new results
        results = {
            "anova": self.perform_anova(data),
            "tukey": self.perform_tukey_hsd(data),
            "summary": self.compute_summary_stats(data),
        }

        self._cache[cache_key] = (now, results)
        return results

    def perform_anova(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Performs one-way ANOVA to test if method means are significantly different.
        """
        try:
            df = pd.DataFrame(data)
            if df.empty or "method_type" not in df or "computed_price" not in df:
                return {"error": "Invalid data format"}

            groups = [
                group["computed_price"].values
                for name, group in df.groupby("method_type")
            ]
            if len(groups) < 2:
                return {"error": "Insufficient groups for ANOVA"}

            f_stat, p_val = stats.f_oneway(*groups)
            return {
                "f_statistic": float(f_stat),
                "p_value": float(p_val),
                "significant": bool(p_val < 0.05),
            }
        except Exception as e:
            logger.error("anova_failed", error=str(e))
            return {"error": str(e)}

    def perform_tukey_hsd(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Performs Tukey Honestly Significant Difference (HSD) test for pairwise comparisons.
        """
        try:
            df = pd.DataFrame(data)
            if df.empty or df["method_type"].nunique() < 2:
                return [{"error": "Insufficient methods for Tukey HSD"}]

            tukey = pairwise_tukeyhsd(
                endog=df["computed_price"], groups=df["method_type"], alpha=0.05
            )

            summary_df = pd.DataFrame(
                data=tukey.summary().data[1:], columns=tukey.summary().data[0]
            )
            return summary_df.to_dict(orient="records")

        except Exception as e:
            logger.error("tukey_hsd_failed", error=str(e))
            return [{"error": str(e)}]

    def compute_summary_stats(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Computes mean, std, and count per method."""
        try:
            df = pd.DataFrame(data)
            if df.empty:
                return {}
            summary = (
                df.groupby("method_type")["computed_price"]
                .agg(["mean", "std", "count"])
                .to_dict(orient="index")
            )
            return summary
        except Exception as e:
            logger.error("summary_stats_failed", error=str(e))
            return {}
