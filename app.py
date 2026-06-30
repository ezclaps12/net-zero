from flask import Flask, render_template, request, session, redirect, url_for
from flask_session import Session
import pandas as pd
import plotly.express as px
from net0.core.dataloader import get_data_s1, get_data_s2
from net0.scope.scope1 import run_scope1
from net0.scope.scope2 import run_scope2
from net0.scope.scope3.manager import run_scope3

app = Flask(__name__)
app.secret_key = 'ashok_leyland_net0_key'

# Use server-side filesystem sessions instead of cookie-based sessions.
# Cookie sessions have a 4KB limit which the large ledger data exceeds,
# causing s1_inputs and s2_inputs to silently fail to persist.
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = '.flask_sessions'
app.config['SESSION_PERMANENT'] = False
Session(app)


def init_session_data():
    if 'initialized_ledger' not in session:
        session['baseline_year'] = 2024
        session['ledger_s1'] = [
            {'Year': 2021, 'Production': 100725, 'HSD_Liters': 5980000.0, 'CNG_kg': 560000.0, 'LPG_kg': 1350000.0, 'Propane_kg': 1350000.0, 'DA_Liters': 4700.0, 'Refrigerant_Emissions': 2481.63, 'Renewable_Thermal_Energy': 0.0},
            {'Year': 2022, 'Production': 128326, 'HSD_Liters': 7150000.0, 'CNG_kg': 820000.0, 'LPG_kg': 2030000.0, 'Propane_kg': 2200000.0, 'DA_Liters': 3200.0, 'Refrigerant_Emissions': 3287.76, 'Renewable_Thermal_Energy': 0.0},
            {'Year': 2023, 'Production': 192205, 'HSD_Liters': 5990000.0, 'CNG_kg': 750000.0, 'LPG_kg': 2240000.0, 'Propane_kg': 2110000.0, 'DA_Liters': 550.0, 'Refrigerant_Emissions': 3719.10, 'Renewable_Thermal_Energy': 0.0},
            {'Year': 2024, 'Production': 194555, 'HSD_Liters': 4849767.0, 'CNG_kg': 908441.0, 'LPG_kg': 2444540.0, 'Propane_kg': 2003420.0, 'DA_Liters': 23485.0, 'Refrigerant_Emissions': 3800.00, 'Renewable_Thermal_Energy': 0.0}
        ]
        session['ledger_s2'] = [
            {'Year': 2021, 'Production': 100725, 'Electricity_kWh': 246455556.0, 'Renewable_Share': 0.715, 'Grid_EF': 0.703},
            {'Year': 2022, 'Production': 128326, 'Electricity_kWh': 313594444.0, 'Renewable_Share': 0.581, 'Grid_EF': 0.715},
            {'Year': 2023, 'Production': 192205, 'Electricity_kWh': 306661111.0, 'Renewable_Share': 0.613, 'Grid_EF': 0.716},
            {'Year': 2024, 'Production': 194555, 'Electricity_kWh': 317052778.0, 'Renewable_Share': 0.698, 'Grid_EF': 0.727}
        ]
        for cid in [4, 5, 6, 7, 9]:
            session[f'ledger_s3_cat{cid}'] = get_default_s3_data(cid)
        session['initiatives'] = []
        session['initialized_ledger'] = True

    # Migration for sessions initialized with the old GJ values (value is less than 10M kWh)
    if 'ledger_s2' in session:
        s2 = session['ledger_s2']
        if len(s2) > 0 and any(float(x.get('Electricity_kWh', 0)) < 10000000.0 for x in s2):
            new_s2 = []
            for item in s2:
                kwh = float(item.get('Electricity_kWh', 0.0))
                if kwh < 10000000.0:
                    kwh = round(kwh * 1000 / 3.6, 2)
                item['Electricity_kWh'] = kwh
                new_s2.append(item)
            session['ledger_s2'] = new_s2


