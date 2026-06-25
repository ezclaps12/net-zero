import numpy as np


def run_cagr(base_val, target_val, years):
    values = []
    if base_val == 0 or target_val == 0:
        values = np.linspace(base_val, target_val, years)
        return values

    g = (target_val / base_val) ** (1/years) - 1
    current_val = base_val

    for i in range(years):
        current_val = current_val * (1+g)
        values.append(current_val)

    return np.array(values)

