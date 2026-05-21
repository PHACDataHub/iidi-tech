import base64, io, os
import pandas as pd
import numpy as np
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go

# ─────────────────────────── CONSTANTS ───────────────────────────
JUR_COL = '2.0: Please indicate which jurisdiction you are representing'
UNKNOWN_JUR = 'No Jurisdiction'

PROVINCE_SHORT = {
    'British Columbia': 'BC', 'Alberta': 'AB', 'Saskatchewan': 'SK',
    'Manitoba': 'MB', 'Ontario': 'ON', 'Quebec': 'QC', 'Québec': 'QC',
    'New Brunswick': 'NB', 'Nova Scotia': 'NS', 'Prince Edward Island': 'PEI',
    'Newfoundland and Labrador': 'NL', 'Northwest Territories': 'NWT',
    'Nunavut': 'NU', 'Yukon': 'YT', UNKNOWN_JUR: 'N/A',
}

def short(name):
    return PROVINCE_SHORT.get(str(name).strip(), str(name)[:3].upper())

BLUE   = '#1F4E79'; MID    = '#2E75B6'; LIGHT  = '#D6E4F0'
GREEN  = '#375623'; LGREEN = '#D5E8D4'; ORANGE = '#C55A11'
RED    = '#C00000'; GREY   = '#595959'; LGREY  = '#F2F2F2'
WHITE  = '#FFFFFF'

PALETTE = ['#1F4E79','#C55A11','#375623','#7030A0','#1f6b4e',
           '#8B3A3A','#2E6B8A','#5C4A1E','#4A235A','#1A5276','#888888']

# ─────────────────────────── SCORING ───────────────────────────
def score_api_protocol(rest, soap, amqp, other):
    if pd.notna(rest)  and rest  == 1: return 2
    if pd.notna(soap)  and soap  == 1: return 2
    if pd.notna(amqp)  and amqp  == 1: return 2
    if pd.notna(other) and str(other).strip() != '': return -2
    return -2

def score_auth(saml, oauth, other):
    if pd.notna(saml)  and saml  == 1: return 2
    if pd.notna(oauth) and oauth == 1: return 2
    if pd.notna(other) and str(other).strip() != '':
        other_upper = str(other).upper()
        if 'SAML' in other_upper or 'OAUTH' in other_upper or 'OIDC' in other_upper:
            return 2
        return -2
    return -2

def score_10c(no_val, not_sure, yes_val):
    if pd.notna(yes_val) and str(yes_val).strip() not in ['','0','nan','0.0']:
        try:
            if float(yes_val) != 0: return 2
        except: return 2
    if pd.notna(no_val)   and no_val   == 1: return -2
    if pd.notna(not_sure) and not_sure == 1: return -2
    return -2