def get_default_s3_data(cat_id):
    if cat_id == 7:
        return [
            {'Year': 2021, 'Activity': 56560.0, 'EF': 0.073},
            {'Year': 2022, 'Activity': 160220.0, 'EF': 0.080},
            {'Year': 2023, 'Activity': 91650.0, 'EF': 0.078},
            {'Year': 2024, 'Activity': 76140.0, 'EF': 0.078}
        ]
    elif cat_id == 4:
        return [
            {'Year': 2021, 'Activity': 447090.0, 'EF': 0.0732},
            {'Year': 2022, 'Activity': 710350.0, 'EF': 0.0818},
            {'Year': 2023, 'Activity': 847870.0, 'EF': 0.0818},
            {'Year': 2024, 'Activity': 801000.0, 'EF': 0.0820}
        ]
    elif cat_id == 5:
        return [
            {'Year': 2021, 'Activity': 5000.0, 'EF': 0.1562},
            {'Year': 2022, 'Activity': 6160.0, 'EF': 0.0818},
            {'Year': 2023, 'Activity': 6630.0, 'EF': 0.0818},
            {'Year': 2024, 'Activity': 5770.0, 'EF': 0.0820}
        ]
    elif cat_id == 9:
        return [
            {'Year': 2021, 'Activity': 95750.0, 'EF': 0.0656},
            {'Year': 2022, 'Activity': 760950.0, 'EF': 0.0818},
            {'Year': 2023, 'Activity': 837050.0, 'EF': 0.0818},
            {'Year': 2024, 'Activity': 878890.0, 'EF': 0.0820}
        ]
    elif cat_id == 6:
        return [
            {'Year': 2021, 'Activity': 400.0, 'EF': 0.0568},
            {'Year': 2022, 'Activity': 2140.0, 'EF': 0.0818},
            {'Year': 2023, 'Activity': 260.0, 'EF': 0.0816},
            {'Year': 2024, 'Activity': 150.0, 'EF': 0.0845}
        ]
    return []


@app.before_request
def setup_defaults():
    init_session_data()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/dashboard')
