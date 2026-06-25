import pandas as pd
import net0.core.dataloader as dataloader
import net0.core.emissions as emissions
import net0.core.activity as activity
import net0.core.scenario as scenario


def run_scope2(target_year, target_production, intensity_val, renewable_val, grid_ef_val, s1=None):
    df = dataloader.get_data_s2()
    df = emissions.calculate_intensity(df)

    intensity_slider_value = intensity_val
    renewable_slider_value = renewable_val
    grid_ef_slider_value = grid_ef_val

    bau_df = activity.forecast_activity_s2(df, target_year, target_production, intensity_slider_value=0,
                                           grid_ef_slider_value=0)
    forecast_df = activity.forecast_activity_s2(df, target_year, target_production, intensity_slider_value,
                                                grid_ef_slider_value)

    if s1 is not None:

        s1["Electricity_Energy"] = s1["Total_Energy"] * s1["Electricity"]
        forecast_df = forecast_df.merge(s1[["Year", "Electricity_Energy"]], on="Year", how="left")
        forecast_df["Total_Energy"] += forecast_df["Electricity_Energy"]

    electricity_cols = ["Grid", "Renewable"]
    last_share = df.iloc[-1][electricity_cols]
    for col in electricity_cols:
        forecast_df[col] = last_share[col]
        bau_df[col] = last_share[col]

    scenario_df = scenario.apply_renewable(forecast_df, renewable_slider_value)

    combined_bau_df = pd.concat([df, bau_df], ignore_index=True)
    combined_df = pd.concat([df, scenario_df], ignore_index=True)

    print(combined_df.to_string())
    s2_bau = emissions.calculate_emissions_s2(combined_bau_df)
    s2 = emissions.calculate_emissions_s2(combined_df)
    print(s2.to_string())
    return s2_bau, s2