def score_row(row):
    q2 = str(row.get('4: 2. Does your jurisdiction have an official provincial/territorial immunization registry/repository?','')).strip()
    q2_dcc = q2_oc = 2 if q2 == 'Yes' else -2

    q3 = str(row.get('5: 3. Is your registry/repository implemented using Panorama?','')).strip()
    q3_dcc = q3_oc = 2 if q3=='Yes' else (-2 if q3=='No' else 0)

    q5 = str(row.get('9: 5. Where is your immunization registry/repository hosted?','')).strip()
    q5_dcc = q5_oc = 2 if q5=='Cloud' else (-2 if q5.lower() in ['on-premise','hybrid'] else 0)

    audit   = row.get('10: 6a. Is there Auditing of Logins in place for all registry/repository access?','')
    logging = row.get('11: 6b. Is there logging of user activities in place for all registry/repository transactions?','')
    q6_dcc  = 0
    q6_oc   = 2 if (str(audit).strip()=='Yes' and str(logging).strip()=='Yes') else -2

    q7 = str(row.get('12: 7. To ensure reliability and availability of data in the registry/repository, are there backups and mechanisms for disaster recovery?','')).strip()
    q7_dcc = 0; q7_oc = 2 if q7=='Yes' else -2

    q10 = str(row.get('15: 9. Does your registry/repository have externally accessible Application Programming Interfaces (API) covering functionality needed to access and exchange immunization data?','')).strip()
    if q10 == 'No':
        q10_dcc = q10_oc = -2
    elif q10 == 'Yes':
        s10a = score_api_protocol(row.get('16: REST'), row.get('16: SOAP'), row.get('16: AMQP'), row.get('16: Other, please specify'))
        s10b = score_auth(row.get('17: SAML'), row.get('17: OAuth'), row.get('17: Other, please specify'))
        s10c = score_10c(row.get('18: No '), row.get('18: No sure'), row.get('18: Yes'))
        q10_dcc = q10_oc = min(s10a, s10b, s10c)
    else:
        q10_dcc = q10_oc = 0

    q14  = str(row.get('24: 14. Are you currently upgrading or replacing any components of your immunization registry/repository or its technical ecosystem? (e.g., hosting environment, data exchange standards, interfaces with EMRs/EHRs, or other major system changes that will impact immunization data collection and sharing)','')).strip()
    q14a = str(row.get('25: 14a. If not, have any decisions or plans being made towards future upgrading or replacing of any components of your immunization registry/repository or its technical ecosystem?','')).strip()
    if q14 == 'Yes':    q14_dcc=q14_oc=2; q14a_dcc=q14a_oc=0
    elif q14a == 'Yes': q14_dcc=q14_oc=0; q14a_dcc=q14a_oc=2
    else:               q14_dcc=q14_oc=0; q14a_dcc=q14a_oc=0

    any_yes = any([
        pd.notna(row.get('26: Yes: PS-CA')) and row.get('26: Yes: PS-CA')==1,
        pd.notna(row.get('26: Yes: Pan-Canadian Health Data Content Framework')) and row.get('26: Yes: Pan-Canadian Health Data Content Framework')==1,
        pd.notna(row.get('26: Yes: CA:FeX ')) and row.get('26: Yes: CA:FeX ')==1,
    ])
    q16_dcc = q16_oc = 2 if any_yes else 0

    dcc_s = q2_dcc+q3_dcc+q5_dcc+q6_dcc+q7_dcc+q10_dcc+q14_dcc+q14a_dcc+q16_dcc
    oc_s  = q2_oc +q3_oc +q5_oc +q6_oc +q7_oc +q10_oc +q14_oc +q14a_oc +q16_oc
    return dcc_s, oc_s

def readiness_band(dcc_s, oc_s):
    avg = (dcc_s + oc_s) / 2
    if avg >= 8: return 'High'
    if avg >= 4: return 'Moderate'
    if avg >= 0: return 'Low'
    return 'Very Low'

# ─────────────────────────── DEDUPLICATION ───────────────────────────
def deduplicate(df):
    """
    Same respondent + same jurisdiction → keep latest only.
    Different respondents + same jurisdiction → keep all.
    No jurisdiction → fill with UNKNOWN_JUR sentinel so they still appear.
    """
    df = df.copy()
    df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
    # Fill missing jurisdiction with sentinel
    df[JUR_COL] = df[JUR_COL].fillna(UNKNOWN_JUR)
    # Sort by date, dedup on (Respondent, Jurisdiction) keeping latest
    df = (df.sort_values('Date')
            .drop_duplicates(subset=['Respondent', JUR_COL], keep='last'))
    df['Date'] = df['Date'].dt.strftime('%d/%m/%Y %H:%M:%S').fillna('')
    return df.reset_index(drop=True)

def calculate_scores(df):
    records = []
    jur_color_idx = {}
    color_counter = [0]

    for _, row in df.iterrows():
        jur = str(row.get(JUR_COL, UNKNOWN_JUR)).strip()

        # Skip scoring for unknown jurisdiction rows
        if jur == UNKNOWN_JUR:
            continue

        dcc_val, oc_val = score_row(row)
        respondent = str(row.get('Respondent', '')).strip()

        if jur not in jur_color_idx:
            jur_color_idx[jur] = color_counter[0]
            color_counter[0] += 1

        records.append({
            'Jurisdiction': jur,
            'Short': short(jur),
            'Respondent': respondent,
            'Data Connection Complexity': dcc_val,
            'Operational Complexity': oc_val,
            'Readiness Band': readiness_band(dcc_val, oc_val),
            '_color_idx': jur_color_idx[jur],
        })

    scores = pd.DataFrame(records)
    if scores.empty:
        return scores

    # Apply jitter to overlapping points so all are visible
    scores = apply_jitter(scores)
    return scores

