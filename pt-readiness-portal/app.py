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

# ─────────────────────────── SCORE NORMALIZATION ─────────────────────────────
# Raw DCC range: -8 to +14  |  Raw OC range: -12 to +18
# Normalize each independently to [-1, +1] using their respective bounds.
DCC_MIN, DCC_MAX = -8,  14
OC_MIN,  OC_MAX  = -12, 18

def normalize_dcc(raw):
    """Map raw DCC score → [-1, 1]."""
    mid  = (DCC_MAX + DCC_MIN) / 2          # 3.0
    half = (DCC_MAX - DCC_MIN) / 2          # 11.0
    return round((raw - mid) / half, 4)

def normalize_oc(raw):
    """Map raw OC score → [-1, 1]."""
    mid  = (OC_MAX + OC_MIN) / 2            # 3.0
    half = (OC_MAX - OC_MIN) / 2            # 15.0
    return round((raw - mid) / half, 4)

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


def score_row_breakdown(row):
    """
    Returns a dict mapping each scored section to its (dcc_raw, oc_raw, signal) where
    signal is 'positive' | 'negative' | 'neutral'.
    Used to annotate the viewer with per-question scoring impact.
    """
    results = {}

    def _sig(dcc_v, oc_v):
        avg = (dcc_v + oc_v) / 2 if (dcc_v is not None and oc_v is not None) else (dcc_v or oc_v or 0)
        if avg > 0:  return 'positive'
        if avg < 0:  return 'negative'
        return 'neutral'

    # Q2
    q2 = str(row.get('4: 2. Does your jurisdiction have an official provincial/territorial immunization registry/repository?','')).strip()
    v = 2 if q2 == 'Yes' else -2
    results['q2'] = (v, v, _sig(v, v))

    # Q3
    q3 = str(row.get('5: 3. Is your registry/repository implemented using Panorama?','')).strip()
    v = 2 if q3=='Yes' else (-2 if q3=='No' else 0)
    results['q3'] = (v, v, _sig(v, v))

    # Q5
    q5 = str(row.get('9: 5. Where is your immunization registry/repository hosted?','')).strip()
    v = 2 if q5=='Cloud' else (-2 if q5.lower() in ['on-premise','hybrid'] else 0)
    results['q5'] = (v, v, _sig(v, v))

    # Q6 – OC only
    audit   = row.get('10: 6a. Is there Auditing of Logins in place for all registry/repository access?','')
    logging = row.get('11: 6b. Is there logging of user activities in place for all registry/repository transactions?','')
    oc_v = 2 if (str(audit).strip()=='Yes' and str(logging).strip()=='Yes') else -2
    results['q6'] = (0, oc_v, _sig(None, oc_v))

    # Q7 – OC only
    q7 = str(row.get('12: 7. To ensure reliability and availability of data in the registry/repository, are there backups and mechanisms for disaster recovery?','')).strip()
    oc_v = 2 if q7=='Yes' else -2
    results['q7'] = (0, oc_v, _sig(None, oc_v))

    # Q10
    q10 = str(row.get('15: 9. Does your registry/repository have externally accessible Application Programming Interfaces (API) covering functionality needed to access and exchange immunization data?','')).strip()
    if q10 == 'No':
        v = -2
    elif q10 == 'Yes':
        s10a = score_api_protocol(row.get('16: REST'), row.get('16: SOAP'), row.get('16: AMQP'), row.get('16: Other, please specify'))
        s10b = score_auth(row.get('17: SAML'), row.get('17: OAuth'), row.get('17: Other, please specify'))
        s10c = score_10c(row.get('18: No '), row.get('18: No sure'), row.get('18: Yes'))
        v = min(s10a, s10b, s10c)
    else:
        v = 0
    results['q10'] = (v, v, _sig(v, v))

    # Q14 / Q14a
    q14  = str(row.get('24: 14. Are you currently upgrading or replacing any components of your immunization registry/repository or its technical ecosystem? (e.g., hosting environment, data exchange standards, interfaces with EMRs/EHRs, or other major system changes that will impact immunization data collection and sharing)','')).strip()
    q14a = str(row.get('25: 14a. If not, have any decisions or plans being made towards future upgrading or replacing of any components of your immunization registry/repository or its technical ecosystem?','')).strip()
    if q14 == 'Yes':
        results['q14']  = (2, 2, 'positive')
        results['q14a'] = (0, 0, 'neutral')
    elif q14a == 'Yes':
        results['q14']  = (0, 0, 'neutral')
        results['q14a'] = (2, 2, 'positive')
    else:
        results['q14']  = (0, 0, 'neutral')
        results['q14a'] = (0, 0, 'neutral')

    # Q16
    any_yes = any([
        pd.notna(row.get('26: Yes: PS-CA')) and row.get('26: Yes: PS-CA')==1,
        pd.notna(row.get('26: Yes: Pan-Canadian Health Data Content Framework')) and row.get('26: Yes: Pan-Canadian Health Data Content Framework')==1,
        pd.notna(row.get('26: Yes: CA:FeX ')) and row.get('26: Yes: CA:FeX ')==1,
    ])
    v = 2 if any_yes else 0
    results['q16'] = (v, v, _sig(v, v))

    return results


