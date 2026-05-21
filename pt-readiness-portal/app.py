import base64
import io
import pandas as pd
import numpy as np
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go

# -------------------- SCORING FUNCTIONS (unchanged) --------------------
def score_api_protocol(rest, soap, amqp, other):
    if pd.notna(rest) and rest == 1: return 2
    if pd.notna(soap) and soap == 1: return 2
    if pd.notna(amqp) and amqp == 1: return 2
    if pd.notna(other) and str(other).strip() != '': return -2
    return -2

def score_auth(saml, oauth, other):
    if pd.notna(saml) and saml == 1: return 2
    if pd.notna(oauth) and oauth == 1: return 2
    if pd.notna(other) and str(other).strip() != '': return -2
    return -2

def score_10c(no_val, not_sure, yes_val):
    if pd.notna(yes_val) and str(yes_val).strip() not in ['', '0', 'nan', '0.0']:
        try:
            if float(yes_val) != 0: return 2
        except: return 2
    if pd.notna(no_val) and no_val == 1: return -2
    if pd.notna(not_sure) and not_sure == 1: return -2
    return -2

def calculate_scores(df):
    records = []
    for _, row in df.iterrows():
        jur = row['2.0: Please indicate which jurisdiction you are representing']
        if pd.isna(jur): continue

        q2 = str(row['4: 2. Does your jurisdiction have an official provincial/territorial immunization registry/repository?']).strip()
        q2_dcc = q2_oc = 2 if q2 == 'Yes' else -2

        q3 = str(row['5: 3. Is your registry/repository implemented using Panorama?']).strip()
        if q3 == 'Yes': q3_dcc = q3_oc = 2
        elif q3 == 'No': q3_dcc = q3_oc = -2
        else: q3_dcc = q3_oc = 0

        q5 = str(row['9: 5. Where is your immunization registry/repository hosted?']).strip()
        if q5 == 'Cloud': q5_dcc = q5_oc = 2
        elif q5.lower() in ['on-premise', 'hybrid']: q5_dcc = q5_oc = -2
        else: q5_dcc = q5_oc = 0

        audit = row['10: 6a. Is there Auditing of Logins in place for all registry/repository access?']
        logging = row['11: 6b. Is there logging of user activities in place for all registry/repository transactions?']
        q6_dcc = 0
        q6_oc = 2 if (str(audit).strip() == 'Yes' and str(logging).strip() == 'Yes') else -2

        q7 = str(row['12: 7. To ensure reliability and availability of data in the registry/repository, are there backups and mechanisms for disaster recovery?']).strip()
        q7_dcc = 0
        q7_oc = 2 if q7 == 'Yes' else -2

        q10 = str(row['15: 9. Does your registry/repository have externally accessible Application Programming Interfaces (API) covering functionality needed to access and exchange immunization data?']).strip()
        if q10 == 'No': q10_dcc = q10_oc = -2
        elif q10 == 'Yes':
            s10a = score_api_protocol(row['16: REST'], row['16: SOAP'], row['16: AMQP'], row['16: Other, please specify'])
            s10b = score_auth(row['17: SAML'], row['17: OAuth'], row['17: Other, please specify'])
            s10c = score_10c(row['18: No '], row['18: No sure'], row['18: Yes'])
            q10_dcc = q10_oc = min(s10a, s10b, s10c)
        else: q10_dcc = q10_oc = 0

        q14 = str(row['24: 14. Are you currently upgrading or replacing any components of your immunization registry/repository or its technical ecosystem? (e.g., hosting environment, data exchange standards, interfaces with EMRs/EHRs, or other major system changes that will impact immunization data collection and sharing)']).strip()
        q14a = str(row['25: 14a. If not, have any decisions or plans being made towards future upgrading or replacing of any components of your immunization registry/repository or its technical ecosystem?']).strip()
        if q14 == 'Yes': q14_dcc = q14_oc = 2; q14a_dcc = q14a_oc = 0
        elif q14a == 'Yes': q14_dcc = q14_oc = 0; q14a_dcc = q14a_oc = 2
        else: q14_dcc = q14_oc = 0; q14a_dcc = q14a_oc = 0

        any_yes = any([
            pd.notna(row['26: Yes: PS-CA']) and row['26: Yes: PS-CA'] == 1,
            pd.notna(row['26: Yes: Pan-Canadian Health Data Content Framework']) and row['26: Yes: Pan-Canadian Health Data Content Framework'] == 1,
            pd.notna(row['26: Yes: CA:FeX ']) and row['26: Yes: CA:FeX '] == 1,
        ])
        q16_dcc = q16_oc = 2 if any_yes else 0

        total_dcc = q2_dcc + q3_dcc + q5_dcc + q6_dcc + q7_dcc + q10_dcc + q14_dcc + q14a_dcc + q16_dcc
        total_oc  = q2_oc  + q3_oc  + q5_oc  + q6_oc  + q7_oc  + q10_oc  + q14_oc  + q14a_oc  + q16_oc

        records.append({
            'Jurisdiction': jur,
            'Data Connection Complexity': total_dcc,
            'Operational Complexity': total_oc,
        })
    return pd.DataFrame(records)

