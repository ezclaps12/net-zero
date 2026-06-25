import numpy as np
import pandas as pd
import net0.core.scenario as scenario
import net0.core.formula as formula
from net0.scope.scope3.Scope3 import Scope3


class Cat11SoldVehicles(Scope3):
    def __init__(self):
        super().__init__(cat_id=11)

    def calc_emissions(self,forecast_df):
        forecast_df["Emissions"] = ((forecast_df["Units"] * forecast_df["Diesel"] * forecast_df["Diesel_EF"] +
                                     forecast_df["Units"] * forecast_df["LPG/CNG"] * forecast_df["LPG/CNG_EF"] +
                                     forecast_df["Units"] * forecast_df["Electricity"] * forecast_df["Grid_EF"] +
                                     forecast_df["Units"] * forecast_df["Hydrogen"] * forecast_df["Hydrogen_EF"]) *
                                    forecast_df["Avg_Annual_Km"] * forecast_df["Life_Years"]) / 1000
        return forecast_df

    def apply_scenario(self, df, target_year, sliders):
        df_list = []
        forecast_list = []
        for seg in df["Segment"].unique():
            seg_df = df[df["Segment"] == seg].copy()
            df_list.append(seg_df)

            seg_conversions = sliders.get(f"conversions_{seg}", [])

            seg_forecast = self.apply_forecast(seg_df, target_year, sliders, seg, seg_conversions)
            print(seg_forecast.to_string())
            forecast_list.append(seg_forecast)

        df = pd.concat(df_list, ignore_index=True)
        forecast_df = pd.concat(forecast_list, ignore_index=True)

        df = self.calc_emissions(df)
        forecast_df = self.calc_emissions(forecast_df)

        df = df.groupby("Year")[["Units","Emissions"]].sum().reset_index()
        forecast_df = forecast_df.groupby("Year")[["Units", "Emissions"]].sum().reset_index()

        forecast_df = pd.concat([df,forecast_df], ignore_index=True)

        forecast_df.rename(columns={"Units": "Activity"}, inplace=True)

        forecast_df["EF"] = forecast_df["Emissions"] / forecast_df["Activity"]
        print(forecast_df.to_string())
        return forecast_df

    def apply_forecast(self, df, target_year, sliders, seg_name, conversions):
        last_year = df["Year"].iloc[-1]
        years_count = target_year - last_year

        base_units = df["Units"].iloc[-1]
        target_units = sliders.get(f"activity_slider_{seg_name}", 0)
        unit_values = formula.run_cagr(base_units, target_units, years_count)

        future_years = np.arange(last_year + 1, target_year + 1)
        forecast_df = pd.DataFrame({"Year": future_years})
        forecast_df["Units"] = unit_values

        fuel_cols = ["Diesel", "LPG/CNG", "Electricity", "Hydrogen"]
        for col in fuel_cols:
            forecast_df[col] = df[col].iloc[-1]

        forecast_df = scenario.fuel_conversion_matrix(conversions, fuel_cols, forecast_df)

        ef_improvement_total = sliders.get("ef_slider", 0)

        ef_cols = ["Diesel_EF", "LPG/CNG_EF", "Grid_EF", "Hydrogen_EF"]

        for col in ef_cols:
            start_ef = df[col].iloc[-1]
            end_ef = start_ef * (1 - ef_improvement_total)

            forecast_df[col] = np.linspace(start_ef, end_ef, len(future_years))

        forecast_df["Segment"] = seg_name
        forecast_df["Avg_Annual_Km"] = df["Avg_Annual_Km"].iloc[-1]
        forecast_df["Life_Years"] = df["Life_Years"].iloc[-1]

        return forecast_df
