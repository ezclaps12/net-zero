import numpy as np
import pandas as pd


def calculate_ev_transition(
    start_year=2024,
    end_year=2035,
    diesel_rate_g_km=585.26,
    lifetime_km=1000000,
    ev_kwh_km=1.1,
    grid_ef_start=0.716,
    grid_ef_end=0.350,
    diesel_start_prod=9000,
    diesel_end_prod=5000,
    ev_start_prod=1000,
    ev_end_prod=10000
):
    """
    Simulates fleet lifetime emissions transition from Diesel to Electric Vehicles.
    
    Parameters:
        start_year (int): Baseline start year (e.g. 2024)
        end_year (int): Target horizon year (e.g. 2035)
        diesel_rate_g_km (float): Diesel vehicle tailpipe emission rate in gCO2/km
        lifetime_km (float): Vehicle operating lifetime distance in km (e.g. 1,000,000 km)
        ev_kwh_km (float): EV vehicle energy consumption rate in kWh/km
        grid_ef_start (float): Baseline grid emission factor in kgCO2/kWh
        grid_ef_end (float): Target grid emission factor in kgCO2/kWh
        diesel_start_prod (int): Baseline annual production of Diesel vehicles
        diesel_end_prod (int): Target annual production of Diesel vehicles
        ev_start_prod (int): Baseline annual production of EV vehicles
        ev_end_prod (int): Target annual production of EV vehicles
        
    Returns:
        pd.DataFrame: Yearly scenario metrics and emissions dataframe
    """
    start_year = int(start_year)
    end_year = int(end_year)
    if end_year <= start_year:
        end_year = start_year + 1

    years = np.arange(start_year, end_year + 1)
    n_years = len(years)

    if n_years > 1:
        t_factors = np.linspace(0.0, 1.0, n_years)
    else:
        t_factors = np.array([0.0])

    diesel_prods = diesel_start_prod + t_factors * (diesel_end_prod - diesel_start_prod)
    ev_prods = ev_start_prod + t_factors * (ev_end_prod - ev_start_prod)
    grid_efs = grid_ef_start + t_factors * (grid_ef_end - grid_ef_start)

    # 1 Diesel bus lifetime emissions in tCO2e (585.26 g/km * 1,000,000 km / 1,000,000 = 585.26 tCO2e)
    diesel_unit_emissions = (diesel_rate_g_km * lifetime_km) / 1000000.0

    # 1 EV bus lifetime emissions in tCO2e (1.1 kWh/km * 1,000,000 km * Grid_EF kgCO2/kWh / 1000)
    ev_unit_emissions = (ev_kwh_km * lifetime_km * grid_efs) / 1000.0

    diesel_emissions = diesel_prods * diesel_unit_emissions
    ev_emissions = ev_prods * ev_unit_emissions
    combined_emissions = diesel_emissions + ev_emissions

    # BAU scenario: scale total annual production at baseline Diesel/EV ratio and baseline Grid EF
    total_start_prod = diesel_start_prod + ev_start_prod
    diesel_share_base = diesel_start_prod / total_start_prod if total_start_prod > 0 else 0.9
    ev_share_base = ev_start_prod / total_start_prod if total_start_prod > 0 else 0.1

    total_prods = diesel_prods + ev_prods
    bau_diesel_unit = diesel_unit_emissions
    bau_ev_unit = (ev_kwh_km * lifetime_km * grid_ef_start) / 1000.0
    bau_series = total_prods * (diesel_share_base * bau_diesel_unit + ev_share_base * bau_ev_unit)

    df = pd.DataFrame({
        'Year': years,
        'Diesel_Prod': np.round(diesel_prods).astype(int),
        'EV_Prod': np.round(ev_prods).astype(int),
        'Total_Prod': np.round(diesel_prods + ev_prods).astype(int),
        'Grid_EF': np.round(grid_efs, 4),
        'Diesel_Unit_Emissions': np.round(diesel_unit_emissions, 2),
        'EV_Unit_Emissions': np.round(ev_unit_emissions, 2),
        'Diesel_Emissions': np.round(diesel_emissions, 2),
        'EV_Emissions': np.round(ev_emissions, 2),
        'Combined_Emissions': np.round(combined_emissions, 2),
        'BAU_Emissions': np.round(bau_series, 2)
    })

    return df