# -------------------- COLOURS --------------------
BLUE   = '#1F4E79'
MID    = '#2E75B6'
LIGHT  = '#D6E4F0'
GREEN  = '#375623'
LGREEN = '#D5E8D4'
ORANGE = '#C55A11'
RED    = '#C00000'
GREY   = '#595959'
LGREY  = '#F2F2F2'
WHITE  = '#FFFFFF'
JCOLORS = [BLUE, MID, ORANGE, '#7030A0', '#00B050']

def readiness_band(dcc, oc):
    avg = (dcc + oc) / 2
    if avg >= 8:  return 'High'
    if avg >= 4:  return 'Moderate'
    if avg >= 0:  return 'Low'
    return 'Very Low'

def short(name):
    return name.replace('Northwest Territories', 'NWT') \
               .replace('British Columbia', 'BC') \
               .replace('Nova Scotia', 'NS') \
               .replace('Ontario', 'ON') \
               .replace('Manitoba', 'MB')

# -------------------- QUESTION SECTION DEFINITIONS --------------------
# Maps display section labels to column prefix patterns
QUESTION_SECTIONS = [
    ('Respondent & Jurisdiction',    ['Respondent', 'Date', '1:', '2.0:']),
    ('Q1 – Information Systems',     ['3:']),
    ('Q2 – Registry Existence',      ['4:']),
    ('Q3 – Panorama',                ['5:', '6:', '7:']),
    ('Q4 – Immunization Capture',    ['8.']),
    ('Q5 – Hosting',                 ['9:']),
    ('Q6 – Security & Logging',      ['10:', '11:']),
    ('Q7 – Backup & Recovery',       ['12:']),
    ('Q8 – Citizen Access',          ['13:', '14:']),
    ('Q9 – API & Protocols',         ['15:', '16:', '17:', '18:']),
    ('Q10 – System Integration',     ['19:', '20:', '21:']),
    ('Q11 – Standards',              ['22:']),
    ('Q12 – Data Sharing',           ['23:']),
    ('Q13–14 – Upgrades & Roadmap',  ['24:', '25:', '26:']),
    ('Q15–16 – Data Quality',        ['27:', '28:']),
    ('Q17–18 – Patient Updates',     ['29:', '30:', '31:']),
    ('Q19–21 – Governance',          ['32:', '33.', '34.']),
    ('Q22–25 – Admin & Policies',    ['35:', '36:', '37:', '38:']),
]

def assign_section(col_name):
    for section_label, prefixes in QUESTION_SECTIONS:
        for pfx in prefixes:
            if col_name.startswith(pfx):
                return section_label
    return 'Other'

def is_binary_col(col_name, series=None):
    """Detect columns that are checkbox-style (contain only 0, 1, NaN)."""
    if series is not None:
        vals = series.dropna().unique()
        return all(v in [0, 1, 0.0, 1.0] for v in vals) and len(vals) <= 2
    return False

def get_checkbox_label(col_name):
    """Extract the short label after the prefix for checkbox columns."""
    # e.g. "16: REST" -> "REST", "19: EMRs" -> "EMRs"
    parts = col_name.split(':', 1)
    if len(parts) == 2:
        label = parts[1].strip()
        # Strip sub-question letters like "16: REST" stays "REST"
        return label if label else col_name
    return col_name