# Column prefix → which scored question key it belongs to (for badge display)
# None means it contributes to scoring indirectly (sub-question of q10, etc.)
PREFIX_TO_SCORE_KEY = {
    '4':  'q2',
    '5':  'q3',
    '9':  'q5',
    '10': 'q6',
    '11': 'q6',
    '12': 'q7',
    '15': 'q10',
    '16': 'q10',
    '17': 'q10',
    '18': 'q10',
    '24': 'q14',
    '25': 'q14a',
    '26': 'q16',
}

SCORE_KEY_LABELS = {
    'q2':   'Registry existence',
    'q3':   'Panorama usage',
    'q5':   'Hosting model',
    'q6':   'Security & logging',
    'q7':   'Backup & DR',
    'q10':  'API readiness',
    'q14':  'Active upgrades',
    'q14a': 'Upgrade plans',
    'q16':  'Interop roadmap',
}


def readiness_band(dcc_s, oc_s):
    avg = (dcc_s + oc_s) / 2
    if avg >= 8: return 'High'
    if avg >= 4: return 'Moderate'
    if avg >= 0: return 'Low'
    return 'Very Low'

# ─────────────────────────── DEDUPLICATION ───────────────────────────
def deduplicate(df):
    df = df.copy()
    df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
    df[JUR_COL] = df[JUR_COL].fillna(UNKNOWN_JUR)
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
        if jur == UNKNOWN_JUR:
            continue
        dcc_raw, oc_raw = score_row(row)
        dcc_norm = normalize_dcc(dcc_raw)
        oc_norm  = normalize_oc(oc_raw)
        respondent = str(row.get('Respondent', '')).strip()
        if jur not in jur_color_idx:
            jur_color_idx[jur] = color_counter[0]
            color_counter[0] += 1
        records.append({
            'Jurisdiction': jur,
            'Short': short(jur),
            'Respondent': respondent,
            'Data Connection Complexity': dcc_raw,        # raw integer — for table & hover
            'Operational Complexity': oc_raw,             # raw integer — for table & hover
            '_dcc_norm': dcc_norm,                        # normalized — for chart axes only
            '_oc_norm': oc_norm,                          # normalized — for chart axes only
            'Readiness Band': readiness_band(dcc_raw, oc_raw),
            '_color_idx': jur_color_idx[jur],
        })

    scores = pd.DataFrame(records)
    if scores.empty:
        return scores
    scores = apply_jitter(scores)
    return scores

def apply_jitter(scores):
    scores = scores.copy()
    scores['_x'] = scores['_dcc_norm'].astype(float)
    scores['_y'] = scores['_oc_norm'].astype(float)
    coord_groups = scores.groupby(['_x', '_y'])
    for (x, y), idx in coord_groups.groups.items():
        n = len(idx)
        if n == 1:
            continue
        radius = 0.05   # Scaled down since axis is now [-1, 1]
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

# ─────────────────────────── SCORE BADGE ─────────────────────────────
_SIGNAL_CFG = {
    'positive': {'icon': '▲', 'label': 'Positive impact',  'color': '#375623', 'bg': '#D5E8D4', 'border': '#A9C9A0'},
    'negative': {'icon': '▼', 'label': 'Negative impact',  'color': '#C00000', 'bg': '#FFDCE1', 'border': '#F4A0A0'},
    'neutral':  {'icon': '●', 'label': 'Neutral','color': '#7F6B00', 'bg': '#FFF8DC', 'border': '#E0D080'},
}

def _single_pill(label, signal):
    """One DCC or OC signal pill."""
    cfg = _SIGNAL_CFG.get(signal, _SIGNAL_CFG['neutral'])
    return html.Span(
        [
            html.Span(cfg['icon'], style={'marginRight': 3, 'fontSize': 9}),
            html.Span(label, style={'fontSize': 10}),
        ],
        title=cfg['label'],
        style={
            'display': 'inline-flex', 'alignItems': 'center',
            'padding': '1px 6px', 'borderRadius': 10,
            'border': f"1px solid {cfg['border']}",
            'backgroundColor': cfg['bg'],
            'color': cfg['color'],
            'fontWeight': '700',
            'whiteSpace': 'nowrap',
        }
    )

def score_badges(dcc_signal, oc_signal):
    """Return a span with two pills: one for DCC signal, one for OC signal."""
    return html.Span(
        [
            _single_pill('DCC', dcc_signal),
            _single_pill('OC',  oc_signal),
        ],
        style={'display': 'inline-flex', 'gap': 4, 'marginLeft': 8, 'verticalAlign': 'middle'}
    )