def apply_jitter(scores):
    """
    For rows that share the exact same (DCC, OC) coordinates,
    spread them in a small arc so each bubble is visible.
    Jitter is small enough to not mislead (< 0.4 units).
    """
    scores = scores.copy()
    scores['_x'] = scores['Data Connection Complexity'].astype(float)
    scores['_y'] = scores['Operational Complexity'].astype(float)

    coord_groups = scores.groupby(['_x', '_y'])
    for (x, y), idx in coord_groups.groups.items():
        n = len(idx)
        if n == 1:
            continue
        # Spread in a circle of radius 0.35 around the true point
        radius = 0.35
        for i, row_idx in enumerate(idx):
            angle = (2 * np.pi * i) / n
            scores.at[row_idx, '_x'] = x + radius * np.cos(angle)
            scores.at[row_idx, '_y'] = y + radius * np.sin(angle)

    return scores

# ─────────────────────────── HELPERS ───────────────────────────────
def _lighten(hex_color, factor=0.45):
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    return f'#{int(r+(255-r)*factor):02x}{int(g+(255-g)*factor):02x}{int(b+(255-b)*factor):02x}'

# ─────────────────────────── BUBBLE CHART ───────────────────────────
def create_bubble_chart(scores):
    fig = go.Figure()

    if scores.empty:
        fig.add_annotation(text="Upload a CSV or Excel file to get started.",
                           xref="paper", yref="paper", x=0.5, y=0.5,
                           showarrow=False, font=dict(size=14, color=GREY))
        fig.update_layout(plot_bgcolor=WHITE, paper_bgcolor=WHITE, height=560)
        return fig

    max_abs_x = max(np.ceil(scores['Data Connection Complexity'].abs().max() * 1.3), 5)
    max_abs_y = max(np.ceil(scores['Operational Complexity'].abs().max() * 1.3), 5)

    # Quadrant shading
    for x0, y0, x1, y1, color, label, lx, ly in [
        (-max_abs_x, 0,          0,         max_abs_y, 'rgba(255,242,204,0.22)', 'Moderate DCC\nHigh OC',    -max_abs_x*0.85, max_abs_y*0.88),
        (0,          0,          max_abs_x, max_abs_y, 'rgba(213,232,212,0.22)', 'High DCC\nHigh OC',         max_abs_x*0.75,  max_abs_y*0.88),
        (-max_abs_x, -max_abs_y, 0,         0,         'rgba(252,228,214,0.22)', 'Low DCC\nLow OC',          -max_abs_x*0.85, -max_abs_y*0.88),
        (0,          -max_abs_y, max_abs_x, 0,         'rgba(244,204,204,0.22)', 'High DCC\nLow OC',          max_abs_x*0.75, -max_abs_y*0.88),
    ]:
        fig.add_shape(type='rect', x0=x0, y0=y0, x1=x1, y1=y1,
                      fillcolor=color, line_width=0, layer='below')

    fig.add_hline(y=0, line=dict(color='#BBBBBB', dash='dash', width=1))
    fig.add_vline(x=0, line=dict(color='#BBBBBB', dash='dash', width=1))

    for _, row in scores.iterrows():
        color = PALETTE[int(row['_color_idx']) % len(PALETTE)]
        x_pos = row.get('_x', row['Data Connection Complexity'])
        y_pos = row.get('_y', row['Operational Complexity'])
        true_x = row['Data Connection Complexity']
        true_y = row['Operational Complexity']
        jur_full = row['Jurisdiction']
        resp = row.get('Respondent', '')

        # Show connector line from jittered pos to true position if jittered
        if abs(x_pos - true_x) > 0.01 or abs(y_pos - true_y) > 0.01:
            fig.add_shape(type='line',
                x0=true_x, y0=true_y, x1=x_pos, y1=y_pos,
                line=dict(color=color, width=1, dash='dot'), layer='below')

        hover = (
            f"<b>{jur_full}</b><br>"
            f"DCC: {true_x:.0f} &nbsp; OC: {true_y:.0f}<br>"
            f"Readiness: {row['Readiness Band']}<br>"
            f"Respondent: {resp}"
            "<extra></extra>"
        )

        fig.add_trace(go.Scatter(
            x=[x_pos], y=[y_pos],
            mode='markers+text',
            marker=dict(size=54, color=color,
                        line=dict(width=1.5, color='rgba(255,255,255,0.5)'),
                        opacity=0.93),
            text=[row['Short']],
            textposition='middle center',
            textfont=dict(color=WHITE, size=12, family='Arial Black'),
            name=jur_full,
            hovertemplate=hover,
            showlegend=True,
        ))

    fig.update_layout(
        xaxis=dict(
            title='Data Connection Complexity →', zeroline=False,
            gridcolor='#EEEEEE', range=[-max_abs_x, max_abs_x],
            title_font=dict(size=12), tickfont=dict(size=11),
        ),
        yaxis=dict(
            title='Operational Complexity →', zeroline=False,
            gridcolor='#EEEEEE', range=[-max_abs_y, max_abs_y],
            title_font=dict(size=12), tickfont=dict(size=11),
        ),
        plot_bgcolor=WHITE, paper_bgcolor=WHITE,
        legend=dict(
            title='Jurisdiction', font=dict(size=11),
            bgcolor='rgba(255,255,255,0.9)', bordercolor=LIGHT, borderwidth=1,
            x=1.01, xanchor='left', y=1, yanchor='top',
        ),
        height=600,
        margin=dict(l=60, r=180, t=30, b=60),
        hovermode='closest',
    )
    return fig