# -------------------- BUBBLE CHART --------------------
def create_bubble_chart(sdf):
    if sdf.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data loaded. Please upload a CSV file.",
                           xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
                           font=dict(size=16, color=GREY))
        fig.update_layout(plot_bgcolor=WHITE, paper_bgcolor=WHITE)
        return fig

    max_abs_x = np.ceil(sdf['Data Connection Complexity'].abs().max() * 1.15)
    max_abs_y = np.ceil(sdf['Operational Complexity'].abs().max() * 1.15)

    fig = go.Figure()
    for i, (_, row) in enumerate(sdf.iterrows()):
        fig.add_trace(go.Scatter(
            x=[row['Data Connection Complexity']],
            y=[row['Operational Complexity']],
            mode='markers+text',
            marker=dict(size=28, color=JCOLORS[i % len(JCOLORS)], line=dict(width=2, color=WHITE)),
            text=[row['Short']],
            textposition='middle center',
            textfont=dict(color=WHITE, size=10, family='Arial'),
            name=row['Jurisdiction'],
            hovertemplate=(
                f"<b>{row['Jurisdiction']}</b><br>"
                f"Data Connection Complexity: {row['Data Connection Complexity']}<br>"
                f"Operational Complexity: {row['Operational Complexity']}<br>"
                f"Readiness: {row['Readiness Band']}"
                "<extra></extra>"
            ),
        ))

    fig.add_hline(y=0, line=dict(color=GREY, dash='dash', width=1))
    fig.add_vline(x=0, line=dict(color=GREY, dash='dash', width=1))
    fig.add_shape(type='rect', x0=-max_abs_x, y0=0, x1=0, y1=max_abs_y,
                  fillcolor='rgba(255,242,204,0.3)', line_width=0, layer='below')
    fig.add_shape(type='rect', x0=0, y0=0, x1=max_abs_x, y1=max_abs_y,
                  fillcolor='rgba(213,232,212,0.3)', line_width=0, layer='below')
    fig.add_shape(type='rect', x0=-max_abs_x, y0=-max_abs_y, x1=0, y1=0,
                  fillcolor='rgba(252,228,214,0.3)', line_width=0, layer='below')
    fig.add_shape(type='rect', x0=0, y0=-max_abs_y, x1=max_abs_x, y1=0,
                  fillcolor='rgba(244,204,204,0.3)', line_width=0, layer='below')

    fig.update_layout(
        title=dict(text='Adoption Complexity Matrix<br><sup>Each bubble is one jurisdiction. Higher = less complex.</sup>',
                   font=dict(size=15, color=BLUE)),
        xaxis=dict(title='Data Connection Complexity (DCC)', zeroline=False, gridcolor='#EEEEEE',
                   range=[-max_abs_x, max_abs_x]),
        yaxis=dict(title='Operational Complexity (OC)', zeroline=False, gridcolor='#EEEEEE',
                   range=[-max_abs_y, max_abs_y]),
        plot_bgcolor=WHITE, paper_bgcolor=WHITE,
        legend=dict(title='Jurisdiction', font=dict(size=11)),
        width=720, height=520,
    )
    return fig

# -------------------- INITIAL STATE --------------------
initial_scores = pd.DataFrame(columns=['Jurisdiction', 'Data Connection Complexity', 'Operational Complexity'])
initial_scores['Short'] = None
initial_scores['Readiness Band'] = None
initial_raw_df = pd.DataFrame()

# -------------------- APP LAYOUT --------------------
app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server

@server.route('/healthcheck')
def healthcheck():
    return 'ok'