# ─────────────────────────── BUBBLE CHART ───────────────────────────
def create_bubble_chart(scores):
    fig = go.Figure()
    if scores.empty:
        fig.add_annotation(text="Upload a CSV or Excel file to get started.",
                           xref="paper", yref="paper", x=0.5, y=0.5,
                           showarrow=False, font=dict(size=14, color=GREY))
        fig.update_layout(plot_bgcolor=WHITE, paper_bgcolor=WHITE, height=560)
        return fig

    # Normalized axes are always [-1, 1] with a small margin
    axis_range = [-1.15, 1.15]

    for x0, y0, x1, y1, color in [
        (-1.15, 0,    0,    1.15, 'rgba(255,242,204,0.22)'),
        (0,     0,    1.15, 1.15, 'rgba(213,232,212,0.22)'),
        (-1.15,-1.15, 0,    0,    'rgba(252,228,214,0.22)'),
        (0,    -1.15, 1.15, 0,    'rgba(244,204,204,0.22)'),
    ]:
        fig.add_shape(type='rect', x0=x0, y0=y0, x1=x1, y1=y1,
                      fillcolor=color, line_width=0, layer='below')

    fig.add_hline(y=0, line=dict(color='#BBBBBB', dash='dash', width=1))
    fig.add_vline(x=0, line=dict(color='#BBBBBB', dash='dash', width=1))

    for _, row in scores.iterrows():
        color = PALETTE[int(row['_color_idx']) % len(PALETTE)]
        x_pos  = row.get('_x', row['_dcc_norm'])   # jittered normalized position
        y_pos  = row.get('_y', row['_oc_norm'])     # jittered normalized position
        true_x = row['_dcc_norm']                   # un-jittered normalized (for jitter line)
        true_y = row['_oc_norm']
        raw_dcc = int(row['Data Connection Complexity'])
        raw_oc  = int(row['Operational Complexity'])

        if abs(x_pos - true_x) > 0.001 or abs(y_pos - true_y) > 0.001:
            fig.add_shape(type='line',
                x0=true_x, y0=true_y, x1=x_pos, y1=y_pos,
                line=dict(color=color, width=1, dash='dot'), layer='below')

        hover = (
            f"<b>{row['Jurisdiction']}</b><br>"
            f"DCC: {raw_dcc} &nbsp; OC: {raw_oc}<br>"
            f"Readiness: {row['Readiness Band']}<br>"
            f"Respondent: {row.get('Respondent','')}"
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
            name=row['Jurisdiction'],
            hovertemplate=hover,
            showlegend=True,
        ))

    # Tick marks at meaningful positions on the normalized scale
    tick_vals  = [-1, -0.5, 0, 0.5, 1]
    tick_texts = ['-1', '-0.5', '0', '+0.5', '+1']

    fig.update_layout(
        xaxis=dict(
            title='Data Connection Complexity (normalized) →',
            zeroline=False, gridcolor='#EEEEEE',
            range=axis_range,
            tickvals=tick_vals, ticktext=tick_texts,
            title_font=dict(size=12), tickfont=dict(size=11),
        ),
        yaxis=dict(
            title='Operational Complexity (normalized) →',
            zeroline=False, gridcolor='#EEEEEE',
            range=axis_range,
            tickvals=tick_vals, ticktext=tick_texts,
            title_font=dict(size=12), tickfont=dict(size=11),
        ),
        plot_bgcolor=WHITE, paper_bgcolor=WHITE,
        legend=dict(title='Jurisdiction', font=dict(size=11),
                    bgcolor='rgba(255,255,255,0.9)', bordercolor=LIGHT, borderwidth=1,
                    x=1.01, xanchor='left', y=1, yanchor='top'),
        height=600,
        margin=dict(l=60, r=180, t=30, b=60),
        hovermode='closest',
    )
    return fig

# ─────────────────────────── SECTION / COLUMN METADATA ──────────────
COL_META = {
    'Respondent': ('Respondent & Jurisdiction', 'Respondent ID'),
    'Date':       ('Respondent & Jurisdiction', 'Submission Date'),
    '1':          ('Respondent & Jurisdiction', 'Name / Email'),
    '2.0':        ('Respondent & Jurisdiction', 'Jurisdiction'),

    '3':    ('Information Systems',
             'What types of information systems capture immunization data?'),

    '4':    ('Registry',
             'Does your jurisdiction have an official immunization registry/repository?'),

    '5':    ('Panorama', 'Is your registry implemented using Panorama?'),
    '6':    ('Panorama', 'Panorama version'),
    '7':    ('Panorama', 'Non-Panorama system name(s) and version(s)'),

    '8.1':  ('Immunization Capture by Care Setting', None),
    '8.2.1':('Immunization Capture by Care Setting', 'Public Health – additional notes'),
    '8.2.2':('Immunization Capture by Care Setting', 'Primary Care – additional notes'),
    '8.2.3':('Immunization Capture by Care Setting', 'Pharmacy – additional notes'),
    '8.2.4':('Immunization Capture by Care Setting', 'Hospital – additional notes'),
    '8.2.5':('Immunization Capture by Care Setting', 'Other – additional notes'),

    '9':    ('Hosting', 'Where is the registry/repository hosted?'),

    '10':   ('Security & Logging', 'Auditing of logins in place?'),
    '11':   ('Security & Logging', 'Logging of user activities in place?'),

    '12':   ('Backup & Disaster Recovery',
             'Backups and disaster recovery mechanisms in place?'),

    '13':   ('Citizen Access',
             'Digital tool for citizens to access their immunization records?'),
    '14':   ('Citizen Access', 'Alternative citizen access methods'),

    '15':   ('API & Data Exchange',
             'Does the registry have externally accessible APIs?'),
    '16':   ('API & Data Exchange', 'API protocol(s) used'),
    '17':   ('API & Data Exchange', 'API authentication method(s)'),
    '18':   ('API & Data Exchange',
             'If no APIs, other data exchange interfaces/protocols supported?'),

    '19':   ('System Integration',
             'Which systems report immunization data to the registry?'),
    '20':   ('System Integration', 'Reporting mechanism(s)'),
    '21':   ('System Integration', 'Data exchange formats/standards used'),

    '22':   ('Terminology & Standards',
             'Terminology and data exchange standards used'),

    '23':   ('Data Sharing Processes',
             'Immunization data sharing/transfer processes in place'),

    '24':   ('Upgrades & Roadmap',
             'Currently upgrading or replacing registry components?'),
    '25':   ('Upgrades & Roadmap',
             'Plans to upgrade or replace registry components in future?'),
    '26':   ('Upgrades & Roadmap',
             'Participating in Interoperability Roadmap (PS-CA / Pan-Canadian HDCF / CA:FeX)?'),

    '27':   ('Data Quality', 'How is registry data quality assessed?'),
    '28':   ('Data Quality',
             'How are provider-identified data quality issues remediated?'),

    '29':   ('Patient Data Updates',
             'How can patients update or correct their immunization record?'),

    '30':   ('Archiving', 'Is immunization data ever archived?'),
    '31':   ('Archiving', 'When and how is data archived?'),

    '32':   ('Governance & Custodianship',
             'Who is the custodian/business owner of immunization data?'),

    '33.1': ('Who Administers Immunizations', 'Public Health Office'),
    '33.2': ('Who Administers Immunizations', 'Primary Care'),
    '33.3': ('Who Administers Immunizations', 'Community Health Centre'),
    '33.4': ('Who Administers Immunizations', 'School'),
    '33.5': ('Who Administers Immunizations', 'Pharmacy'),
    '33.6': ('Who Administers Immunizations', 'Acute Care Facilities'),
    '33.7': ('Who Administers Immunizations', 'Long Term Care Facilities'),
    '33.8': ('Who Administers Immunizations', 'Other'),

    '34.1': ('Care Settings by Immunization Type', 'Childhood Immunizations'),
    '34.2': ('Care Settings by Immunization Type', 'Flu / COVID Immunizations'),
    '34.3': ('Care Settings by Immunization Type', 'Travel Immunizations'),
    '34.4': ('Care Settings by Immunization Type', 'Adult Immunizations'),
    '34.5': ('Care Settings by Immunization Type', 'Adolescent Immunizations'),
    '34.6': ('Care Settings by Immunization Type', 'High Risk Immunizations'),
    '34.7': ('Care Settings by Immunization Type', 'Post-Exposure Immunizations'),

    '35':   ('Adverse Events & Vaccine Issues',
             'How are adverse events recorded and shared with providers?'),
    '36':   ('Adverse Events & Vaccine Issues',
             'How are vaccine inventory issues (spoilage, wastage) recorded?'),

    '37':   ('Policies & Agreements',
             'Policies, procedures or agreements guiding data sharing'),
    '38':   ('Challenges',
             'Clinical / business / technical challenges in sharing immunization data'),
}