def dashboard():
    if not session.get('initialized'):
        return redirect(url_for('setup_page'))

    s1_p = session.get('s1_inputs')
    s2_p = session.get('s2_inputs')
    s3_p = session.get('s3_inputs', {})

    import plotly.graph_objects as go

    # Only run scope calculations if the user has explicitly configured them.
    # Unconfigured scopes contribute 0 emissions to the dashboard.
    years_range = list(range(session.get('baseline_year', 2024), session['target_year'] + 1))
    empty_df = pd.DataFrame({'Year': years_range, 'Emissions': 0.0})

    # Run s1 only if user has configured it
    if s1_p is not None:
        s1_bau, s1_scene = run_scope1(session['target_year'], session['target_prod'], *s1_p,
                                      baseline_year=session.get('baseline_year', 2024),
                                      initiatives=session.get('initiatives', []))
    else:
        s1_bau, s1_scene = empty_df.copy(), empty_df.copy()

    # Run s2 only if user has configured it
    if s2_p is not None:
        # Only pass s1 data if scope1 was actually configured (empty_df lacks Total_Energy/Electricity columns)
        s1_for_s2 = s1_scene if s1_p is not None else None
        s2_bau, s2_scene = run_scope2(session['target_year'], session['target_prod'], *s2_p, s1=s1_for_s2,
                                      baseline_year=session.get('baseline_year', 2024),
                                      initiatives=session.get('initiatives', []))
    else:
        s2_bau, s2_scene = empty_df.copy(), empty_df.copy()

    # Run s3
    s3_inputs_converted = {int(k): v for k, v in s3_p.items()}
    s3_bau, s3_scene = run_scope3(session['target_year'], session['target_prod'], s3_inputs_converted,
                                  baseline_year=session.get('baseline_year', 2024))
    
    # Standarize and merge
    s1_bau_clean = s1_bau[['Year', 'Emissions']].rename(columns={'Emissions': 'Scope 1'})
    s1_scene_clean = s1_scene[['Year', 'Emissions']].rename(columns={'Emissions': 'Scope 1'})
    
    s2_bau_clean = s2_bau[['Year', 'Emissions']].rename(columns={'Emissions': 'Scope 2'})
    s2_scene_clean = s2_scene[['Year', 'Emissions']].rename(columns={'Emissions': 'Scope 2'})
    
    s3_bau_clean = s3_bau[['Year', 'Emissions']].rename(columns={'Emissions': 'Scope 3'})
    s3_scene_clean = s3_scene[['Year', 'Emissions']].rename(columns={'Emissions': 'Scope 3'})
    
    bau_merged = s1_bau_clean.merge(s2_bau_clean, on='Year', how='left')
    if not s3_bau_clean.empty:
        bau_merged = bau_merged.merge(s3_bau_clean, on='Year', how='left')
    else:
        bau_merged['Scope 3'] = 0.0
    bau_merged = bau_merged.fillna(0.0)
    bau_merged['Total'] = bau_merged['Scope 1'] + bau_merged['Scope 2'] + bau_merged['Scope 3']
    
    scene_merged = s1_scene_clean.merge(s2_scene_clean, on='Year', how='left')
    if not s3_scene_clean.empty:
        scene_merged = scene_merged.merge(s3_scene_clean, on='Year', how='left')
    else:
        scene_merged['Scope 3'] = 0.0
    scene_merged = scene_merged.fillna(0.0)
    scene_merged['Total'] = scene_merged['Scope 1'] + scene_merged['Scope 2'] + scene_merged['Scope 3']


    fig = go.Figure()
    
    # Net Zero Pathway lines
    fig.add_trace(go.Scatter(x=scene_merged['Year'], y=scene_merged['Total'], name='Scenario Total', line=dict(color='#10b981', width=4, shape='spline')))
    fig.add_trace(go.Scatter(x=bau_merged['Year'], y=bau_merged['Total'], name='BAU Total', line=dict(color='#ef4444', width=3, dash='dash', shape='spline')))
    
    fig.add_trace(go.Scatter(x=scene_merged['Year'], y=scene_merged['Scope 1'], name='Scope 1: Direct', line=dict(color='#f43f5e', width=2, shape='spline')))
    fig.add_trace(go.Scatter(x=scene_merged['Year'], y=scene_merged['Scope 2'], name='Scope 2: Electricity', line=dict(color='#3b82f6', width=2, shape='spline')))
    fig.add_trace(go.Scatter(x=scene_merged['Year'], y=scene_merged['Scope 3'], name='Scope 3: Value Chain', line=dict(color='#8b5cf6', width=2, shape='spline')))

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Outfit, sans-serif', color='#475569'),
        margin=dict(t=50, r=20, l=65, b=50),
        xaxis=dict(gridcolor='#f1f5f9', zerolinecolor='#e2e8f0', title='Year', tickmode='linear', dtick=1),
        yaxis=dict(gridcolor='#f1f5f9', zerolinecolor='#e2e8f0', title='Emissions (tCO2e)'),
        hovermode='closest',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    
    base_yr = session.get('baseline_year', 2024)
    target_yr = session['target_year']
    
    # Baseline scope emissions
    s1_base = scene_merged[scene_merged['Year'] == base_yr]['Scope 1'].values[0] if base_yr in scene_merged['Year'].values else 0.0
    s2_base = scene_merged[scene_merged['Year'] == base_yr]['Scope 2'].values[0] if base_yr in scene_merged['Year'].values else 0.0
    s3_base = scene_merged[scene_merged['Year'] == base_yr]['Scope 3'].values[0] if base_yr in scene_merged['Year'].values else 0.0
    
    s1_target = scene_merged[scene_merged['Year'] == target_yr]['Scope 1'].values[0] if target_yr in scene_merged['Year'].values else 0.0
    s2_target = scene_merged[scene_merged['Year'] == target_yr]['Scope 2'].values[0] if target_yr in scene_merged['Year'].values else 0.0
    s3_target = scene_merged[scene_merged['Year'] == target_yr]['Scope 3'].values[0] if target_yr in scene_merged['Year'].values else 0.0
    
    s1_bau_t = bau_merged[bau_merged['Year'] == target_yr]['Scope 1'].values[0] if target_yr in bau_merged['Year'].values else 0.0
    s2_bau_t = bau_merged[bau_merged['Year'] == target_yr]['Scope 2'].values[0] if target_yr in bau_merged['Year'].values else 0.0
    s3_bau_t = bau_merged[bau_merged['Year'] == target_yr]['Scope 3'].values[0] if target_yr in bau_merged['Year'].values else 0.0

    # Dynamic Pie Chart for baseline scope distribution
    pie_fig = go.Figure(data=[go.Pie(
        labels=['Scope 1: Direct', 'Scope 2: Electricity', 'Scope 3: Value Chain'],
        values=[s1_base, s2_base, s3_base],
        hole=0.4,
        marker=dict(colors=['#f43f5e', '#3b82f6', '#8b5cf6']),
        textinfo='percent'
    )])
    pie_fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Outfit, sans-serif', color='#475569'),
        margin=dict(t=20, r=10, l=10, b=10),
        showlegend=True,
        legend=dict(orientation='h', yanchor='top', y=-0.05, xanchor='center', x=0.5)
    )
    
    base_emissions = s1_base + s2_base + s3_base
    target_emissions = s1_target + s2_target + s3_target
    target_bau = s1_bau_t + s2_bau_t + s3_bau_t
    
    reduction_pct = ((base_emissions - target_emissions) / base_emissions * 100) if base_emissions > 0 else 0.0
    
    scope_data = {
        's1': {'base': s1_base, 'target': s1_target, 'bau': s1_bau_t},
        's2': {'base': s2_base, 'target': s2_target, 'bau': s2_bau_t},
        's3': {'base': s3_base, 'target': s3_target, 'bau': s3_bau_t}
    }
    
    return render_template('overview.html',
                           fig_json=fig.to_json(),
                           pie_json=pie_fig.to_json(),
                           base_emissions=base_emissions,
                           target_emissions=target_emissions,
                           target_bau=target_bau,
                           reduction_pct=reduction_pct,
                           scope_data=scope_data)


