import numpy as np
import pandas as pd
import net0.core.formula as formula


def apply_renewable_thermal(forecast_df, renewable_thermal_slider_value):

    thermal_cols = ["HSD", "CNG", "LPG", "Propane", "DA"]
    renewable_path = np.linspace(0.01, renewable_thermal_slider_value, len(forecast_df))

    for i in range(len(forecast_df)):
        renewable_share = renewable_path[i]
        thermal_total = forecast_df.loc[i, thermal_cols].sum()
        renewable_energy = thermal_total * renewable_share * forecast_df.loc[i, "Total_Energy"]
        forecast_df.loc[i, "Total_Energy"] -= renewable_energy
        forecast_df.loc[i, "Renewable_Thermal_Energy"] = renewable_energy

    return forecast_df


def fuel_conversion_matrix(conversion, fuel_cols, forecast_df):
    n = len(fuel_cols)
    matrix = np.eye(n)
    fuel_idx = {}
    for i, fuel in enumerate(fuel_cols):
        fuel_idx[fuel] = i

    for fuel1, fuel2, fuel1_to_fuel2_slider_value in conversion:
        i = fuel_idx[fuel1]
        j = fuel_idx[fuel2]

        matrix[i][i] -= fuel1_to_fuel2_slider_value
        matrix[i][j] += fuel1_to_fuel2_slider_value

    print(matrix)
    last_shares = forecast_df[fuel_cols].iloc[0].values
    print(last_shares)
    new_shares = np.dot(last_shares, matrix)
    print(new_shares)

    for i in range(n):
        fuel1_to_fuel2_conversion(forecast_df, last_shares[i], new_shares[i], fuel_cols[i])

    return forecast_df


def fuel1_to_fuel2_conversion(forecast_df, base_fuel, target_fuel, fuel):
    years = len(forecast_df) + 1

    fuel_values = np.linspace(base_fuel, target_fuel, years)

    forecast_df[fuel] = fuel_values[1:]
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