# ─────────────────────────── SECTION DEFS ───────────────────────────
QUESTION_SECTIONS = [
    ('Respondent & Jurisdiction',   ['Respondent','Date','1:','2.0:']),
    ('Q1 – Information Systems',    ['3:']),
    ('Q2 – Registry Existence',     ['4:']),
    ('Q3 – Panorama',               ['5:','6:','7:']),
    ('Q4 – Immunization Capture',   ['8.']),
    ('Q5 – Hosting',                ['9:']),
    ('Q6 – Security & Logging',     ['10:','11:']),
    ('Q7 – Backup & Recovery',      ['12:']),
    ('Q8 – Citizen Access',         ['13:','14:']),
    ('Q9 – API & Protocols',        ['15:','16:','17:','18:']),
    ('Q10 – System Integration',    ['19:','20:','21:']),
    ('Q11 – Standards',             ['22:']),
    ('Q12 – Data Sharing',          ['23:']),
    ('Q13–14 – Upgrades & Roadmap', ['24:','25:','26:']),
    ('Q15–16 – Data Quality',       ['27:','28:']),
    ('Q17–18 – Patient Updates',    ['29:','30:','31:']),
    ('Q19–21 – Governance',         ['32:','33.','34.']),
    ('Q22–25 – Admin & Policies',   ['35:','36:','37:','38:']),
]

def assign_section(col):
    for label, prefixes in QUESTION_SECTIONS:
        for pfx in prefixes:
            if col.startswith(pfx): return label
    return 'Other'

def get_checkbox_label(col):
    parts = col.split(':',1)
    return parts[1].strip() if len(parts)==2 and parts[1].strip() else col

# ─────────────────────────── VIEWER ───────────────────────────────
def _field_row(label, val_cells, is_diff, rows_list):
    label_el = html.Div(label, style={
        'flex':'0 0 30%','fontSize':12,'color':'#2E75B6',
        'fontWeight':'600','wordBreak':'break-word','paddingTop':2,
    })
    if is_diff:
        val_el = html.Div([
            html.Div(cell, style={
                'flex':1,
                'borderLeft':f'3px solid {rows_list[i][2]}',
                'paddingLeft':8,
                'marginLeft': 4 if i > 0 else 0,
            }) for i, cell in enumerate(val_cells)
        ], style={'display':'flex','flex':1,'gap':8})
    else:
        val_el = html.Div(val_cells[0], style={'flex':1,'fontSize':12,'color':'#111','wordBreak':'break-word'})
    return html.Div([label_el, val_el], style={
        'display':'flex','padding':'7px 14px',
        'borderBottom':f'1px solid #F0F4F8','gap':12,'alignItems':'flex-start',
    })

