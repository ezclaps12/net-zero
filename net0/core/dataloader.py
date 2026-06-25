import pandas as pd
import os


def get_data_s1():
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

    return df


def get_data_s3(cat_id):

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