# Inline CSS for the collapsible panel & pill tags
VIEWER_STYLE = """
<style>
.field-filter-panel {
    border: 1px solid #D6E4F0;
    border-radius: 6px;
    background: #F7FBFF;
    padding: 12px 16px;
    margin-bottom: 14px;
}
.field-filter-panel summary {
    cursor: pointer;
    font-weight: 600;
    color: #1F4E79;
    font-size: 13px;
    list-style: none;
    display: flex;
    align-items: center;
    gap: 6px;
    user-select: none;
}
.field-filter-panel summary::after {
    content: '▸';
    font-size: 11px;
    transition: transform 0.2s;
}
.field-filter-panel[open] summary::after {
    transform: rotate(90deg);
}
.section-group-label {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #1F4E79;
    margin: 10px 0 4px 0;
}
.field-checkbox-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 2px 8px;
}
.field-checkbox-row {
    display: flex;
    align-items: center;
    gap: 5px;
    font-size: 12px;
    color: #333;
    padding: 2px 4px;
    border-radius: 3px;
    cursor: pointer;
}
.field-checkbox-row:hover { background: #E8F1FB; }
.section-card {
    border: 1px solid #D6E4F0;
    border-left: 4px solid #1F4E79;
    border-radius: 6px;
    margin-bottom: 10px;
    background: #FFFFFF;
    overflow: hidden;
}
.section-card-header {
    background: #EDF4FB;
    padding: 7px 14px;
    font-size: 12px;
    font-weight: 700;
    color: #1F4E79;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    border-bottom: 1px solid #D6E4F0;
}
.field-row {
    display: flex;
    padding: 7px 14px;
    border-bottom: 1px solid #F0F4F8;
    gap: 12px;
    align-items: flex-start;
}
.field-row:last-child { border-bottom: none; }
.field-label {
    flex: 0 0 38%;
    font-size: 12px;
    color: #2E75B6;
    font-weight: 600;
    word-break: break-word;
    padding-top: 2px;
}
.field-value {
    flex: 1;
    font-size: 12px;
    color: #222;
    word-break: break-word;
}
.pill-group { display: flex; flex-wrap: wrap; gap: 4px; }
.pill {
    display: inline-block;
    padding: 2px 9px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
    background: #D5E8D4;
    color: #375623;
}
.pill-na {
    background: #F2F2F2;
    color: #888;
    font-weight: 400;
}
.empty-state {
    color: #888;
    font-style: italic;
    font-size: 12px;
    padding: 20px 14px;
}
.btn-filter-toggle {
    background: #1F4E79;
    color: white;
    border: none;
    padding: 6px 14px;
    border-radius: 5px;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    margin-bottom: 10px;
}
.filter-actions {
    display: flex;
    gap: 10px;
    margin-top: 10px;
}
.filter-action-btn {
    font-size: 11px;
    color: #1F4E79;
    background: none;
    border: 1px solid #2E75B6;
    border-radius: 4px;
    padding: 3px 10px;
    cursor: pointer;
}
</style>
"""

