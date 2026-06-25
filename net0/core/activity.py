import numpy as np
import pandas as pd
import net0.core.formula as formula


def forecast_activity_s1(df, target_year, target_production, intensity_slider_value, refr_growth_rate):
    base_production = df["Production"].iloc[-1]
    base_intensity = df["Intensity"].iloc[-1]
    target_intensity = base_intensity * (1 - intensity_slider_value)
    last_year = df["Year"].iloc[-1]
    last_refr_val = df["Refrigerant Emissions"].iloc[-1]
    target_refr_val = last_refr_val * (1 + refr_growth_rate)
    years = target_year - last_year
    if years <= 0:
        raise ValueError("Target year must be greater than last year")

    future_years = np.arange(last_year + 1, target_year + 1)
    forecast_df = pd.DataFrame({
        "Year": future_years
    })

    productions = formula.run_cagr(base_production, target_production, years)
    intensity_values = formula.run_cagr(base_intensity, target_intensity, years)
    refr_values = formula.run_cagr(last_refr_val, target_refr_val, years)

    forecast_df["Production"] = productions
    forecast_df["Intensity"] = intensity_values
    forecast_df["Refrigerant Emissions"] = refr_values
    forecast_df["Total_Energy"] = forecast_df["Production"] * forecast_df["Intensity"]

    return forecast_df


def forecast_activity_s2(df, target_year, target_production, intensity_slider_value, grid_ef_slider_value):
    base_production = df["Production"].iloc[-1]
    base_intensity = df["Intensity"].iloc[-1]
    base_grid_ef = df["Grid_EF"].iloc[-1]
    target_intensity = base_intensity * (1 - intensity_slider_value)
    target_grid = base_grid_ef * (1 - grid_ef_slider_value)
    last_year = df["Year"].iloc[-1]
    years = target_year - last_year

    if years <= 0:
        raise ValueError("Target year must be greater than last year")

    future_years = np.arange(last_year + 1, target_year + 1)
    forecast_df = pd.DataFrame({
        "Year": future_years
    })

    productions = formula.run_cagr(base_production, target_production, years)
    intensity_values = formula.run_cagr(base_intensity, target_intensity, years)

    grid_values = np.linspace(base_grid_ef, target_grid, years)

    forecast_df["Production"] = productions
    forecast_df["Intensity"] = intensity_values
    forecast_df["Grid_EF"] = grid_values
    forecast_df["Total_Energy"] = forecast_df["Production"] * forecast_df["Intensity"]

    return forecast_df
