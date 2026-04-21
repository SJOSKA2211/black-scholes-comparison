from datetime import datetime
from typing import Any, Dict, List

import structlog

from src.data.validators import MarketDataInput
from src.database import repository
from src.methods.analytical import BlackScholesAnalytical
from src.methods.base import OptionParams

logger = structlog.get_logger(__name__)


class DataPipeline:
    def __init__(self, run_id: str):
        self.run_id = run_id
        self.stats = {
            "rows_scraped": 0,
            "rows_validated": 0,
            "rows_inserted": 0,
            "error_count": 0,
        }

    async def process_rows(self, batch_rows: List[Dict[str, Any]]):
        """
        Process a batch of scraped rows: validate, upsert parameters,
        compute IV if missing, and insert market data.
        """
        self.stats["rows_scraped"] += len(batch_rows)

        for raw_row in batch_rows:
            try:
                # 1. Validate raw data
                validated_data = MarketDataInput(**raw_row)
                self.stats["rows_validated"] += 1

                # 2. Upsert Option Parameters to get/create option_id
                option_params_dict = {
                    "underlying_price": validated_data.underlying_price,
                    "strike_price": validated_data.strike_price,
                    "maturity_years": validated_data.maturity_years,
                    "volatility": validated_data.volatility
                    or 0.2,  # default if unknown
                    "risk_free_rate": validated_data.risk_free_rate,
                    "option_type": validated_data.option_type,
                    "is_american": validated_data.is_american,
                    "market_source": validated_data.market_source,
                }
                option_id = await repository.upsert_option_parameters(
                    option_params_dict
                )

                # 3. Compute Implied Volatility if not provided (IV inversion)
                mid_price = (validated_data.bid_price + validated_data.ask_price) / 2
                implied_vol = validated_data.volatility
                if not implied_vol:
                    analytical_engine = BlackScholesAnalytical()
                    option_params_obj = OptionParams(**option_params_dict)
                    implied_vol = analytical_engine.implied_volatility(
                        mid_price, option_params_obj
                    )

                # 4. Insert Market Data row
                market_data_dict = {
                    "option_id": option_id,
                    "trade_date": validated_data.trade_date.isoformat(),
                    "bid_price": validated_data.bid_price,
                    "ask_price": validated_data.ask_price,
                    "volume": validated_data.volume,
                    "open_interest": validated_data.open_interest,
                    "implied_vol": implied_vol,
                    "data_source": validated_data.data_source,
                }
                await repository.insert_market_data([market_data_dict])
                self.stats["rows_inserted"] += 1

            except Exception as processing_error:
                self.stats["error_count"] += 1
                logger.error(
                    "pipeline_row_error",
                    error=str(processing_error),
                    scrape_run_id=self.run_id,
                    raw_data=raw_row,
                )
                # Log to audit_log
                await repository.insert_audit_log(
                    pipeline_run_id=self.run_id,
                    step_name="transform_upsert",
                    status="failed",
                    rows_affected=0,
                    message=f"Error processing row: {str(processing_error)}",
                )

        # Final update to the scrape run record
        final_status = "success" if self.stats["error_count"] == 0 else "partial"
        if self.stats["rows_inserted"] == 0 and self.stats["rows_scraped"] > 0:
            final_status = "failed"

        await repository.update_scrape_run(
            self.run_id,
            {
                "rows_scraped": self.stats["rows_scraped"],
                "rows_validated": self.stats["rows_validated"],
                "rows_inserted": self.stats["rows_inserted"],
                "error_count": self.stats["error_count"],
                "status": final_status,
                "finished_at": datetime.utcnow().isoformat(),
            },
        )

        logger.info(
            "pipeline_completed", scrape_run_id=self.run_id, pipeline_stats=self.stats
        )