app.layout = html.Div([
    html.H1("Immunization Registry Readiness Dashboard",
            style={'color': BLUE, 'textAlign': 'center', 'fontFamily': 'Arial'}),

    # Upload
    html.Div([
        dcc.Upload(
            id='upload-data',
            children=html.Div(['Drag and Drop or ', html.A('Select a CSV File')]),
            style={
                'width': '100%', 'height': '60px', 'lineHeight': '60px',
                'borderWidth': '2px', 'borderStyle': 'dashed', 'borderRadius': '5px',
                'textAlign': 'center', 'marginBottom': '20px', 'color': GREY,
                'backgroundColor': '#FAFAFA'
            },
            multiple=False
        ),
    ]),

    # Stores
    dcc.Store(id='scores-store', data=initial_scores.to_json(date_format='iso', orient='split')),
    dcc.Store(id='raw-data-store', data=initial_raw_df.to_json(date_format='iso', orient='split')),
    dcc.Store(id='binary-cols-store', data='[]'),
    dcc.Store(id='selected-sections-store', data='all'),

    # ===== RAW DATA VIEWER =====
    html.H3("Survey Response Viewer", style={'color': BLUE, 'marginTop': 10, 'fontFamily': 'Arial'}),

    html.Div([
        # Jurisdiction picker
        html.Div([
            html.Label("Jurisdiction:", style={'fontWeight': 'bold', 'marginRight': 10,
                                               'fontSize': 13, 'color': GREY}),
            dcc.Dropdown(
                id='raw-jurisdiction-dropdown',
                placeholder="Choose a jurisdiction...",
                clearable=False,
                style={'width': '320px', 'display': 'inline-block', 'fontSize': 13}
            )
        ], style={'marginBottom': 12}),

        # Section filter — collapsible <details> rendered via Dash HTML injection
        html.Div(id='section-filter-container'),

    ], style={'fontFamily': 'Arial'}),

    # The data display
    html.Div(id='raw-data-table', style={
        'maxHeight': '600px',
        'overflowY': 'auto',
        'border': f'1px solid {LIGHT}',
        'borderRadius': 6,
        'backgroundColor': WHITE,
        'marginBottom': '30px',
        'fontFamily': 'Arial',
    }),

    html.Hr(),

    # Scores table
    html.H3("Table 1 – Technical Readiness Scores by Jurisdiction",
            style={'marginTop': 10, 'color': BLUE, 'fontFamily': 'Arial'}),

    dash_table.DataTable(
        id='summary-table',
        columns=[
            {'name': 'Jurisdiction', 'id': 'Jurisdiction'},
            {'name': 'Data Connection Complexity', 'id': 'Data Connection Complexity'},
            {'name': 'Operational Complexity', 'id': 'Operational Complexity'},
            {'name': 'Readiness Band', 'id': 'Readiness Band'},
        ],
        style_header={'backgroundColor': BLUE, 'color': WHITE, 'fontWeight': 'bold',
                      'fontSize': 12, 'textAlign': 'center'},
        style_data={'fontSize': 11, 'textAlign': 'center', 'padding': '6px 12px'},
        style_data_conditional=[
            {'if': {'filter_query': '{Data Connection Complexity} > 0', 'column_id': 'Data Connection Complexity'},
             'color': GREEN, 'fontWeight': 'bold'},
            {'if': {'filter_query': '{Data Connection Complexity} < 0', 'column_id': 'Data Connection Complexity'},
             'color': RED, 'fontWeight': 'bold'},
            {'if': {'filter_query': '{Operational Complexity} > 0', 'column_id': 'Operational Complexity'},
             'color': GREEN, 'fontWeight': 'bold'},
            {'if': {'filter_query': '{Operational Complexity} < 0', 'column_id': 'Operational Complexity'},
             'color': RED, 'fontWeight': 'bold'},
            {'if': {'filter_query': '{Readiness Band} = "High"', 'column_id': 'Readiness Band'},
             'backgroundColor': LGREEN, 'color': 'black'},
            {'if': {'filter_query': '{Readiness Band} = "Moderate"', 'column_id': 'Readiness Band'},
             'backgroundColor': '#FFF2CC', 'color': 'black'},
            {'if': {'filter_query': '{Readiness Band} = "Low"', 'column_id': 'Readiness Band'},
             'backgroundColor': '#FCE4D6', 'color': 'black'},
            {'if': {'filter_query': '{Readiness Band} = "Very Low"', 'column_id': 'Readiness Band'},
             'backgroundColor': '#F4CCCC', 'color': 'black'},
            {'if': {'row_index': 'odd'}, 'backgroundColor': LGREY},
        ],
        style_cell_conditional=[
            {'if': {'column_id': 'Jurisdiction'}, 'textAlign': 'left'}
        ],
        style_table={'overflowX': 'auto'},
    ),

    html.Hr(),
    dcc.Graph(id='bubble-chart', figure=create_bubble_chart(initial_scores)),

], style={'maxWidth': '960px', 'margin': 'auto', 'fontFamily': 'Arial'})


# -------------------- HELPER: build section filter UI --------------------
def build_section_filter(sections_present):
    """
    Build a <details> collapsible with checkboxes for each section.
    Uses dcc.Checklist for Dash interactivity.
    """
    options = [{'label': s, 'value': s} for s in sections_present]
    return html.Div([
        html.Details([
            html.Summary("⚙ Filter question sections", style={
                'cursor': 'pointer', 'fontWeight': '600', 'color': BLUE,
                'fontSize': 13, 'padding': '8px 12px',
                'backgroundColor': '#EDF4FB',
                'borderRadius': '6px 6px 0 0',
                'listStyle': 'none',
            }),
            html.Div([
                html.Div([
                    html.Span("Show / hide sections:", style={
                        'fontSize': 11, 'color': GREY, 'display': 'block', 'marginBottom': 8
                    }),
                    dcc.Checklist(
                        id='section-checklist',
                        options=options,
                        value=[s['value'] for s in options],
                        labelStyle={'display': 'inline-flex', 'alignItems': 'center',
                                    'marginRight': 14, 'marginBottom': 4,
                                    'fontSize': 12, 'cursor': 'pointer', 'color': '#222'},
                        inputStyle={'marginRight': 4, 'accentColor': BLUE},
                    ),
                ], style={'padding': '10px 14px'}),
            ], style={
                'border': f'1px solid {LIGHT}',
                'borderTop': 'none',
                'borderRadius': '0 0 6px 6px',
                'backgroundColor': '#FAFCFF',
            }),
        ], style={
            'border': f'1px solid {LIGHT}',
            'borderRadius': 6,
            'marginBottom': 12,
        }),
    ])