# ─────────────────────────── Q4 CAPTURE MATRIX ──────────────────────
_CARE_SETTINGS  = ['Public Health', 'Primary Care', 'Pharmacy', 'Hospital', 'Other']
_FREQ_SUFFIXES  = ['', '.1', '.2', '.3', '.4']
_FREQ_LABELS    = ['routinely captured', 'occasionally captured', 'rarely captured']

_FREQ_COLS = {
    sfx: {lbl: f'8.1: 1_Immunization events are {lbl}{sfx}' for lbl in _FREQ_LABELS}
    for sfx in _FREQ_SUFFIXES
}

_FREQ_STYLE = {
    'routinely':    ('#375623', '#D5E8D4'),
    'occasionally': ('#7F4800', '#FFF2CC'),
    'rarely':       ('#C00000', '#FFDCE1'),
}

def _setting_freq(row_s, sfx):
    for lbl in _FREQ_LABELS:
        col = _FREQ_COLS[sfx][lbl]
        v = row_s.get(col)
        try:
            if pd.notna(v) and float(v) == 1.0:
                return lbl.replace(' captured', '')
        except Exception:
            pass
    return None

def render_imm_capture_table(rows_list):
    is_diff = len(rows_list) > 1
    th_style = {'padding': '5px 10px', 'fontSize': 11, 'fontWeight': '700',
                'backgroundColor': '#F5F8FB', 'borderBottom': f'2px solid {LIGHT}'}
    header_cells = [html.Th('Care Setting', style={**th_style, 'textAlign': 'left', 'color': GREY})]
    if is_diff:
        for _, suffix, accent in rows_list:
            header_cells.append(html.Th(suffix or 'Response',
                                        style={**th_style, 'textAlign': 'center', 'color': accent}))
    else:
        header_cells.append(html.Th('Capture Frequency',
                                    style={**th_style, 'textAlign': 'center', 'color': GREY}))
    trows = []
    for setting, sfx in zip(_CARE_SETTINGS, _FREQ_SUFFIXES):
        cells = [html.Td(setting,
                         style={'padding': '5px 10px', 'fontSize': 12,
                                'fontWeight': '600', 'color': '#222'})]
        for row_s, _, _ in rows_list:
            freq = _setting_freq(row_s, sfx)
            if freq:
                fg, bg = _FREQ_STYLE.get(freq, (GREY, LGREY))
                cells.append(html.Td(
                    freq.capitalize(),
                    style={'textAlign': 'center', 'padding': '4px 10px', 'fontSize': 11,
                           'fontWeight': '700', 'color': fg, 'backgroundColor': bg,
                           'borderRadius': 4}
                ))
            else:
                cells.append(html.Td('—', style={'textAlign': 'center', 'color': '#ccc',
                                                  'fontSize': 11, 'padding': '4px 10px'}))
        trows.append(html.Tr(cells, style={'borderBottom': f'1px solid #F0F4F8'}))

    return html.Table(
        [html.Thead(html.Tr(header_cells)), html.Tbody(trows)],
        style={'width': '100%', 'borderCollapse': 'collapse', 'fontSize': 12, 'marginBottom': 4}
    )

