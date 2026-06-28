import pandas as pd
import net0.core.emissions as emissions

from net0.scope.scope3.cat4 import Cat4Upstream
from net0.scope.scope3.cat5 import Cat5Waste
from net0.scope.scope3.cat6 import Cat6Business
from net0.scope.scope3.cat7 import Cat7Commute
from net0.scope.scope3.cat9 import Cat9Downstream
from net0.scope.scope3.cat11 import Cat11SoldVehicles


def run_scope3(target_year, target_production, all_inputs, baseline_year=2024):
    available_cats = {
        4: Cat4Upstream, 5: Cat5Waste, 6: Cat6Business,
        7: Cat7Commute, 9: Cat9Downstream, 11: Cat11SoldVehicles
    }

    bau_results = []
    scenario_results = []

    # Only process categories that the user has explicitly enabled/selected.
    # Categories not in all_inputs should contribute 0 emissions.
    if not all_inputs:
        return pd.DataFrame(columns=["Year", "Emissions"]), pd.DataFrame(columns=["Year", "Emissions"])

    for cat_id, cat_class in available_cats.items():
        if cat_id not in all_inputs:
            continue

        cat_obj = cat_class()
        raw_data = cat_obj.load_data()
        raw_data = raw_data[raw_data["Year"] <= baseline_year].copy()

        if cat_id == 11:
            bau_sliders = {
                "activity_slider_lcv": 65049,
                "activity_slider_buses": 21253,
                "activity_slider_trucks": 93540,
                "ef_slider": 0
            }
        else:
            bau_sliders = {"activity_slider": 0, "ef_slider": 0}

        bau_df = cat_obj.apply_scenario(raw_data, target_year, bau_sliders)
        bau_df["Category"] = cat_obj.name
        bau_results.append(bau_df)

        sliders = all_inputs.get(cat_id, bau_sliders)

        scenario_df = cat_obj.apply_scenario(raw_data, target_year, sliders)
        scenario_df["Category"] = cat_obj.name
        scenario_results.append(scenario_df)

    if not bau_results:
        return pd.DataFrame(columns=["Year", "Emissions"]), pd.DataFrame(columns=["Year", "Emissions"])

    full_bau = pd.concat(bau_results)
    full_scenario = pd.concat(scenario_results)

    full_bau = emissions.calculate_emissions_s3(full_bau)
    full_scenario = emissions.calculate_emissions_s3(full_scenario)
    bau_total = full_bau.groupby("Year")["Emissions"].sum().reset_index()
    scenario_total = full_scenario.groupby("Year")["Emissions"].sum().reset_index()
    print("Scope 3 Scenario Final Total (2021-2040):")
    print(scenario_total.to_string())

    return bau_total, scenario_total

