import pandas as pd
import net0.core.dataloader as dataloader
import net0.core.emissions as emissions
import net0.core.activity as activity
import net0.core.scenario as scenario


def run_scope2(target_year, target_production, intensity_val, renewable_val, grid_ef_val, s1=None, baseline_year=2024, initiatives=[]):
    full_df = dataloader.get_data_s2()

    # Split into historical (up to baseline) and roadmap (after baseline)
    historical_df = full_df[full_df["Year"] <= baseline_year].copy()
    roadmap_df = full_df[full_df["Year"] > baseline_year].copy()

    historical_df = emissions.calculate_intensity(historical_df)

    intensity_slider_value = intensity_val
    renewable_slider_value = renewable_val
    grid_ef_slider_value = grid_ef_val

    # 1. Forecast Total_Energy dynamically from baseline to target_year
    forecast_bau = activity.forecast_activity_s2(historical_df, target_year, target_production,
                                                 intensity_slider_value=0, grid_ef_slider_value=0)
    forecast_df = activity.forecast_activity_s2(historical_df, target_year, target_production,
                                                intensity_slider_value, grid_ef_slider_value)

    # Add electrification energy from S1 if available
    if s1 is not None:
        s1_copy = s1.copy()
        s1_copy["Electricity_Energy"] = s1_copy["Total_Energy"] * s1_copy["Electricity"]
        forecast_df = forecast_df.merge(s1_copy[["Year", "Electricity_Energy"]], on="Year", how="left")
        forecast_df["Total_Energy"] += forecast_df["Electricity_Energy"].fillna(0)
        forecast_bau = forecast_bau.merge(s1_copy[["Year", "Electricity_Energy"]], on="Year", how="left")
        forecast_bau["Total_Energy"] += forecast_bau["Electricity_Energy"].fillna(0)

    # 2. Overlay Grid, Renewable, and Grid_EF from the ledger roadmap
    last_known_grid = historical_df.iloc[-1]["Grid"]
    last_known_renewable = historical_df.iloc[-1]["Renewable"]
    
    for i, row in forecast_df.iterrows():
        year = row["Year"]
        roadmap_match = roadmap_df[roadmap_df["Year"] == year]
        
        if not roadmap_match.empty:
            last_known_grid = roadmap_match.iloc[0]["Grid"]
            last_known_renewable = roadmap_match.iloc[0]["Renewable"]
            # Overwrite Grid_EF with the exact roadmap value if provided
            forecast_df.loc[i, "Grid_EF"] = roadmap_match.iloc[0]["Grid_EF"]
            forecast_bau.loc[i, "Grid_EF"] = roadmap_match.iloc[0]["Grid_EF"]
            
        forecast_df.loc[i, "Grid"] = last_known_grid
        forecast_df.loc[i, "Renewable"] = last_known_renewable
        forecast_bau.loc[i, "Grid"] = last_known_grid
        forecast_bau.loc[i, "Renewable"] = last_known_renewable

    # 3. Apply initiatives and sliders to the forecast
    scenario_df = scenario.apply_initiatives_s2(forecast_df, initiatives, baseline_year)
    scenario_df = scenario.apply_renewable(scenario_df, renewable_slider_value)

    # 4. Build combined DataFrames
    combined_bau_df = pd.concat([historical_df, forecast_bau], ignore_index=True)
    combined_df = pd.concat([historical_df, scenario_df], ignore_index=True)

    print(combined_df.to_string())
    s2_bau = emissions.calculate_emissions_s2(combined_bau_df)
    s2 = emissions.calculate_emissions_s2(combined_df)
    print(s2.to_string())
    return s2_bau, s2
