import pandas as pd
import os
from flask import session
from net0.config.ef import CONVERSIONS


def convert_physical_to_s1_df(physical_data_list):
    rows = []
    for item in physical_data_list:
        year = int(item['Year'])
        prod = int(item['Production'])
        
        # Calculate energy in GJ for each fuel
        e_hsd = float(item.get('HSD_Liters', 0)) * CONVERSIONS['HSD']['NCV']
        e_cng = float(item.get('CNG_kg', 0)) * CONVERSIONS['CNG']['NCV']
        e_lpg = float(item.get('LPG_kg', 0)) * CONVERSIONS['LPG']['NCV']
        e_prop = float(item.get('Propane_kg', 0)) * CONVERSIONS['Propane']['NCV']
        e_da = float(item.get('DA_Liters', 0)) * CONVERSIONS['DA']['NCV']
        
        total_energy = e_hsd + e_cng + e_lpg + e_prop + e_da
        
        row = {
            'Year': year,
            'Production': prod,
            'Total_Energy': total_energy,
            'Renewable_Thermal_Energy': float(item.get('Renewable_Thermal_Energy', 0)),
            'HSD': e_hsd / total_energy if total_energy > 0 else 0.0,
            'CNG': e_cng / total_energy if total_energy > 0 else 0.0,
            'LPG': e_lpg / total_energy if total_energy > 0 else 0.0,
            'Propane': e_prop / total_energy if total_energy > 0 else 0.0,
            'DA': e_da / total_energy if total_energy > 0 else 0.0,
            'Electricity': 0.0,
            'Refrigerant Emissions': float(item.get('Refrigerant_Emissions', 0))
        }
        rows.append(row)
    return pd.DataFrame(rows)


def convert_physical_to_s2_df(physical_data_list):
    rows = []
    for item in physical_data_list:
        kwh = float(item.get('Electricity_kWh', 0))
        renewable = float(item.get('Renewable_Share', 0))
        grid_share = 1.0 - renewable
        
        row = {
            'Year': int(item['Year']),
            'Production': int(item['Production']),
            'Total_Energy': kwh * 0.0036, # Store in GJ to align with calculate_emissions_s2 (1 kWh = 0.0036 GJ)
            'Grid': grid_share,
            'Renewable': renewable,
            'Grid_EF': float(item.get('Grid_EF', 0.727))
        }
        rows.append(row)
    df = pd.DataFrame(rows)
    df["Electricity_kWh"] = df["Total_Energy"] * 1000 / 3.6
    return df


def get_data_s1():
    try:
        if session.get('ledger_s1'):
            return convert_physical_to_s1_df(session['ledger_s1'])
    except Exception:
        pass

    production_df = pd.DataFrame({
        "Year": [2021, 2022, 2023, 2024],
        "Production": [100725, 128326, 192205, 194555]
    })

    energy_df = pd.DataFrame({
        "Year": [2021, 2022, 2023, 2024],
        "Total_Energy": [367760, 492590, 452110, 422740],
        "Renewable_Thermal_Energy": [0, 0, 0, 0]
    })

    fuel_share_df = pd.DataFrame({
        "Year": [2021, 2022, 2023, 2024],
        "HSD": [0.586, 0.523, 0.477, 0.413],
        "CNG": [0.072, 0.079, 0.078, 0.101],
        "LPG": [0.170, 0.190, 0.228, 0.266],
        "Propane": [0.170, 0.206, 0.215, 0.218],
        "DA": [0.00046, 0.00024, 0.000044, 0.002],
        "Electricity": [0, 0, 0, 0]
    })

    refrigerant_emission_df = pd.DataFrame({
        "Year": [2021,2022,2023, 2024],
        "Refrigerant Emissions": [2481.630, 3287.759, 3719.097, 3800]
    })
    df = production_df.merge(energy_df, on="Year")
    df = df.merge(fuel_share_df, on="Year")
    df = df.merge(refrigerant_emission_df, on="Year")

    return df



def get_data_s2():
    try:
        if session.get('ledger_s2'):
            return convert_physical_to_s2_df(session['ledger_s2'])
    except Exception:
        pass

    production_df = pd.DataFrame({
        "Year": [2021, 2022, 2023, 2024],
        "Production": [100725, 128326, 192205, 194555]
    })

    energy_df = pd.DataFrame({
        "Year": [2021, 2022, 2023, 2024],
        "Total_Energy": [887240, 1128940, 1103980, 1141390]
    })

    renewable_share_df = pd.DataFrame({
        "Year": [2021, 2022, 2023, 2024],
        "Grid": [0.284, 0.418, 0.386, 0.301],
        "Renewable": [0.715, 0.581, 0.613, 0.698]
    })

    grid_ef_df = pd.DataFrame({
        "Year": [2021, 2022, 2023, 2024],
        "Grid_EF": [0.703, 0.715, 0.716, 0.727]
    })
    df = production_df.merge(energy_df, on="Year")
    df = df.merge(renewable_share_df, on="Year")
    df = df.merge(grid_ef_df, on="Year")
    df["Electricity_kWh"] = df["Total_Energy"] * 1000 / 3.6

    return df


def get_data_s3(cat_id):
    try:
        session_key = f'ledger_s3_cat{cat_id}'
        if session.get(session_key):
            rows = []
            for item in session[session_key]:
                rows.append({
                    'Year': int(item['Year']),
                    'Activity': float(item['Activity']),
                    'EF': float(item['EF'])
                })
            return pd.DataFrame(rows)
    except Exception:
        pass

    if cat_id == 7:
        cat7_df = pd.DataFrame({
            "Year": [2021, 2022, 2023, 2024],
            "Activity": [56560, 160220, 91650, 76140],
            "EF": [0.073, 0.080, 0.078, 0.078]
        })
        return cat7_df

    if cat_id == 4:
        cat4_df = pd.DataFrame({
            "Year": [2021, 2022, 2023, 2024],
            "Activity": [447090, 710350, 847870, 801000],
            "EF": [0.0732, 0.0818, 0.0818, 0.0820]
        })
        return cat4_df

    if cat_id == 5:
        cat5_df = pd.DataFrame({
            "Year": [2021, 2022, 2023, 2024],
            "Activity": [5000, 6160, 6630, 5770],
            "EF": [0.1562, 0.0818, 0.0818, 0.0820]
        })
        return cat5_df

    if cat_id == 9:
        cat9_df = pd.DataFrame({
            "Year": [2021, 2022, 2023, 2024],
            "Activity": [95750, 760950, 837050, 878890],
            "EF": [0.0656, 0.0818, 0.0818, 0.0820]
        })
        return cat9_df

    if cat_id == 6:
        cat6_df = pd.DataFrame({
            "Year": [2021, 2022, 2023, 2024],
            "Activity": [400, 2140, 260, 150],
            "EF": [0.0568, 0.0818, 0.0816, 0.0845]
        })
        return cat6_df

    if cat_id == 11:

        current_dir = os.path.dirname(os.path.abspath(__file__))

        data_dir = os.path.join(os.path.dirname(current_dir), "data")

        segments = ["lcv", "buses", "trucks"]
        all_dfs = []

        for seg in segments:
            path = os.path.join(data_dir, f"{seg}.csv")

            if os.path.exists(path):
                temp_df = pd.read_csv(path)
                temp_df["Segment"] = seg
                all_dfs.append(temp_df)
            else:
                print(f"CRITICAL: Still can't find {path}")

        return pd.concat(all_dfs, ignore_index=True)