# -------------------- HELPER: render data rows --------------------
def render_survey_row(col_name, value, is_binary, all_binary_in_group, group_cols_done):
    """Render a single field row, or skip if it's part of a binary group already rendered."""
    pass  # logic in main render


def render_jurisdiction_data(row_series, raw_df, selected_sections):
    """
    Build the grouped display for one jurisdiction's survey response.
    Groups binary checkboxes within the same prefix into pill rows.
    """
    if row_series is None:
        return html.Div("No data found.", style={'color': GREY, 'padding': 16})

    # Detect binary columns
    binary_cols = set()
    for col in raw_df.columns:
        vals = raw_df[col].dropna().unique()
        if len(vals) <= 2 and all(v in [0, 1, 0.0, 1.0] for v in vals):
            binary_cols.add(col)

    # Group columns by section
    sections = {}
    for col in raw_df.columns:
        sec = assign_section(col)
        if sec not in sections:
            sections[sec] = []
        sections[sec].append(col)

    # Filter sections
    if selected_sections and selected_sections != 'all':
        sections = {k: v for k, v in sections.items() if k in selected_sections}

    cards = []

    for sec_label, cols in sections.items():
        rows_html = []
        # Group consecutive binary cols that share same numeric prefix (e.g. "16: ...")
        rendered_binary_groups = set()

        for col in cols:
            if col in binary_cols:
                # Find the group prefix (everything before the ': ' label part is the q-number)
                prefix = col.split(':')[0].strip()
                group_key = (sec_label, prefix)

                if group_key in rendered_binary_groups:
                    continue
                rendered_binary_groups.add(group_key)

                # Collect all binary cols in this section with same prefix
                group_members = [c for c in cols if c in binary_cols and c.split(':')[0].strip() == prefix]

                checked = []
                for c in group_members:
                    val = row_series.get(c)
                    try:
                        if pd.notna(val) and float(val) == 1.0:
                            checked.append(get_checkbox_label(c))
                    except (ValueError, TypeError):
                        if str(val).strip() not in ['', 'nan', '0', '0.0']:
                            checked.append(get_checkbox_label(c))

                # Question label from first col
                first_col = group_members[0]
                # Use prefix to look up a clean label if available
                q_label = f"Q {prefix} (select all that apply)"

                if checked:
                    value_el = html.Div(
                        [html.Span(c, style={
                            'display': 'inline-block',
                            'padding': '2px 9px',
                            'borderRadius': 12,
                            'fontSize': 11,
                            'fontWeight': '600',
                            'background': '#D5E8D4',
                            'color': '#375623',
                            'margin': '2px 3px 2px 0',
                        }) for c in checked],
                        style={'display': 'flex', 'flexWrap': 'wrap', 'gap': 2}
                    )
                else:
                    value_el = html.Span("None selected", style={
                        'fontSize': 12, 'color': '#aaa', 'fontStyle': 'italic'
                    })

                rows_html.append(html.Div([
                    html.Div(q_label, style={
                        'flex': '0 0 38%', 'fontSize': 12, 'color': '#2E75B6',
                        'fontWeight': '600', 'wordBreak': 'break-word', 'paddingTop': 2
                    }),
                    html.Div(value_el, style={'flex': 1}),
                ], style={
                    'display': 'flex', 'padding': '8px 14px',
                    'borderBottom': f'1px solid #F0F4F8',
                    'gap': 12, 'alignItems': 'flex-start',
                }))

            else:
                # Text / select field
                val = row_series.get(col, None)
                if pd.isna(val) or str(val).strip() in ['', 'nan']:
                    val_str = "—"
                    val_style = {'flex': 1, 'fontSize': 12, 'color': '#bbb', 'fontStyle': 'italic'}
                else:
                    val_str = str(val)
                    val_style = {'flex': 1, 'fontSize': 12, 'color': '#222', 'wordBreak': 'break-word'}

                # Clean column label: remove leading "N: " prefix
                parts = col.split(':', 1)
                if len(parts) == 2:
                    clean_label = parts[1].strip()
                else:
                    clean_label = col

                rows_html.append(html.Div([
                    html.Div(clean_label, style={
                        'flex': '0 0 38%', 'fontSize': 12, 'color': '#2E75B6',
                        'fontWeight': '600', 'wordBreak': 'break-word', 'paddingTop': 2
                    }),
                    html.Div(val_str, style=val_style),
                ], style={
                    'display': 'flex', 'padding': '8px 14px',
                    'borderBottom': f'1px solid #F0F4F8',
                    'gap': 12, 'alignItems': 'flex-start',
                }))

        if rows_html:
            card = html.Div([
                html.Div(sec_label, style={
                    'background': '#EDF4FB',
                    'padding': '7px 14px',
                    'fontSize': 11,
                    'fontWeight': '700',
                    'color': BLUE,
                    'textTransform': 'uppercase',
                    'letterSpacing': '0.04em',
                    'borderBottom': f'1px solid {LIGHT}',
                }),
                html.Div(rows_html),
            ], style={
                'border': f'1px solid {LIGHT}',
                'borderLeft': f'4px solid {BLUE}',
                'borderRadius': 6,
                'marginBottom': 10,
                'background': WHITE,
                'overflow': 'hidden',
            })
            cards.append(card)

    return html.Div(cards) if cards else html.Div("No sections selected.", style={'color': GREY, 'padding': 16})


