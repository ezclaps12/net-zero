# Codebase Review: Net Zero Scenario Planner

This review analyzes the current architecture, implementation, and calculation logic of the **Net Zero Scenario Planner** web application and highlights critical bugs, design flaws, and opportunities for improvements.

---

## 1. Architectural & Code Quality Review

### 📂 Code Duplication (Scope 3 Category Classes)
- **Problem**: There is a severe violation of the DRY (Don't Repeat Yourself) principle in the Scope 3 category implementations. Classes like [Cat4Upstream](file:///C:/Users/LENOVO/PycharmProjects/net0_app/net0/scope/scope3/cat4.py) and other categories have duplicate code for `apply_scenario`.
- **Improvement**: Refactor the common `apply_scenario` logic into the base [Scope3](file:///C:/Users/LENOVO/PycharmProjects/net0_app/net0/scope/scope3/Scope3.py) class. (Note: This refactoring has been initialized!)

### 🔌 Hardcoded Historical Baseline Data
- **Problem**: In [dataloader.py](file:///C:/Users/LENOVO/PycharmProjects/net0_app/net0/core/dataloader.py), all historical baseline data for Scope 1, Scope 2, and standard Scope 3 categories is hardcoded directly inside Python functions as Pandas DataFrames.
- **Improvement**: Externalize this data into configuration files (e.g., CSV, JSON, YAML) or a database. This will decouple data updates from the calculation logic.

### 🧪 Absence of Automated Testing
- **Problem**: There are no unit tests, integration tests, or end-to-end tests in the codebase.
- **Improvement**: Set up `pytest` and add tests for utilities in [formula.py](file:///C:/Users/LENOVO/PycharmProjects/net0_app/net0/core/formula.py), scenario transitions in [scenario.py](file:///C:/Users/LENOVO/PycharmProjects/net0_app/net0/core/scenario.py), and routes in [app.py](file:///C:/Users/LENOVO/PycharmProjects/net0_app/app.py).

---

## 2. Calculation & Mathematical Logic Bugs

### 🚨 Bug 1: Scope 1/2 Energy Reduction Interaction Bug
- **Location**: [apply_renewable_thermal](file:///C:/Users/LENOVO/PycharmProjects/net0_app/net0/core/scenario.py#L6)
- **Description**: Replacing fossil fuel combustion with renewable thermal energy reduces the overall fossil fuel demand but does *not* reduce electricity demand. However, the current code reduces the overall `Total_Energy` of the facility. Because electricity demand is subsequently computed as `Total_Energy * Electricity_Share`, **applying renewable thermal energy causes the calculated electricity usage (and Scope 2 emissions) to incorrectly drop**!
- **Improvement**: Distinguish between thermal energy and electrical energy in the data structures, and reduce only the thermal fuel shares while keeping electricity untouched.

### 🚨 Bug 2: Missing Validation for Fuel Switch Shares
- **Location**: [fuel_conversion_matrix](file:///C:/Users/LENOVO/PycharmProjects/net0_app/net0/core/scenario.py#L21)
- **Description**: The conversion matrix allows users to switch fuel allocations. If a user sets multiple switches from the same base fuel that sum to more than 100%, the diagonal value `matrix[i][i]` becomes negative. This results in negative fuel shares, which breaks the physical realism of the simulation.
- **Improvement**: Add validation in the backend and frontend to ensure the sum of outbound conversions from any single fuel source never exceeds 100%.

### 🚨 Bug 3: Scope 3 Baseline Ignored Step 1 Production Target
- **Location**: [run_scope3](file:///C:/Users/LENOVO/PycharmProjects/net0_app/net0/scope/scope3/manager.py#L12)
- **Description**: Step 1 asks the user for a global `target_production` volume. This is used to project Scope 1 and Scope 2 energy CAGRs. However, [run_scope3](file:///C:/Users/LENOVO/PycharmProjects/net0_app/net0/scope/scope3/manager.py#L12) takes `target_production` but completely ignores it in its calculations. This means a user could double their vehicle production volume, but their Scope 3 baseline emissions (logistics, waste, use of sold products) would remain flat.
- **Improvement**: Scale the baseline activity levels of logistics (Cat 4 & 9) and use of sold products (Cat 11) relative to the global production volume CAGR.

---

## 3. Security, Input Validation & Stability Issues

### 💥 Uncaught Flask Server Crash on Empty Input
- **Location**: [app.py](file:///C:/Users/LENOVO/PycharmProjects/net0_app/app.py#L109)
- **Description**: When Category 11 (Sold Vehicles) is enabled in Scope 3, the user enters target units through text inputs. If they leave any segment field blank, `request.form.get()` returns an empty string `""`. The application tries to cast this directly via `int(request.form.get('cat11_lcv', 0))`, which immediately raises a `ValueError` and crashes the Flask server.
- **Improvement**: Implement input validation to verify numeric formats and fall back gracefully to historical defaults if left blank.

### 🔑 Hardcoded Flask Secret Key
- **Location**: [app.py](file:///C:/Users/LENOVO/PycharmProjects/net0_app/app.py#L10)
- **Description**: The secret key for signing cookies is hardcoded: `app.secret_key = 'ashok_leyland_net0_key'`.
- **Improvement**: Load the secret key from environment variables (e.g., `os.environ.get('FLASK_SECRET_KEY')`).

---

## 4. UI/UX & Data Visualization Improvements

### 🗺️ Missing Consolidated Net Zero Dashboard
- **Problem**: The application does not have a dashboard that combines Scope 1, Scope 2, and Scope 3 emissions into a single corporate-wide trajectory chart.
- **Improvement**: Add a "Consolidated Dashboard" page that aggregates simulations across all scopes to show the total net emissions path.

### 🎨 Visual Identity & Styling Polish
- **Problem**: The current visual styling uses basic Bootstrap 5 elements, default grey cards, and generic blue colors. It lacks a premium, modern design identity.
- **Improvement**: Update layouts, fonts (e.g. *Outfit* or *Inter*), add soft gradients/glassmorphism, and custom-theme the Plotly charts.
