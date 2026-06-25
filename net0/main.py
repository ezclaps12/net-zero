import matplotlib.pyplot as plt

import scope.scope1 as scope1
import scope.scope2 as scope2
import scope.scope3.manager as scope3


def main():
    target_year = int(input("Enter Target-Year: "))
    target_production = int(input("Enter expected production during Target-Year: "))
    s1 = None
    s2 = None
    s3 = None

    while True:
        choice = int(input("Enter choice Scope1 (1) / Scope2 (2) / Scope3 (3) / Exit (4): "))
        if choice == 1:
            s1_bau, s1 = scope1.run_scope1(target_year, target_production)
        if choice == 2:
            s2_bau, s2 = scope2.run_scope2(target_year, target_production, s1)
        if choice == 3:
            s3_bau, s3 = scope3.run_scope3(target_year, target_production)
        if choice == 4:
            break

    total_emissions_bau_df = s1_bau.merge(s2_bau, on="Year", suffixes=('_s1', '_s2')).merge(s3_bau, on="Year")
    total_emissions_bau_df = total_emissions_bau_df.rename(columns={
        "Emissions": "Emissions_s3"
    })
    total_emissions_bau_df["Total Emissions"] = total_emissions_bau_df[["Emissions_s1", "Emissions_s2", "Emissions_s3"]].sum(axis = 1)
    total_emissions_bau_df = total_emissions_bau_df[["Year", "Production_s1", "Total Emissions"]]
    print("Total Baseline Emissions: ")
    print(total_emissions_bau_df.to_string())
    total_emissions_bau_df.plot(x="Year", y=["Total Emissions"])
    plt.show()

    total_emissions_df = s1.merge(s2, on="Year", suffixes=('_s1', '_s2')).merge(s3, on="Year")
    total_emissions_df = total_emissions_df.rename(columns={
        "Emissions": "Emissions_s3"
    })
    total_emissions_df["Total Emissions"] = total_emissions_df[["Emissions_s1", "Emissions_s2", "Emissions_s3"]].sum(axis = 1)
    total_emissions_df = total_emissions_df[["Year", "Production_s1", "Total Emissions"]]
    print("Total Emissions: ")
    print(total_emissions_df.to_string())
    total_emissions_df.plot(x="Year", y=["Total Emissions"])
    plt.show()


if __name__ == "__main__":
    main()
