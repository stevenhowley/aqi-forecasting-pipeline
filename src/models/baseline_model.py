from dataclasses import dataclass
from typing import Optional

import pandas as pd


@dataclass
class NaiveAQIForecastModel:
    """
    Very simple baseline AQI forecasting model.

    strategy = "persistence":
        forecast_aqi(t+1) = observed max_aqi(t) for each location.

    strategy = "mean":
        forecast_aqi(t+1) = mean of historical max_aqi for that location.
    """

    strategy: str = "persistence"
    location_means_: Optional[dict] = None

    def fit(self, df: pd.DataFrame) -> None:
        """
        "Train" the model on historical daily aggregates.

        Expects df with at least:
            - location_id
            - date
            - max_aqi
        """
        if self.strategy == "mean":
            self.location_means_ = (
                df.groupby("location_id")["max_aqi"].mean().to_dict()
            )
        else:
            # persistence model doesn't really need training
            self.location_means_ = None

    def predict(self, df: pd.DataFrame) -> pd.Series:
        """
        Predict next-day AQI for each row in df.

        Expects df with:
            - location_id
            - max_aqi  (most recent day's max AQI)
        """
        if self.strategy == "persistence":
            # forecast = today's max_aqi
            return df["max_aqi"].astype(float)

        if self.strategy == "mean":
            if self.location_means_ is None:
                raise RuntimeError("Model not fitted: location_means_ is None.")

            return df["location_id"].map(self.location_means_).astype(float)

        raise ValueError(f"Unknown strategy: {self.strategy}")
