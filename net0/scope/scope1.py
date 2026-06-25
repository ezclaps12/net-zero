import pandas as pd
import net0.core.dataloader as dataloader
import net0.core.emissions as emissions
import net0.core.activity as activity
import net0.config.ef as ef
import net0.core.scenario as scenario


def run_scope1(target_year, target_production, intensity_val, therm_re_val,
               electrification_val, refr_growth_val, refr_red_val, conversions):

    df = dataloader.get_data_s1()
    df = emissions.calculate_intensity(df)

    intensity_slider_value = intensity_val
    therm_renewable_slider_value = therm_re_val
    electrification_slider_value = electrification_val
    refr_growth_rate = refr_growth_val
    refr_emission_slider_value = refr_red_val

    bau_df = activity.forecast_activity_s1(df, target_year, target_production,
                                           intensity_slider_value=0, refr_growth_rate=0)
    forecast_df = activity.forecast_activity_s1(df, target_year, target_production,
                                                intensity_slider_value, refr_growth_rate)

    bau_df["Renewable_Thermal_Energy"] = df.iloc[-1]["Renewable_Thermal_Energy"]
    fuel_cols = ["HSD", "CNG", "LPG", "Propane", "DA", "Electricity"]
    last_share = df.iloc[-1][fuel_cols]

    for fuel in fuel_cols:
        bau_df[fuel] = last_share[fuel]
        forecast_df[fuel] = last_share[fuel]

    forecast_df["Renewable_Thermal_Energy"] = 0.0

    scenario_df = scenario.apply_renewable_thermal(forecast_df, therm_renewable_slider_value)
    scenario_df = scenario.fuel_conversion_matrix(conversions, fuel_cols, scenario_df)
    scenario_df = scenario.apply_electrification(scenario_df, electrification_slider_value)
    scenario_df = scenario.apply_refrigerant_reduction(df, forecast_df, refr_emission_slider_value)

    combined_bau_df = pd.concat([df, bau_df], ignore_index=True)
    combined_df = pd.concat([df, scenario_df], ignore_index=True)

    print(combined_df.to_string())
    s1_bau = emissions.calculate_emissions_s1(combined_bau_df, ef.EF)
    s1 = emissions.calculate_emissions_s1(combined_df, ef.EF)
    print(s1.to_string())
    return s1_bau, s1
