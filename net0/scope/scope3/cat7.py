import numpy as np
import pandas as pd
import net0.core.formula as formula
from net0.scope.scope3.Scope3 import Scope3


class Cat7Commute(Scope3):
    def __init__(self):
        super().__init__(cat_id=7)

    def apply_scenario(self, df, target_year, sliders):
        last_year = df["Year"].iloc[-1]
        years = target_year - last_year

        future_years = np.arange(last_year + 1, target_year + 1)
        forecast_df = pd.DataFrame({
            "Year": future_years
        })
        base_activity = df["Activity"].iloc[-1]
        base_ef = df["EF"].iloc[-1]

        activity_slider = sliders.get("activity_slider", 0)
        ef_slider = sliders.get("ef_slider", 0)

        if ef_slider == 0 and activity_slider == 0:
            forecast_df["Activity"] = base_activity
            forecast_df["EF"] = base_ef
            return forecast_df

        target_activity = base_activity * (1 - activity_slider)
        activity_values = formula.run_cagr(base_activity, target_activity, years)

        target_ef = base_ef * (1 - ef_slider)
        ef_values = np.linspace(base_ef, target_ef, years)

        forecast_df["Activity"] = activity_values
        forecast_df["EF"] = ef_values

        forecast_df = pd.concat([df, forecast_df], ignore_index=True)

        return forecast_df
