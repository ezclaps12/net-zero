# IPCC AR6 Standard Emission Factors & Calorific Value Conversions
EF = {
    "HSD": 74.1,       # tCO2/TJ (Scope 1 default)
    "HFO": 77.4,       # tCO2/TJ
    "CNG": 56.1,       # tCO2/TJ
    "LPG": 63.1,       # tCO2/TJ
    "Propane": 63.1,   # tCO2/TJ
    "DA": 74.1,        # tCO2/TJ
}

CONVERSIONS = {
    "HSD": {
        "NCV": 0.036,      # GJ / Litre
        "EF": 2.68         # kg CO2e / Litre
    },
    "CNG": {
        "NCV": 0.047,      # GJ / kg
        "EF": 2.69         # kg CO2e / kg
    },
    "LPG": {
        "NCV": 0.046,      # GJ / kg
        "EF": 2.98         # kg CO2e / kg
    },
    "Propane": {
        "NCV": 0.046,      # GJ / kg
        "EF": 3.00         # kg CO2e / kg
    },
    "DA": {
        "NCV": 0.036,      # GJ / Litre
        "EF": 2.68         # kg CO2e / Litre
    }
}