# ─────────────────────────── COLUMN HELPERS ─────────────────────────
def assign_section(col):
    prefix = col.split(':')[0].strip()
    meta = COL_META.get(prefix)
    return meta[0] if meta else 'Other'

def get_col_label(col):
    prefix = col.split(':')[0].strip()
    meta = COL_META.get(prefix)
    if meta and meta[1]:
        return meta[1]
    parts = col.split(':', 1)
    return parts[1].strip() if len(parts) == 2 and parts[1].strip() else col

def get_checkbox_label(col):
    parts = col.split(':', 1)
    return parts[1].strip() if len(parts) == 2 and parts[1].strip() else col

# ─────────────────────────── VIEWER ─────────────────────────────────
def _field_row(label, val_cells, is_diff, rows_list, badge=None):
    """
    badge: an html element (score_badge) to append after the label, or None.
    """
    label_content = [
        html.Span(label, style={'fontSize': 12, 'color': '#2E75B6', 'fontWeight': '600'}),
    ]
    if badge is not None:
        label_content.append(badge)

    label_el = html.Div(label_content, style={
        'flex': '0 0 30%', 'wordBreak': 'break-word', 'paddingTop': 2,
        'display': 'flex', 'flexWrap': 'wrap', 'alignItems': 'center', 'gap': 4,
    })

    if is_diff:
        val_el = html.Div([
            html.Div(cell, style={
                'flex': 1,
                'borderLeft': f'3px solid {rows_list[i][2]}',
                'paddingLeft': 8,
                'marginLeft': 4 if i > 0 else 0,
            }) for i, cell in enumerate(val_cells)
        ], style={'display': 'flex', 'flex': 1, 'gap': 8})
    else:
        val_el = html.Div(val_cells[0], style={
            'flex': 1, 'fontSize': 12, 'color': '#111', 'wordBreak': 'break-word'
        })

    return html.Div([label_el, val_el], style={
        'display': 'flex', 'padding': '7px 14px',
        'borderBottom': f'1px solid #F0F4F8', 'gap': 12, 'alignItems': 'flex-start',
    })