def render_viewer(rows_list, raw_df, selected_sections):
    if not rows_list:
        return html.Div("Select a jurisdiction to view responses.",
                        style={'color':GREY,'padding':20,'fontStyle':'italic','fontSize':13})

    is_diff = len(rows_list) > 1

    binary_cols = set()
    for col in raw_df.columns:
        vals = raw_df[col].dropna().unique()
        if len(vals) <= 2 and all(v in [0,1,0.0,1.0] for v in vals):
            binary_cols.add(col)

    sections_order, sections_map = [], {}
    for col in raw_df.columns:
        sec = assign_section(col)
        if sec not in sections_map:
            sections_map[sec] = []
            sections_order.append(sec)
        sections_map[sec].append(col)

    if selected_sections:
        sections_order = [s for s in sections_order if s in selected_sections]

    cards = []
    for sec in sections_order:
        cols = sections_map.get(sec, [])
        row_els = []
        rendered_bin_groups = set()

        for col in cols:
            if col in binary_cols:
                prefix = col.split(':')[0].strip()
                gkey = (sec, prefix)
                if gkey in rendered_bin_groups: continue
                rendered_bin_groups.add(gkey)
                group_members = [c for c in cols if c in binary_cols and c.split(':')[0].strip()==prefix]

                val_cells = []
                for (row_s, suffix, accent) in rows_list:
                    checked = []
                    for c in group_members:
                        v = row_s.get(c)
                        try:
                            if pd.notna(v) and float(v)==1.0:
                                checked.append(get_checkbox_label(c))
                        except: pass
                    if checked:
                        cell = html.Div([
                            html.Span(c, style={
                                'display':'inline-block','padding':'2px 8px',
                                'borderRadius':10,'fontSize':11,'fontWeight':'600',
                                'background':_lighten(accent, 0.75),
                                'color':accent,
                                'border':f'1px solid {_lighten(accent, 0.4)}',
                                'margin':'2px 3px 2px 0',
                            }) for c in checked
                        ], style={'display':'flex','flexWrap':'wrap','gap':2})
                    else:
                        cell = html.Span("—", style={'fontSize':12,'color':'#bbb','fontStyle':'italic'})
                    val_cells.append(cell)

                row_els.append(_field_row(f"Q{prefix} (check all)", val_cells, is_diff, rows_list))

            else:
                parts = col.split(':',1)
                clean_label = parts[1].strip() if len(parts)==2 else col

                val_cells = []
                for (row_s, suffix, accent) in rows_list:
                    v = row_s.get(col)
                    if pd.isna(v) or str(v).strip() in ['','nan']:
                        cell = html.Span("—", style={'fontSize':12,'color':'#ccc','fontStyle':'italic'})
                    else:
                        cell = html.Span(str(v), style={'fontSize':12,'color':'#111','wordBreak':'break-word'})
                    val_cells.append(cell)

                # Highlight diffs
                if is_diff and len(val_cells)==2:
                    v0 = str(rows_list[0][0].get(col,'')).strip()
                    v1 = str(rows_list[1][0].get(col,'')).strip()
                    neither_empty = not (v0 in ['','nan'] and v1 in ['','nan'])
                    if v0 != v1 and neither_empty:
                        val_cells = [
                            html.Div(val_cells[0], style={'background':'#FFF9E6','borderRadius':4,'padding':'2px 4px'}),
                            html.Div(val_cells[1], style={'background':'#FFF9E6','borderRadius':4,'padding':'2px 4px'}),
                        ]

                row_els.append(_field_row(clean_label, val_cells, is_diff, rows_list))

        if row_els:
            cards.append(html.Div([
                html.Div(sec, style={
                    'background':'#EDF4FB','padding':'6px 14px',
                    'fontSize':11,'fontWeight':'700','color':BLUE,
                    'textTransform':'uppercase','letterSpacing':'0.04em',
                    'borderBottom':f'1px solid {LIGHT}',
                }),
                html.Div(row_els),
            ], style={
                'border':f'1px solid {LIGHT}','borderLeft':f'4px solid {BLUE}',
                'borderRadius':6,'marginBottom':8,'background':WHITE,'overflow':'hidden',
            }))

    return html.Div(cards) if cards else html.Div("No sections selected.", style={'color':GREY,'padding':16})

