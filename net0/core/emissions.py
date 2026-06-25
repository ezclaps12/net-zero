

def calculate_intensity(df):
    df["Intensity"] = df["Total_Energy"] / df["Production"]
    return df


def calculate_emissions_s1(df, ef):
    df["Emissions"] = (
      df["Total_Energy"] * df["HSD"] * ef["HSD"] +
      df["Total_Energy"] * df["CNG"] * ef["CNG"] +
      df["Total_Energy"] * df["LPG"] * ef["LPG"] +
      df["Total_Energy"] * df["Propane"] * ef["Propane"] +
      df["Total_Energy"] * df["DA"] * ef["DA"]
    ) / 1000 + df["Refrigerant Emissions"]
    return df


def calculate_emissions_s2(df):
    df["Emissions"] = (
        df["Total_Energy"] * df["Grid"] * (df["Grid_EF"]/3.6)
    )
    return df


def calculate_emissions_s3(df):
    df["Emissions"] = (
        df["Activity"] * df["EF"]
    )
    return df