def render_viewer(rows_list, raw_df, selected_sections):
    if not rows_list:
        return html.Div("Select a jurisdiction to view responses.",
                        style={'color': GREY, 'padding': 20, 'fontStyle': 'italic', 'fontSize': 13})

    is_diff = len(rows_list) > 1

    # Compute scoring breakdown for each respondent row
    breakdowns = [score_row_breakdown(row_s) for row_s, _, _ in rows_list]

    # Identify pure-binary checkbox columns (0/1 only)
    binary_cols = set()
    for col in raw_df.columns:
        vals = raw_df[col].dropna().unique()
        if len(vals) <= 2 and all(v in [0, 1, 0.0, 1.0] for v in vals):
            binary_cols.add(col)

    # Build ordered section → columns map
    sections_order, sections_map = [], {}
    for col in raw_df.columns:
        sec = assign_section(col)
        if sec not in sections_map:
            sections_map[sec] = []
            sections_order.append(sec)
        sections_map[sec].append(col)

    if selected_sections:
        sections_order = [s for s in sections_order if s in selected_sections]

    # Track which score keys have already had a badge shown (per-section render pass)
    # so we don't show the badge on every sub-column of the same scored question.
    # We reset this per section card.

    cards = []
    for sec in sections_order:
        cols = sections_map.get(sec, [])
        row_els = []
        rendered_bin_groups = set()
        imm_capture_rendered = False
        shown_score_keys = set()   # reset per section card

        for col in cols:
            prefix = col.split(':')[0].strip()

            # ── Q4 immunization capture matrix ───────────────────────
            if prefix == '8.1':
                if not imm_capture_rendered:
                    imm_capture_rendered = True
                    table = render_imm_capture_table(rows_list)
                    row_els.append(html.Div([
                        html.Div('Immunization events capture frequency by care setting',
                                 style={'flex': '0 0 30%', 'fontSize': 12, 'color': '#2E75B6',
                                        'fontWeight': '600', 'paddingTop': 4}),
                        html.Div(table, style={'flex': 1}),
                    ], style={'display': 'flex', 'padding': '10px 14px',
                               'borderBottom': f'1px solid #F0F4F8', 'gap': 12,
                               'alignItems': 'flex-start'}))
                continue

            # Determine if this column has a scoring badge to show.
            # q6 and q10 are handled in the section header — skip them here.
            _HEADER_BADGE_KEYS = {'q6', 'q10'}
            score_key = PREFIX_TO_SCORE_KEY.get(prefix)
            badge = None
            if score_key and score_key not in shown_score_keys and score_key not in _HEADER_BADGE_KEYS:
                shown_score_keys.add(score_key)
                def _sig_from(v): return 'positive' if v > 0 else ('negative' if v < 0 else 'neutral')
                tup = breakdowns[0].get(score_key, (0, 0, 'neutral'))
                badge = score_badges(_sig_from(tup[0]), _sig_from(tup[1]))

            # ── Checkbox groups ──────────────────────────────────────
            if col in binary_cols:
                gkey = (sec, prefix)
                if gkey in rendered_bin_groups:
                    continue
                rendered_bin_groups.add(gkey)
                group_members = [c for c in cols
                                 if c in binary_cols and c.split(':')[0].strip() == prefix]

                label = get_col_label(group_members[0])

                val_cells = []
                for (row_s, suffix, accent) in rows_list:
                    checked = []
                    for c in group_members:
                        v = row_s.get(c)
                        try:
                            if pd.notna(v) and float(v) == 1.0:
                                checked.append(get_checkbox_label(c))
                        except Exception:
                            pass
                    if checked:
                        cell = html.Div([
                            html.Span(c, style={
                                'display': 'inline-block', 'padding': '2px 8px',
                                'borderRadius': 10, 'fontSize': 11, 'fontWeight': '500',
                                'background': '#F2F2F2',
                                'color': '#444',
                                'border': '1px solid #D0D0D0',
                                'margin': '2px 3px 2px 0',
                            }) for c in checked
                        ], style={'display': 'flex', 'flexWrap': 'wrap', 'gap': 2})
                    else:
                        cell = html.Span("—", style={'fontSize': 12, 'color': '#bbb',
                                                      'fontStyle': 'italic'})
                    val_cells.append(cell)

                row_els.append(_field_row(label, val_cells, is_diff, rows_list, badge=badge))

            # ── Free-text / single-value fields ──────────────────────
            else:
                label = get_col_label(col)
                val_cells = []
                for (row_s, suffix, accent) in rows_list:
                    v = row_s.get(col)
                    if pd.isna(v) or str(v).strip() in ['', 'nan']:
                        cell = html.Span("—", style={'fontSize': 12, 'color': '#ccc',
                                                      'fontStyle': 'italic'})
                    else:
                        cell = html.Span(str(v), style={'fontSize': 12, 'color': '#111',
                                                         'wordBreak': 'break-word'})
                    val_cells.append(cell)

                if is_diff and len(val_cells) == 2:
                    v0 = str(rows_list[0][0].get(col, '')).strip()
                    v1 = str(rows_list[1][0].get(col, '')).strip()
                    neither_empty = not (v0 in ['', 'nan'] and v1 in ['', 'nan'])
                    if v0 != v1 and neither_empty:
                        val_cells = [
                            html.Div(val_cells[0], style={'background': '#FFF9E6',
                                                           'borderRadius': 4, 'padding': '2px 4px'}),
                            html.Div(val_cells[1], style={'background': '#FFF9E6',
                                                           'borderRadius': 4, 'padding': '2px 4px'}),
                        ]

                row_els.append(_field_row(label, val_cells, is_diff, rows_list, badge=badge))

        if row_els:
            # For sections whose score combines multiple columns (q6, q10),
            # show the DCC/OC badge in the section header instead of a field row.
            _SECTION_BADGE_KEYS = {
                'Security & Logging': 'q6',
                'API & Data Exchange': 'q10',
            }
            def _sig_from(v): return 'positive' if v > 0 else ('negative' if v < 0 else 'neutral')
            sec_badge = None
            sec_score_key = _SECTION_BADGE_KEYS.get(sec)
            if sec_score_key:
                tup = breakdowns[0].get(sec_score_key, (0, 0, 'neutral'))
                sec_badge = score_badges(_sig_from(tup[0]), _sig_from(tup[1]))

            header_children = [
                html.Span(sec, style={'textTransform': 'uppercase', 'letterSpacing': '0.04em'}),
            ]
            if sec_badge:
                header_children.append(sec_badge)

            cards.append(html.Div([
                html.Div(header_children, style={
                    'background': '#EDF4FB', 'padding': '6px 14px',
                    'fontSize': 11, 'fontWeight': '700', 'color': BLUE,
                    'borderBottom': f'1px solid {LIGHT}',
                    'display': 'flex', 'alignItems': 'center', 'gap': 8,
                }),
                html.Div(row_els),
            ], style={
                'border': f'1px solid {LIGHT}', 'borderLeft': f'4px solid {BLUE}',
                'borderRadius': 6, 'marginBottom': 8, 'background': WHITE, 'overflow': 'hidden',
            }))

    # ── Scoring legend ───────────────────────────────────────────────
    legend = html.Div([
        html.Span("DCC / OC score impact: ", style={'fontSize': 11, 'color': GREY, 'fontWeight': '600', 'marginRight': 6}),
        *[html.Span(
            [html.Span(cfg['icon'], style={'marginRight': 3}), cfg['label']],
            style={
                'display': 'inline-flex', 'alignItems': 'center',
                'padding': '1px 8px', 'borderRadius': 10, 'fontSize': 10,
                'border': f"1px solid {cfg['border']}",
                'backgroundColor': cfg['bg'], 'color': cfg['color'],
                'fontWeight': '700', 'marginRight': 6,
            }
        ) for cfg in _SIGNAL_CFG.values()],
        html.Span("·", style={'color': '#ccc', 'margin': '0 6px'}),
        html.Span("Badges appear on scored questions only.", style={'fontSize': 10, 'color': '#aaa', 'marginLeft': 8}),
    ], style={
        'display': 'flex', 'flexWrap': 'wrap', 'alignItems': 'center',
        'padding': '8px 14px', 'marginBottom': 10,
        'background': '#FAFCFF', 'border': f'1px solid {LIGHT}',
        'borderRadius': 6, 'gap': 4,
    })

    return html.Div([legend] + cards) if cards else html.Div(
        "No sections selected.", style={'color': GREY, 'padding': 16}
    )