# ─────────────────────────── PARSE / LOAD ───────────────────────────
def parse_upload(contents, filename):
    _, cs = contents.split(',')
    decoded = base64.b64decode(cs)
    if filename.lower().endswith(('.xlsx','.xls')):
        return pd.read_excel(io.BytesIO(decoded))
    try:    return pd.read_csv(io.StringIO(decoded.decode('utf-8')))
    except: return pd.read_csv(io.StringIO(decoded.decode('latin-1')))

DEFAULT_CSV = os.environ.get('SURVEY_CSV', '')

def try_load_default():
    if DEFAULT_CSV and os.path.exists(DEFAULT_CSV):
        try:
            return pd.read_excel(DEFAULT_CSV) if DEFAULT_CSV.lower().endswith(('.xlsx','.xls')) \
                   else pd.read_csv(DEFAULT_CSV)
        except Exception: pass
    return pd.DataFrame()

def prepare_data(raw_df):
    if raw_df.empty:
        empty = pd.DataFrame(columns=[
            'Jurisdiction','Short','Respondent',
            'Data Connection Complexity','Operational Complexity',
            'Readiness Band','_color_idx','_x','_y',
        ])
        return raw_df, empty
    clean = deduplicate(raw_df)
    scores = calculate_scores(clean)
    return clean, scores

initial_raw, initial_scores = prepare_data(try_load_default())

# ─────────────────────────── LAYOUT ───────────────────────────────
app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server

@server.route('/healthcheck')
def healthcheck():
    return 'ok', 200

def build_section_filter(sections_present):
    options = [{'label': s, 'value': s} for s in sections_present]
    return html.Details([
        html.Summary("⚙ Filter question sections", style={
            'cursor':'pointer','fontWeight':'600','color':BLUE,'fontSize':13,
            'padding':'7px 12px','backgroundColor':'#EDF4FB',
            'borderRadius':'5px 5px 0 0','listStyle':'none','userSelect':'none',
        }),
        html.Div([
            html.Span("Select which sections to display:", style={
                'fontSize':11,'color':GREY,'display':'block','marginBottom':6,
            }),
            dcc.Checklist(
                id='section-checklist',
                options=options,
                value=[s['value'] for s in options],
                labelStyle={'display':'inline-flex','alignItems':'center',
                            'marginRight':14,'marginBottom':4,
                            'fontSize':12,'cursor':'pointer','color':'#222'},
                inputStyle={'marginRight':4,'accentColor':BLUE},
            ),
        ], style={'padding':'10px 14px','border':f'1px solid {LIGHT}',
                  'borderTop':'none','borderRadius':'0 0 5px 5px','background':'#FAFCFF'}),
    ], style={'border':f'1px solid {LIGHT}','borderRadius':6,'marginBottom':12})