@app.route('/dashboard/setup', methods=['GET', 'POST'])
def setup_page():
    if request.method == 'POST':
        session['target_year'] = int(request.form.get('target_year'))
        session['target_prod'] = int(request.form.get('target_production'))
        session['initialized'] = True
        return redirect(url_for('dashboard'))
    return render_template('scopes.html')


@app.route('/dashboard/ledger', methods=['GET', 'POST'])
def ledger_page():
    if not session.get('initialized'):
        return redirect(url_for('setup_page'))

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'save_baseline':
            session['baseline_year'] = int(request.form.get('baseline_year', 2024))
            
        elif action == 'save_s1':
            years = request.form.getlist('s1_year[]')
            prod = request.form.getlist('s1_prod[]')
            hsd = request.form.getlist('s1_hsd[]')
            cng = request.form.getlist('s1_cng[]')
            lpg = request.form.getlist('s1_lpg[]')
            prop = request.form.getlist('s1_prop[]')
            da = request.form.getlist('s1_da[]')
            refr = request.form.getlist('s1_refr[]')
            
            ledger = []
            for y, p, h, c, l, pr, d, r in zip(years, prod, hsd, cng, lpg, prop, da, refr):
                ledger.append({
                    'Year': int(y),
                    'Production': int(p) if p else 0,
                    'HSD_Liters': float(h) if h else 0.0,
                    'CNG_kg': float(c) if c else 0.0,
                    'LPG_kg': float(l) if l else 0.0,
                    'Propane_kg': float(pr) if pr else 0.0,
                    'DA_Liters': float(d) if d else 0.0,
                    'Refrigerant_Emissions': float(r) if r else 0.0,
                    'Renewable_Thermal_Energy': 0.0
                })
            session['ledger_s1'] = ledger
            
        elif action == 'save_s2':
            years = request.form.getlist('s2_year[]')
            prod = request.form.getlist('s2_prod[]')
            kwh = request.form.getlist('s2_kwh[]')
            re_share = request.form.getlist('s2_re[]')
            ef = request.form.getlist('s2_ef[]')
            
            ledger = []
            for y, p, k, r, e in zip(years, prod, kwh, re_share, ef):
                ledger.append({
                    'Year': int(y),
                    'Production': int(p) if p else 0,
                    'Electricity_kWh': float(k) if k else 0.0,
                    'Renewable_Share': float(r) / 100.0 if r else 0.0,
                    'Grid_EF': float(e) if e else 0.727
                })
            session['ledger_s2'] = ledger
            
        elif action == 'add_year':
            new_yr = int(request.form.get('new_year'))
            if not any(x['Year'] == new_yr for x in session['ledger_s1']):
                last1 = session['ledger_s1'][-1].copy()
                last1['Year'] = new_yr
                last2 = session['ledger_s2'][-1].copy()
                last2['Year'] = new_yr
                
                s1_l = session['ledger_s1']
                s1_l.append(last1)
                session['ledger_s1'] = sorted(s1_l, key=lambda x: x['Year'])
                
                s2_l = session['ledger_s2']
                s2_l.append(last2)
                session['ledger_s2'] = sorted(s2_l, key=lambda x: x['Year'])
                
        return redirect(url_for('ledger_page'))

    ledger_display = []
    from net0.config.ef import CONVERSIONS
    for s1_r, s2_r in zip(session['ledger_s1'], session['ledger_s2']):
        y = s1_r['Year']
        
        em_hsd = (s1_r['HSD_Liters'] * CONVERSIONS['HSD']['EF']) / 1000
        em_cng = (s1_r['CNG_kg'] * CONVERSIONS['CNG']['EF']) / 1000
        em_lpg = (s1_r['LPG_kg'] * CONVERSIONS['LPG']['EF']) / 1000
        em_prop = (s1_r['Propane_kg'] * CONVERSIONS['Propane']['EF']) / 1000
        em_da = (s1_r['DA_Liters'] * CONVERSIONS['DA']['EF']) / 1000
        refr = s1_r['Refrigerant_Emissions']
        s1_em = em_hsd + em_cng + em_lpg + em_prop + em_da + refr
        
        kwh = s2_r['Electricity_kWh']
        grid_share = 1.0 - s2_r['Renewable_Share']
        s2_em = (kwh * grid_share * s2_r['Grid_EF']) / 1000
        
        ledger_display.append({
            'Year': y,
            'Production': s1_r['Production'],
            'HSD_Liters': s1_r['HSD_Liters'],
            'CNG_kg': s1_r['CNG_kg'],
            'LPG_kg': s1_r['LPG_kg'],
            'Propane_kg': s1_r['Propane_kg'],
            'DA_Liters': s1_r['DA_Liters'],
            'Refrigerant_Emissions': refr,
            'Electricity_kWh': kwh,
            'Renewable_Share': s2_r['Renewable_Share'] * 100,
            'Grid_EF': s2_r['Grid_EF'],
            's1_em': s1_em,
            's2_em': s2_em,
            'total_em': s1_em + s2_em
        })

    return render_template('ledger.html', ledger=ledger_display, baseline_year=session.get('baseline_year', 2024))


