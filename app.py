from flask import Flask, render_template, request, session, redirect, url_for
import pandas as pd
import plotly.express as px
from net0.core.dataloader import get_data_s1, get_data_s2
from net0.scope.scope1 import run_scope1
from net0.scope.scope2 import run_scope2
from net0.scope.scope3.manager import run_scope3

app = Flask(__name__)
app.secret_key = 'ashok_leyland_net0_key'


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if request.method == 'POST':
        session['target_year'] = int(request.form.get('target_year'))
        session['target_prod'] = int(request.form.get('target_production'))
        session['initialized'] = True
        return redirect(url_for('dashboard'))
    return render_template('scopes.html')


@app.route('/dashboard/scope1', methods=['GET', 'POST'])
def scope1_page():
    if not session.get('initialized'): return redirect(url_for('dashboard'))
    form_data = session.get('s1_form_data', {'f_from': [], 'f_to': [], 'f_val': []})
    s1_bau_json, s1_scene_json = None, None

    if request.method == 'POST':
        form_data = request.form.to_dict()
        form_data['f_from'] = request.form.getlist('f_from[]')
        form_data['f_to'] = request.form.getlist('f_to[]')
        form_data['f_val'] = request.form.getlist('f_val[]')
        session['s1_form_data'] = form_data

        # Build conversions list: (From, To, Value/100)
        conversions = []
        for f, t, v in zip(form_data['f_from'], form_data['f_to'], form_data['f_val']):
            if v and str(v).strip():
                conversions.append([f, t, float(v) / 100])  # Use list instead of tuple for JSON safety

        session['s1_inputs'] = [
            float(form_data.get('intensity', 0)) / 100, float(form_data.get('therm_re', 0)) / 100,
            float(form_data.get('elec', 0)) / 100, float(form_data.get('refr_growth', 0)) / 100,
            float(form_data.get('refr_red', 0)) / 100, conversions
        ]

        bau, scene = run_scope1(session['target_year'], session['target_prod'], *session['s1_inputs'])
        s1_bau_json = px.line(bau, x='Year', y='Emissions').to_json()
        s1_scene_json = px.line(scene, x='Year', y='Emissions').to_json()

    hist = px.line(get_data_s1(), x='Year', y='Total_Energy', markers=True).to_json()
    return render_template('scope1.html', hist_json=hist, s1_bau_json=s1_bau_json, s1_scenario_json=s1_scene_json,
                           form_data=form_data)


@app.route('/dashboard/scope2', methods=['GET', 'POST'])
def scope2_page():
    if not session.get('initialized'): return redirect(url_for('dashboard'))
    form_data = session.get('s2_form_data', {})
    s2_bau_json, s2_scene_json = None, None

    if request.method == 'POST':
        form_data = request.form.to_dict()
        session['s2_form_data'] = form_data
        session['s2_inputs'] = [float(form_data.get('intensity', 0)) / 100, float(form_data.get('renewable', 0)) / 100,
                                float(form_data.get('grid_ef', 0)) / 100]

        s1_p = session.get('s1_inputs', [0.0, 0.0, 0.0, 0.0, 0.0, []])
        _, s1_scene = run_scope1(session['target_year'], session['target_prod'], *s1_p)

        bau, scene = run_scope2(session['target_year'], session['target_prod'], *session['s2_inputs'], s1=s1_scene)
        s2_bau_json, s2_scene_json = px.line(bau, x='Year', y='Emissions').to_json(), px.line(scene, x='Year',
                                                                                              y='Emissions').to_json()

    hist = px.line(get_data_s2(), x='Year', y='Total_Energy', markers=True).to_json()
    return render_template('scope2.html', hist_json=hist, s2_bau_json=s2_bau_json, s2_scenario_json=s2_scene_json,
                           form_data=form_data)


@app.route('/dashboard/scope3', methods=['GET', 'POST'])
def scope3_page():
    if not session.get('initialized'): return redirect(url_for('dashboard'))
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

            all_inputs[11] = {"activity_slider_lcv": int(request.form.get('cat11_lcv', 0)),
                              "activity_slider_buses": int(request.form.get('cat11_buses', 0)),
                              "activity_slider_trucks": int(request.form.get('cat11_trucks', 0)),
                              "conversions_lcv": get_c('lcv'), "conversions_buses": get_c('buses'),
                              "conversions_trucks": get_c('trucks'),
                              "ef_slider": float(request.form.get('cat11_ef', 0)) / 100}

        session['s3_inputs'] = {str(k): v for k, v in all_inputs.items()}  # Store as str keys (JSON-safe)
        session['s3_form_data'] = form_data
        bau, scene = run_scope3(session['target_year'], session['target_prod'], all_inputs)
        bau['Year'] = bau['Year'].astype(int)
        scene['Year'] = scene['Year'].astype(int)
        s3_bau_json = px.line(bau, x='Year', y='Emissions').update_xaxes(type='linear').to_json()
        s3_scene_json = px.line(scene, x='Year', y='Emissions').update_xaxes(type='linear').to_json()

    return render_template('scope3.html', s3_bau_json=s3_bau_json, s3_scenario_json=s3_scene_json, form_data=form_data)





@app.route('/dashboard/reset')
def reset_session():
    session.clear()
    return redirect(url_for('dashboard'))


if __name__ == '__main__':
    app.run(debug=True)