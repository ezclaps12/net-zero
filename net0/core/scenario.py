import numpy as np
import pandas as pd
import net0.core.formula as formula


def apply_renewable_thermal(forecast_df, renewable_thermal_slider_value):
    thermal_cols = ["HSD", "CNG", "LPG", "Propane", "DA"]
    if renewable_thermal_slider_value == 0:
        forecast_df["Renewable_Thermal_Energy"] = 0.0
        return forecast_df

    renewable_path = np.linspace(0.01, renewable_thermal_slider_value, len(forecast_df))

    for i in range(len(forecast_df)):
        renewable_share = renewable_path[i]
        thermal_total = forecast_df.loc[i, thermal_cols].sum()
        if thermal_total > 0:
            renewable_energy = thermal_total * renewable_share * forecast_df.loc[i, "Total_Energy"]
            forecast_df.loc[i, "Renewable_Thermal_Energy"] = renewable_energy
            forecast_df.loc[i, thermal_cols] *= (1 - renewable_share)
        else:
            forecast_df.loc[i, "Renewable_Thermal_Energy"] = 0.0

    return forecast_df


def fuel_conversion_matrix(conversion, fuel_cols, forecast_df):
    n = len(fuel_cols)
    fuel_idx = {fuel: idx for idx, fuel in enumerate(fuel_cols)}

    for i in range(len(forecast_df)):
        t_i = (i + 1) / len(forecast_df)
        matrix_i = np.eye(n)
        for fuel1, fuel2, val in conversion:
            idx1 = fuel_idx[fuel1]
            idx2 = fuel_idx[fuel2]
            val_i = val * t_i
            matrix_i[idx1][idx1] -= val_i
            matrix_i[idx1][idx2] += val_i

        current_shares = forecast_df.loc[i, fuel_cols].values
        new_shares_i = np.dot(current_shares, matrix_i)
        forecast_df.loc[i, fuel_cols] = new_shares_i

    return forecast_df



def apply_electrification(forecast_df, electrification_slider_value):
    fossil_cols = ["HSD", "CNG", "LPG", "Propane", "DA"]
    years = len(forecast_df)
    electrification_path = np.linspace(0.01, electrification_slider_value, years)

    for i in range(years):
        e = electrification_path[i]
        fossil_total = forecast_df.loc[i, fossil_cols].sum()
        if fossil_total == 0:
            continue
        shift = fossil_total * e
        reduction_factor = 1 - (shift / fossil_total)
        forecast_df.loc[i, fossil_cols] *= reduction_factor
        forecast_df.loc[i, "Electricity"] += shift

    return forecast_df


def apply_refrigerant_reduction(df, forecast_df, emission_reduction_slider_value):
    if emission_reduction_slider_value == 0:
        return forecast_df
    years = len(forecast_df)
    base_emission = df["Refrigerant Emissions"].iloc[-1]
    final_emission = forecast_df["Refrigerant Emissions"].iloc[-1]
    target_emission = final_emission * (1 - emission_reduction_slider_value)

    emission_values = formula.run_cagr(base_emission, target_emission, years)
    forecast_df["Refrigerant Emissions"] = emission_values

    return forecast_df


def apply_renewable(forecast_df, renewable_slider_value):
    years = len(forecast_df)
    base_grid = forecast_df["Grid"].iloc[0]
    target_grid = base_grid * (1 - renewable_slider_value)
    grid_values = formula.run_cagr(base_grid, target_grid, years)

    forecast_df["Grid"] = grid_values
    forecast_df["Renewable"] = 1 - grid_values

    return forecast_df


def apply_conversion_matrix(conversion, fuel_cols, forecast_df):
    wide_df = forecast_df.pivot(index = ["Year","Segment"])
    return forecast_df