# ─────────────────────────── PARSE / LOAD ───────────────────────────
def parse_upload(contents, filename):
    _, cs = contents.split(',')
    decoded = base64.b64decode(cs)
    if filename.lower().endswith(('.xlsx', '.xls')):
        return pd.read_excel(io.BytesIO(decoded))
    try:    return pd.read_csv(io.StringIO(decoded.decode('utf-8')))
    except: return pd.read_csv(io.StringIO(decoded.decode('latin-1')))

DEFAULT_CSV = os.environ.get('SURVEY_CSV', '')

def try_load_default():
    if DEFAULT_CSV and os.path.exists(DEFAULT_CSV):
        try:
            return pd.read_excel(DEFAULT_CSV) if DEFAULT_CSV.lower().endswith(('.xlsx', '.xls')) \
                   else pd.read_csv(DEFAULT_CSV)
        except Exception:
            pass
    return pd.DataFrame()

def prepare_data(raw_df):
    if raw_df.empty:
        empty = pd.DataFrame(columns=[
            'Jurisdiction', 'Short', 'Respondent',
            'Data Connection Complexity', 'Operational Complexity',
            'Readiness Band', '_color_idx', '_x', '_y',
        ])
        return raw_df, empty
    clean = deduplicate(raw_df)
    scores = calculate_scores(clean)
    return clean, scores

initial_raw, initial_scores = prepare_data(try_load_default())

# ─────────────────────────── LAYOUT ─────────────────────────────────
app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server

@server.route('/healthcheck')
def healthcheck():
    return 'ok', 200