@app.route('/dashboard/planner', methods=['GET', 'POST'])
def planner_page():
    if not session.get('initialized'):
        return redirect(url_for('setup_page'))
        
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add_init':
            init = {
                'name': request.form.get('init_name'),
                'scope': request.form.get('init_scope'),
                'year': int(request.form.get('init_year')),
                'type': request.form.get('init_type'),
                'value': float(request.form.get('init_value', 0)),
                'val_type': request.form.get('init_val_type', 'percentage'),
                'fuel_from': request.form.get('init_fuel_from', ''),
                'fuel_to': request.form.get('init_fuel_to', '')
            }
            inits = session.get('initiatives', [])
            inits.append(init)
            session['initiatives'] = sorted(inits, key=lambda x: (x['year'], x['name']))
            
        elif action == 'delete_init':
            idx = int(request.form.get('init_idx'))
            inits = session.get('initiatives', [])
            if 0 <= idx < len(inits):
                inits.pop(idx)
            session['initiatives'] = inits
            
        return redirect(url_for('planner_page'))
        
    return render_template('planner.html', initiatives=session.get('initiatives', []), target_year=session['target_year'], target_prod=session['target_prod'])


@app.route('/dashboard/scope1', methods=['GET', 'POST'])
def scope1_page():
    if not session.get('initialized'): return redirect(url_for('setup_page'))
    form_data = session.get('s1_form_data', {'f_from': [], 'f_to': [], 'f_val': []})
    s1_bau_json, s1_scene_json = None, None

    if request.method == 'POST':
        form_data = request.form.to_dict()
        form_data['f_from'] = request.form.getlist('f_from[]')
        form_data['f_to'] = request.form.getlist('f_to[]')
        form_data['f_val'] = request.form.getlist('f_val[]')
        session['s1_form_data'] = form_data

        conversions = []
        for f, t, v in zip(form_data['f_from'], form_data['f_to'], form_data['f_val']):
            if v and str(v).strip():
                conversions.append([f, t, float(v) / 100])

        session['s1_inputs'] = [
            float(form_data.get('intensity', 0)) / 100, float(form_data.get('therm_re', 0)) / 100,
            float(form_data.get('elec', 0)) / 100, float(form_data.get('refr_growth', 0)) / 100,
            float(form_data.get('refr_red', 0)) / 100, conversions
        ]

        bau, scene = run_scope1(session['target_year'], session['target_prod'], *session['s1_inputs'],
                                baseline_year=session.get('baseline_year', 2024),
                                initiatives=session.get('initiatives', []))
        s1_bau_json = px.line(bau, x='Year', y='Emissions').to_json()
        s1_scene_json = px.line(scene, x='Year', y='Emissions').to_json()

    hist = px.line(get_data_s1(), x='Year', y='Total_Energy', markers=True).to_json()
    return render_template('scope1.html', hist_json=hist, s1_bau_json=s1_bau_json, s1_scenario_json=s1_scene_json,
                           form_data=form_data)