# -------------------- CALLBACKS --------------------

def parse_upload(contents, filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    return pd.read_csv(io.StringIO(decoded.decode('utf-8')))


@app.callback(
    Output('scores-store', 'data'),
    Output('raw-data-store', 'data'),
    Output('summary-table', 'data'),
    Output('bubble-chart', 'figure'),
    Output('raw-jurisdiction-dropdown', 'options'),
    Output('raw-jurisdiction-dropdown', 'value'),
    Output('section-filter-container', 'children'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    prevent_initial_call=False,
)
def update_on_upload(contents, filename):
    if contents is not None:
        raw_df = parse_upload(contents, filename)
    else:
        raw_df = pd.DataFrame()
        scores = initial_scores.copy()
        return (
            scores.to_json(date_format='iso', orient='split'),
            raw_df.to_json(date_format='iso', orient='split'),
            scores.to_dict('records'),
            create_bubble_chart(scores),
            [], None, html.Div()
        )

    scores = calculate_scores(raw_df)
    if not scores.empty:
        scores['Short'] = scores['Jurisdiction'].apply(short)
        scores['Readiness Band'] = scores.apply(
            lambda r: readiness_band(r['Data Connection Complexity'], r['Operational Complexity']), axis=1
        )
    else:
        scores['Short'] = None
        scores['Readiness Band'] = None

    jurs = raw_df['2.0: Please indicate which jurisdiction you are representing'].dropna().unique()
    jur_options = [{'label': j, 'value': j} for j in jurs]
    jur_value = jurs[0] if len(jurs) > 0 else None

    # Build section list from this dataset's columns
    seen = []
    for col in raw_df.columns:
        sec = assign_section(col)
        if sec not in seen:
            seen.append(sec)
    section_filter_ui = build_section_filter(seen)

    return (
        scores.to_json(date_format='iso', orient='split'),
        raw_df.to_json(date_format='iso', orient='split'),
        scores.to_dict('records'),
        create_bubble_chart(scores),
        jur_options,
        jur_value,
        section_filter_ui,
    )


@app.callback(
    Output('raw-data-table', 'children'),
    Input('raw-jurisdiction-dropdown', 'value'),
    Input('section-checklist', 'value'),
    State('raw-data-store', 'data'),
    prevent_initial_call=False,
)
def update_raw_table(jurisdiction, selected_sections, raw_data_json):
    if not raw_data_json or not jurisdiction:
        return html.Div("Upload a CSV and select a jurisdiction to view responses.",
                        style={'color': GREY, 'padding': 20, 'fontStyle': 'italic', 'fontSize': 13})

    raw_df = pd.read_json(raw_data_json, orient='split')
    mask = raw_df['2.0: Please indicate which jurisdiction you are representing'] == jurisdiction
    rows = raw_df[mask]

    if rows.empty:
        return html.Div(f"No data found for {jurisdiction}.", style={'color': GREY, 'padding': 16})

    row_series = rows.iloc[0]
    return render_jurisdiction_data(row_series, raw_df, selected_sections or [])


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8050, debug=False)