app.layout = html.Div([
    html.H1("PT Readiness Dashboard",
            style={'color':BLUE,'textAlign':'center','fontFamily':'Arial',
                   'fontSize':22,'marginBottom':16,'marginTop':12}),

    dcc.Upload(id='upload-data',
               children=html.Div(['Drag & drop or ', html.A('select a CSV / Excel file')]),
               style={'width':'100%','height':'50px','lineHeight':'50px',
                      'borderWidth':'1.5px','borderStyle':'dashed','borderRadius':6,
                      'textAlign':'center','marginBottom':16,'color':GREY,
                      'backgroundColor':'#FAFAFA','fontSize':13},
               multiple=False),

    dcc.Store(id='scores-store',   data=initial_scores.to_json(date_format='iso', orient='split')),
    dcc.Store(id='raw-data-store', data=initial_raw.to_json(date_format='iso', orient='split')),

    # ── VIEWER ──────────────────────────────────────────────────────
    html.H3("Survey Response Viewer",
            style={'color':BLUE,'marginTop':4,'marginBottom':8,'fontFamily':'Arial','fontSize':16}),
    html.Div([
        html.Div([
            html.Label("Jurisdiction:", style={'fontWeight':'bold','marginRight':8,'fontSize':13,'color':GREY}),
            dcc.Dropdown(
                id='raw-jurisdiction-dropdown',
                options=[{'label':j,'value':j} for j in (
                    initial_raw[JUR_COL].unique() if not initial_raw.empty else []
                )],
                value=None, placeholder="Choose a jurisdiction...",
                clearable=False,
                style={'width':'320px','display':'inline-block','fontSize':13},
            ),
        ], style={'marginBottom':10}),
        html.Div(id='section-filter-container'),
    ], style={'fontFamily':'Arial'}),

    html.Div(id='raw-data-table', style={
        'maxHeight':'580px','overflowY':'auto',
        'border':f'1px solid {LIGHT}','borderRadius':6,
        'backgroundColor':WHITE,'marginBottom':24,'fontFamily':'Arial',
    }),

    html.Hr(style={'borderColor':LIGHT,'margin':'0 0 20px 0'}),

    # ── SCORES TABLE ────────────────────────────────────────────────
    html.H3("Technical Readiness Scores",
            style={'marginTop':0,'color':BLUE,'fontFamily':'Arial','fontSize':16,'marginBottom':8}),

    dash_table.DataTable(
        id='summary-table',
        columns=[
            {'name':'Jurisdiction',               'id':'Jurisdiction'},
            {'name':'Respondent',                 'id':'Respondent'},
            {'name':'Data Connection Complexity', 'id':'Data Connection Complexity'},
            {'name':'Operational Complexity',     'id':'Operational Complexity'},
            {'name':'Readiness Band',             'id':'Readiness Band'},
        ],
        style_header={'backgroundColor':BLUE,'color':WHITE,'fontWeight':'bold','fontSize':12,'textAlign':'center'},
        style_data={'fontSize':11,'textAlign':'center','padding':'5px 10px'},
        style_data_conditional=[
            {'if':{'filter_query':'{Data Connection Complexity} > 0','column_id':'Data Connection Complexity'},'color':GREEN,'fontWeight':'bold'},
            {'if':{'filter_query':'{Data Connection Complexity} < 0','column_id':'Data Connection Complexity'},'color':RED,'fontWeight':'bold'},
            {'if':{'filter_query':'{Operational Complexity} > 0','column_id':'Operational Complexity'},'color':GREEN,'fontWeight':'bold'},
            {'if':{'filter_query':'{Operational Complexity} < 0','column_id':'Operational Complexity'},'color':RED,'fontWeight':'bold'},
            {'if':{'filter_query':'{Readiness Band} = "High"',    'column_id':'Readiness Band'},'backgroundColor':LGREEN,'color':'black'},
            {'if':{'filter_query':'{Readiness Band} = "Moderate"','column_id':'Readiness Band'},'backgroundColor':'#FFF2CC','color':'black'},
            {'if':{'filter_query':'{Readiness Band} = "Low"',     'column_id':'Readiness Band'},'backgroundColor':'#FCE4D6','color':'black'},
            {'if':{'filter_query':'{Readiness Band} = "Very Low"','column_id':'Readiness Band'},'backgroundColor':'#F4CCCC','color':'black'},
            {'if':{'row_index':'odd'},'backgroundColor':LGREY},
        ],
        style_cell_conditional=[
            {'if':{'column_id':'Jurisdiction'},'textAlign':'left'},
            {'if':{'column_id':'Respondent'},'textAlign':'left','fontSize':11},
        ],
        style_table={'overflowX':'auto'},
    ),

    html.Hr(style={'borderColor':LIGHT,'margin':'20px 0'}),

    # ── CHART ───────────────────────────────────────────────────────
    html.H3("Adoption Complexity Matrix",
            style={'marginTop':0,'color':BLUE,'fontFamily':'Arial','fontSize':16,
                   'marginBottom':4,'textAlign':'center'}),
    dcc.Graph(id='bubble-chart', figure=create_bubble_chart(initial_scores),
              style={'width':'100%'}),

], style={'maxWidth':'1100px','margin':'0 auto','padding':'0 20px','fontFamily':'Arial'})