@app.route('/dashboard/scope2', methods=['GET', 'POST'])
def scope2_page():
    if not session.get('initialized'): return redirect(url_for('setup_page'))
    form_data = session.get('s2_form_data', {})
    s2_bau_json, s2_scene_json = None, None

    if request.method == 'POST':
        form_data = request.form.to_dict()
        session['s2_form_data'] = form_data
        session['s2_inputs'] = [float(form_data.get('intensity', 0)) / 100, float(form_data.get('renewable', 0)) / 100,
                                float(form_data.get('grid_ef', 0)) / 100]

        s1_p = session.get('s1_inputs', [0.0, 0.0, 0.0, 0.0, 0.0, []])
        _, s1_scene = run_scope1(session['target_year'], session['target_prod'], *s1_p,
                                 baseline_year=session.get('baseline_year', 2024),
                                 initiatives=session.get('initiatives', []))

        bau, scene = run_scope2(session['target_year'], session['target_prod'], *session['s2_inputs'], s1=s1_scene,
                                baseline_year=session.get('baseline_year', 2024),
                                initiatives=session.get('initiatives', []))
        s2_bau_json, s2_scene_json = px.line(bau, x='Year', y='Emissions').to_json(), px.line(scene, x='Year',
                                                                                              y='Emissions').to_json()

    hist = px.line(get_data_s2(), x='Year', y='Electricity_kWh', markers=True).to_json()
    return render_template('scope2.html', hist_json=hist, s2_bau_json=s2_bau_json, s2_scenario_json=s2_scene_json,
                           form_data=form_data)


@app.route('/dashboard/scope3', methods=['GET', 'POST'])
def scope3_page():
    if not session.get('initialized'): return redirect(url_for('setup_page'))
    form_data = session.get('s3_form_data', {})
    s3_bau_json, s3_scene_json = None, None

    if request.method == 'POST':
        form_data = request.form.to_dict()
        all_inputs = {}
        for cid in [4, 5, 6, 7, 9]:
            if request.form.get(f'cat{cid}_enabled'):
                all_inputs[cid] = {"activity_slider": float(request.form.get(f'cat{cid}_act', 0)) / 100,
                                   "ef_slider": float(request.form.get(f'cat{cid}_ef', 0)) / 100}
        if request.form.get('cat11_enabled'):
            for seg in ['lcv', 'buses', 'trucks']:
                form_data[f'{seg}_from'] = request.form.getlist(f'{seg}_from[]')
                form_data[f'{seg}_to'] = request.form.getlist(f'{seg}_to[]')
                form_data[f'{seg}_val'] = request.form.getlist(f'{seg}_val[]')

            def get_c(s):
                return [(f, t, float(v) / 100) for f, t, v in
                        zip(form_data[f'{s}_from'], form_data[f'{s}_to'], form_data[f'{s}_val']) if v]

            all_inputs[11] = {"activity_slider_lcv": int(request.form.get('cat11_lcv', 0)) if request.form.get('cat11_lcv') else 0,
                              "activity_slider_buses": int(request.form.get('cat11_buses', 0)) if request.form.get('cat11_buses') else 0,
                              "activity_slider_trucks": int(request.form.get('cat11_trucks', 0)) if request.form.get('cat11_trucks') else 0,
                              "conversions_lcv": get_c('lcv'), "conversions_buses": get_c('buses'),
                              "conversions_trucks": get_c('trucks'),
                              "ef_slider": float(request.form.get('cat11_ef', 0)) / 100}

        session['s3_inputs'] = {str(k): v for k, v in all_inputs.items()}
        session['s3_form_data'] = form_data
        bau, scene = run_scope3(session['target_year'], session['target_prod'], all_inputs,
                                baseline_year=session.get('baseline_year', 2024))
        bau['Year'] = bau['Year'].astype(int)
        scene['Year'] = scene['Year'].astype(int)
        s3_bau_json = px.line(bau, x='Year', y='Emissions').update_xaxes(type='linear').to_json()
        s3_scene_json = px.line(scene, x='Year', y='Emissions').update_xaxes(type='linear').to_json()

    return render_template('scope3.html', s3_bau_json=s3_bau_json, s3_scenario_json=s3_scene_json, form_data=form_data)


@app.route('/dashboard/reset')
def reset_session():
    session.clear()
    return redirect(url_for('setup_page'))


if __name__ == '__main__':
    app.run(debug=True)