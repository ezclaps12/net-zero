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


def apply_initiatives_s1(forecast_df, initiatives, baseline_year):
    fuel_cols = ["HSD", "CNG", "LPG", "Propane", "DA", "Electricity"]
    years = sorted(forecast_df["Year"].unique())
    
    for i, year in enumerate(years):
        if i > 0:
            prev_year = years[i-1]
            for col in fuel_cols:
                forecast_df.loc[forecast_df["Year"] == year, col] = forecast_df.loc[forecast_df["Year"] == prev_year, col].values[0]
            forecast_df.loc[forecast_df["Year"] == year, "Renewable_Thermal_Energy"] = forecast_df.loc[forecast_df["Year"] == prev_year, "Renewable_Thermal_Energy"].values[0]
            
        year_initiatives = [init for init in initiatives if init.get('scope') == 'Scope 1' and int(init.get('year')) == year]
        
        for init in year_initiatives:
            itype = init.get('type')
            val = float(init.get('value', 0)) / 100.0
            
            if itype == 'fuel_switch':
                fuel_from = init.get('fuel_from')
                fuel_to = init.get('fuel_to')
                if fuel_from in fuel_cols and fuel_to in fuel_cols:
                    current_from = forecast_df.loc[forecast_df["Year"] == year, fuel_from].values[0]
                    switch_amt = min(val, current_from)
                    forecast_df.loc[forecast_df["Year"] == year, fuel_from] -= switch_amt
                    forecast_df.loc[forecast_df["Year"] == year, fuel_to] += switch_amt
            
            elif itype == 'energy_saving':
                forecast_df.loc[forecast_df["Year"] == year, "Total_Energy"] *= (1 - val)
                
            elif itype == 'renewable_thermal':
                thermal_cols = ["HSD", "CNG", "LPG", "Propane", "DA"]
                thermal_total = forecast_df.loc[forecast_df["Year"] == year, thermal_cols].sum(axis=1).values[0]
                if thermal_total > 0:
                    renewable_energy = thermal_total * val * forecast_df.loc[forecast_df["Year"] == year, "Total_Energy"].values[0]
                    forecast_df.loc[forecast_df["Year"] == year, "Renewable_Thermal_Energy"] += renewable_energy
                    forecast_df.loc[forecast_df["Year"] == year, thermal_cols] *= (1 - val)

    return forecast_df


def apply_initiatives_s2(forecast_df, initiatives, baseline_year):
    years = sorted(forecast_df["Year"].unique())
    
    for i, year in enumerate(years):
        if i > 0:
            prev_year = years[i-1]
            forecast_df.loc[forecast_df["Year"] == year, "Grid"] = forecast_df.loc[forecast_df["Year"] == prev_year, "Grid"].values[0]
            forecast_df.loc[forecast_df["Year"] == year, "Renewable"] = forecast_df.loc[forecast_df["Year"] == prev_year, "Renewable"].values[0]
            
        year_initiatives = [init for init in initiatives if init.get('scope') == 'Scope 2' and int(init.get('year')) == year]
        
        for init in year_initiatives:
            itype = init.get('type')
            val = float(init.get('value', 0)) / 100.0
            
            if itype == 'renewable_addition':
                current_grid = forecast_df.loc[forecast_df["Year"] == year, "Grid"].values[0]
                shift = min(val, current_grid)
                forecast_df.loc[forecast_df["Year"] == year, "Grid"] -= shift
                forecast_df.loc[forecast_df["Year"] == year, "Renewable"] += shift
                
            elif itype == 'electricity_saving':
                forecast_df.loc[forecast_df["Year"] == year, "Total_Energy"] *= (1 - val)
                
    return forecast_df