def build_section_filter(sections_present):
    options = [{'label': s, 'value': s} for s in sections_present]
    return html.Details([
        html.Summary("⚙ Filter question sections", style={
            'cursor': 'pointer', 'fontWeight': '600', 'color': BLUE, 'fontSize': 13,
            'padding': '7px 12px', 'backgroundColor': '#EDF4FB',
            'borderRadius': '5px 5px 0 0', 'listStyle': 'none', 'userSelect': 'none',
        }),
        html.Div([
            html.Span("Select which sections to display:", style={
                'fontSize': 11, 'color': GREY, 'display': 'block', 'marginBottom': 6,
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
        ], style={'padding': '10px 14px', 'border': f'1px solid {LIGHT}',
                  'borderTop': 'none', 'borderRadius': '0 0 5px 5px', 'background': '#FAFCFF'}),
    ], style={'border': f'1px solid {LIGHT}', 'borderRadius': 6, 'marginBottom': 12})

app.layout = html.Div([
    html.H1("PT Readiness Dashboard",
            style={'color': BLUE, 'textAlign': 'center', 'fontFamily': 'Arial',
                   'fontSize': 22, 'marginBottom': 16, 'marginTop': 12}),

    dcc.Upload(id='upload-data',
               children=html.Div(['Drag & drop or ', html.A('select a CSV / Excel file')]),
               style={'width': '100%', 'height': '50px', 'lineHeight': '50px',
                      'borderWidth': '1.5px', 'borderStyle': 'dashed', 'borderRadius': 6,
                      'textAlign': 'center', 'marginBottom': 16, 'color': GREY,
                      'backgroundColor': '#FAFAFA', 'fontSize': 13},
               multiple=False),

    dcc.Store(id='scores-store',   data=initial_scores.to_json(date_format='iso', orient='split')),
    dcc.Store(id='raw-data-store', data=initial_raw.to_json(date_format='iso', orient='split')),

    # ── VIEWER ──────────────────────────────────────────────────────
    html.H3("Survey Response Viewer",
            style={'color': BLUE, 'marginTop': 4, 'marginBottom': 8,
                   'fontFamily': 'Arial', 'fontSize': 16}),
    html.Div([
        html.Div([
            html.Label("Jurisdiction:", style={'fontWeight': 'bold', 'marginRight': 8,
                                               'fontSize': 13, 'color': GREY}),
            dcc.Dropdown(
                id='raw-jurisdiction-dropdown',
                options=[{'label': j, 'value': j} for j in (
                    initial_raw[JUR_COL].unique() if not initial_raw.empty else []
                )],
                value=None, placeholder="Choose a jurisdiction...",
                clearable=False,
                style={'width': '320px', 'display': 'inline-block', 'fontSize': 13},
            ),
        ], style={'marginBottom': 10}),
        html.Div(id='section-filter-container'),
    ], style={'fontFamily': 'Arial'}),

    html.Div(id='raw-data-table', style={
        'maxHeight': '580px', 'overflowY': 'auto',
        'border': f'1px solid {LIGHT}', 'borderRadius': 6,
        'backgroundColor': WHITE, 'marginBottom': 24, 'fontFamily': 'Arial',
    }),

    html.Hr(style={'borderColor': LIGHT, 'margin': '0 0 20px 0'}),

    # ── SCORES TABLE ────────────────────────────────────────────────
    html.H3("Technical Readiness Scores (normalized −1 to +1)",
            style={'marginTop': 0, 'color': BLUE, 'fontFamily': 'Arial',
                   'fontSize': 16, 'marginBottom': 8}),

    dash_table.DataTable(
        id='summary-table',
        columns=[
            {'name': 'Jurisdiction',                        'id': 'Jurisdiction'},
            {'name': 'Respondent',                          'id': 'Respondent'},
            {'name': 'Data Connection Complexity',          'id': 'Data Connection Complexity'},
            {'name': 'Operational Complexity',              'id': 'Operational Complexity'},
            {'name': 'Readiness Band',                      'id': 'Readiness Band'},
        ],
        style_header={'backgroundColor': BLUE, 'color': WHITE, 'fontWeight': 'bold',
                      'fontSize': 12, 'textAlign': 'center'},
        style_data={'fontSize': 11, 'textAlign': 'center', 'padding': '5px 10px'},
        style_data_conditional=[
            {'if': {'row_index': 'odd'}, 'backgroundColor': LGREY},
            {'if': {'filter_query': '{Data Connection Complexity} > 0',
                    'column_id': 'Data Connection Complexity'}, 'color': GREEN, 'fontWeight': 'bold'},
            {'if': {'filter_query': '{Data Connection Complexity} < 0',
                    'column_id': 'Data Connection Complexity'}, 'color': RED, 'fontWeight': 'bold'},
            {'if': {'filter_query': '{Operational Complexity} > 0',
                    'column_id': 'Operational Complexity'}, 'color': GREEN, 'fontWeight': 'bold'},
            {'if': {'filter_query': '{Operational Complexity} < 0',
                    'column_id': 'Operational Complexity'}, 'color': RED, 'fontWeight': 'bold'},
            {'if': {'filter_query': '{Readiness Band} = "High"',
                    'column_id': 'Readiness Band'}, 'backgroundColor': LGREEN, 'color': 'black'},
            {'if': {'filter_query': '{Readiness Band} = "Moderate"',
                    'column_id': 'Readiness Band'}, 'backgroundColor': '#FFF2CC', 'color': 'black'},
            {'if': {'filter_query': '{Readiness Band} = "Low"',
                    'column_id': 'Readiness Band'}, 'backgroundColor': '#FCE4D6', 'color': 'black'},
            {'if': {'filter_query': '{Readiness Band} = "Very Low"',
                    'column_id': 'Readiness Band'}, 'backgroundColor': '#F4CCCC', 'color': 'black'},
        ],
        style_cell_conditional=[
            {'if': {'column_id': 'Jurisdiction'}, 'textAlign': 'left'},
            {'if': {'column_id': 'Respondent'},   'textAlign': 'left', 'fontSize': 11},
        ],
        style_table={'overflowX': 'auto'},
    ),

    html.Hr(style={'borderColor': LIGHT, 'margin': '20px 0'}),

    # ── CHART ───────────────────────────────────────────────────────
    html.H3("Adoption Complexity Matrix",
            style={'marginTop': 0, 'color': BLUE, 'fontFamily': 'Arial', 'fontSize': 16,
                   'marginBottom': 4, 'textAlign': 'center'}),
    dcc.Graph(id='bubble-chart', figure=create_bubble_chart(initial_scores),
              style={'width': '100%'}),

], style={'maxWidth': '1100px', 'margin': '0 auto', 'padding': '0 20px', 'fontFamily': 'Arial'})

# ─────────────────────────── CALLBACKS ──────────────────────────────
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

    display_cols = ['Jurisdiction', 'Respondent', 'Data Connection Complexity',
                    'Operational Complexity', 'Readiness Band']
    table_rows = scores[display_cols].to_dict('records') if not scores.empty else []

    fig = create_bubble_chart(scores)

    all_jurs = list(clean_df[JUR_COL].unique()) if not clean_df.empty else []
    jur_options = [{'label': j, 'value': j} for j in all_jurs]
    jur_value   = all_jurs[0] if all_jurs else None

    seen_sections = []
    for col in (clean_df.columns if not clean_df.empty else []):
        sec = assign_section(col)
        if sec not in seen_sections:
            seen_sections.append(sec)
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
                        style={'color': GREY, 'padding': 20, 'fontStyle': 'italic', 'fontSize': 13})

    raw_df  = pd.read_json(raw_json, orient='split')
    matched = raw_df[raw_df[JUR_COL] == jurisdiction]

    if matched.empty:
        return html.Div(f"No data for {jurisdiction}.", style={'color': GREY, 'padding': 16})

    jur_color_map = {}
    for ci, jur in enumerate(raw_df[JUR_COL].unique()):
        jur_color_map[str(jur).strip()] = PALETTE[ci % len(PALETTE)]
    accent = jur_color_map.get(str(jurisdiction).strip(), BLUE)

    if len(matched) == 1:
        rows_list = [(matched.iloc[0], '', accent)]
        header = None
    else:
        shades = [accent, _lighten(accent, 0.40)]
        rows_list = []
        for i, (_, row_s) in enumerate(matched.iterrows()):
            date_str = str(row_s.get('Date', '')).strip()
            rows_list.append((row_s, f"Respondent {i+1} ({date_str})", shades[i % len(shades)]))

        header = html.Div([
            html.Div("Two respondents submitted for this province — differences highlighted",
                     style={'background': '#F0F7FF', 'border': f'1px solid {MID}',
                            'borderRadius': 5, 'padding': '7px 14px', 'marginBottom': 8,
                            'fontSize': 12, 'color': BLUE, 'fontWeight': '600'}),
            html.Div([
                html.Div([
                    html.Span("●", style={'color': rows_list[i][2], 'marginRight': 5, 'fontSize': 16}),
                    html.Span(rows_list[i][1], style={'fontSize': 12, 'fontWeight': '600'}),
                ], style={'flex': 1, 'paddingLeft': 8 if i > 0 else 0})
                for i in range(len(rows_list))
            ], style={'display': 'flex', 'gap': 8, 'marginBottom': 8, 'paddingLeft': '30%'}),
        ])

    content = render_viewer(rows_list, raw_df, selected_sections or [])
    return html.Div([header, content] if header else [content])


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8050, debug=False)