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
    
    for year in years:
        year_initiatives = [init for init in initiatives if init.get('scope') == 'Scope 1' and int(init.get('year')) == year]
        
        for init in year_initiatives:
            itype = init.get('type')
            val = float(init.get('value', 0))
            val_type = init.get('val_type', 'percentage')
            
            total_energy = forecast_df.loc[forecast_df["Year"] == year, "Total_Energy"].values[0]
            mask = forecast_df["Year"] >= year
            
            if itype == 'fuel_switch':
                fuel_from = init.get('fuel_from')
                fuel_to = init.get('fuel_to')
                if fuel_from in fuel_cols and fuel_to in fuel_cols:
                    if val_type == 'absolute':
                        fraction = val / total_energy if total_energy > 0 else 0.0
                    else:
                        fraction = val / 100.0
                        
                    current_from = forecast_df.loc[forecast_df["Year"] == year, fuel_from].values[0]
                    switch_amt = min(fraction, current_from)
                    forecast_df.loc[mask, fuel_from] -= switch_amt
                    forecast_df.loc[mask, fuel_to] += switch_amt
            
            elif itype == 'capacity_expansion':
                fuel_to = init.get('fuel_to')
                if fuel_to in fuel_cols:
                    new_total_energy = total_energy + val
                    if new_total_energy > 0:
                        for col in fuel_cols:
                            old_share = forecast_df.loc[forecast_df["Year"] == year, col].values[0]
                            old_energy = old_share * total_energy
                            new_energy = old_energy + (val if col == fuel_to else 0.0)
                            forecast_df.loc[mask, col] = new_energy / new_total_energy
                        forecast_df.loc[mask, "Total_Energy"] = new_total_energy
            
            elif itype == 'energy_saving':
                if val_type == 'absolute':
                    forecast_df.loc[mask, "Total_Energy"] = (forecast_df.loc[mask, "Total_Energy"] - val).clip(lower=0.0)
                else:
                    forecast_df.loc[mask, "Total_Energy"] *= (1 - val / 100.0)
                
            elif itype == 'renewable_thermal':
                thermal_cols = ["HSD", "CNG", "LPG", "Propane", "DA"]
                thermal_total = forecast_df.loc[forecast_df["Year"] == year, thermal_cols].sum(axis=1).values[0]
                if thermal_total > 0:
                    if val_type == 'absolute':
                        total_thermal_energy = thermal_total * total_energy
                        renewable_energy = min(val, total_thermal_energy)
                        reduction_fraction = renewable_energy / total_thermal_energy if total_thermal_energy > 0 else 0.0
                    else:
                        fraction = val / 100.0
                        renewable_energy = thermal_total * fraction * total_energy
                        reduction_fraction = fraction
                        
                    forecast_df.loc[mask, "Renewable_Thermal_Energy"] += renewable_energy
                    for col in thermal_cols:
                        forecast_df.loc[mask, col] *= (1 - reduction_fraction)

    return forecast_df


def apply_initiatives_s2(forecast_df, initiatives, baseline_year):
    years = sorted(forecast_df["Year"].unique())
    
    for year in years:
        year_initiatives = [init for init in initiatives if init.get('scope') == 'Scope 2' and int(init.get('year')) == year]
        
        for init in year_initiatives:
            itype = init.get('type')
            val = float(init.get('value', 0))
            val_type = init.get('val_type', 'percentage')
            
            total_energy = forecast_df.loc[forecast_df["Year"] == year, "Total_Energy"].values[0]
            
            if itype == 'renewable_addition':
                current_grid = forecast_df.loc[forecast_df["Year"] == year, "Grid"].values[0]
                if val_type == 'absolute':
                    val_gj = val * 0.0036
                    fraction = val_gj / total_energy if total_energy > 0 else 0.0
                else:
                    fraction = val / 100.0
                    
                shift = min(fraction, current_grid)
                
                # Apply shift permanently to this year and all future years
                mask = forecast_df["Year"] >= year
                forecast_df.loc[mask, "Grid"] -= shift
                forecast_df.loc[mask, "Renewable"] += shift
                # Ensure values don't drop below 0
                forecast_df.loc[mask, "Grid"] = forecast_df.loc[mask, "Grid"].clip(lower=0.0)
                
            elif itype == 'electricity_saving':
                mask = forecast_df["Year"] >= year
                if val_type == 'absolute':
                    val_gj = val * 0.0036
                    forecast_df.loc[mask, "Total_Energy"] = (forecast_df.loc[mask, "Total_Energy"] - val_gj).clip(lower=0.0)
                else:
                    fraction = val / 100.0
                    forecast_df.loc[mask, "Total_Energy"] *= (1 - fraction)
                    
            elif itype == 'electricity_expansion':
                val_gj = val * 0.0036
                mask = forecast_df["Year"] >= year
                forecast_df.loc[mask, "Total_Energy"] += val_gj
                    
    return forecast_df