# ─────────────────────────── CALLBACKS ───────────────────────────────
@app.callback(
    Output('scores-store',   'data'),
    Output('raw-data-store', 'data'),
    Output('summary-table',  'data'),
    Output('bubble-chart',   'figure'),
    Output('raw-jurisdiction-dropdown', 'options'),
    Output('raw-jurisdiction-dropdown', 'value'),
    Output('section-filter-container',  'children'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    prevent_initial_call=False,
)
def on_upload(contents, filename):
    raw_df = parse_upload(contents, filename) if contents else initial_raw
    clean_df, scores = prepare_data(raw_df)

    display_cols = ['Jurisdiction','Respondent','Data Connection Complexity','Operational Complexity','Readiness Band']
    table_rows = scores[display_cols].to_dict('records') if not scores.empty else []

    fig = create_bubble_chart(scores)

    all_jurs = list(clean_df[JUR_COL].unique()) if not clean_df.empty else []
    jur_options = [{'label': j, 'value': j} for j in all_jurs]
    jur_value   = all_jurs[0] if all_jurs else None

    seen_sections = []
    for col in (clean_df.columns if not clean_df.empty else []):
        sec = assign_section(col)
        if sec not in seen_sections: seen_sections.append(sec)
    section_ui = build_section_filter(seen_sections)

    return (
        scores.to_json(date_format='iso', orient='split'),
        clean_df.to_json(date_format='iso', orient='split'),
        table_rows, fig,
        jur_options, jur_value, section_ui,
    )


@app.callback(
    Output('raw-data-table', 'children'),
    Input('raw-jurisdiction-dropdown', 'value'),
    Input('section-checklist', 'value'),
    State('raw-data-store', 'data'),
    prevent_initial_call=False,
)
def update_viewer(jurisdiction, selected_sections, raw_json):
    if not raw_json or not jurisdiction:
        return html.Div("Upload a file and select a jurisdiction.",
                        style={'color':GREY,'padding':20,'fontStyle':'italic','fontSize':13})

    raw_df = pd.read_json(raw_json, orient='split')
    matched = raw_df[raw_df[JUR_COL] == jurisdiction]

    if matched.empty:
        return html.Div(f"No data for {jurisdiction}.", style={'color':GREY,'padding':16})

    # Build colour map consistent with graph
    jur_color_map = {}
    for ci, jur in enumerate(raw_df[JUR_COL].unique()):
        jur_color_map[str(jur).strip()] = PALETTE[ci % len(PALETTE)]
    accent = jur_color_map.get(str(jurisdiction).strip(), BLUE)

    # Single row — plain view
    if len(matched) == 1:
        rows_list = [(matched.iloc[0], '', accent)]
        header = None
    else:
        # Two different respondents for same province — side-by-side diff
        shades = [accent, _lighten(accent, 0.40)]
        rows_list = []
        for i, (_, row_s) in enumerate(matched.iterrows()):
            date_str = str(row_s.get('Date', '')).strip()
            rows_list.append((row_s, f"Respondent {i+1} ({date_str})", shades[i % len(shades)]))

        header = html.Div([
            html.Div("Two respondents submitted for this province — differences highlighted", style={
                'background':'#F0F7FF','border':f'1px solid {MID}',
                'borderRadius':5,'padding':'7px 14px','marginBottom':8,
                'fontSize':12,'color':BLUE,'fontWeight':'600',
            }),
            html.Div([
                html.Div([
                    html.Span("●", style={'color':rows_list[i][2],'marginRight':5,'fontSize':16}),
                    html.Span(rows_list[i][1], style={'fontSize':12,'fontWeight':'600'}),
                ], style={'flex':1,'paddingLeft': 8 if i>0 else 0})
                for i in range(len(rows_list))
            ], style={'display':'flex','gap':8,'marginBottom':8,'paddingLeft':'30%'}),
        ])

    content = render_viewer(rows_list, raw_df, selected_sections or [])
    return html.Div([header, content] if header else [content])


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8050, debug=False)