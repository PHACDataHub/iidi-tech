"""
summary_tables.py
─────────────────
Generates collapsible summary table sections for the PT Readiness portal.
Matches the structure and question titles from the PT Readiness Sub-Report
appendices (Word doc). Import and call build_summary_section(df) + register_callbacks(app).

Usage in app.py:
    from ui.pages.summary_tables import build_summary_section, register_callbacks
    register_callbacks(app)
    # In on_upload return: build_summary_section(clean_df)
"""

import pandas as pd
from dash import html, dcc

# ─────────────────────────── STYLE CONSTANTS ─────────────────────────
BLUE      = '#2E75B6'
DARK_BLUE = '#1F4E79'
PART_BG   = '#1A3A5C'
PART2_BG  = '#5C4A1E'
SEC_BG    = '#EDF4FB'
BORDER    = '#CCDFF0'
HDR_BG    = '#2E75B6'
HDR_FG    = '#FFFFFF'
ROW_ALT   = '#F2F7FB'
ROW_NORM  = '#FFFFFF'

# ─────────────────────────── HELPERS ─────────────────────────────────

def _is_checked(val):
    try:
        return pd.notna(val) and float(val) == 1.0
    except Exception:
        return False


def _count(df, col):
    """Count checked (==1) or non-empty free-text responses."""
    if col not in df.columns:
        return 0
    s = df[col]
    if s.dtype in ['float64', 'int64']:
        return int((s == 1).sum())
    # Free-text: count non-empty non-null
    return int(s.dropna().astype(str).str.strip()
               .replace({'': None, 'nan': None, '0': None, '0.0': None})
               .dropna().shape[0])


def _count_col(df, col):
    """Notebook Cell 9 style: numeric==1, text notna+non-empty."""
    if col not in df.columns:
        return 0
    s = df[col]
    if s.dtype in ['float64', 'int64']:
        return int((s == 1).sum())
    return int(((s.notna()) & (s.astype(str).str.strip() != '')).sum())


def _yes_no_count(df, col):
    if col not in df.columns:
        return 0, 0, 0
    yes   = int((df[col].astype(str).str.strip() == 'Yes').sum())
    no    = int((df[col].astype(str).str.strip() == 'No').sum())
    blank = len(df) - yes - no
    return yes, no, blank


def _pct(n, total):
    if total == 0:
        return '—'
    return f'{round(100 * n / total)}%'


# ─────────────────────────── TABLE PRIMITIVES ────────────────────────

def _th(txt, wrap=False):
    return html.Th(txt, style={
        'backgroundColor': HDR_BG, 'color': HDR_FG,
        'padding': '7px 12px', 'fontSize': 12, 'fontWeight': '600',
        'borderRight': f'1px solid {DARK_BLUE}',
        'whiteSpace': 'normal' if wrap else 'nowrap',
        'textAlign': 'left', 'verticalAlign': 'bottom',
        'minWidth': '80px',
    })


def _td(txt, alt=False):
    return html.Td(str(txt), style={
        'padding': '6px 12px', 'fontSize': 12,
        'borderBottom': f'1px solid {BORDER}',
        'borderRight': f'1px solid {BORDER}',
        'backgroundColor': ROW_ALT if alt else ROW_NORM,
    })


def _tbl(headers, rows, wrap_headers=False):
    """Build a full table. headers: list of str. rows: list of list of values."""
    head = html.Thead(html.Tr([_th(h, wrap=wrap_headers) for h in headers]))
    body = html.Tbody([
        html.Tr([_td(cell, alt=(i % 2 == 1)) for cell in row])
        for i, row in enumerate(rows)
    ])
    return html.Table([head, body], style={
        'width': '100%', 'borderCollapse': 'collapse',
        'border': f'1px solid {BORDER}', 'marginBottom': 12,
        'tableLayout': 'fixed' if wrap_headers else 'auto',
    })


def _q_title(text):
    """Question title block matching word doc style."""
    return html.Div(text, style={
        'fontSize': 12, 'fontWeight': '600', 'color': DARK_BLUE,
        'backgroundColor': SEC_BG,
        'padding': '7px 12px',
        'borderLeft': f'4px solid {BLUE}',
        'marginTop': 14, 'marginBottom': 6,
        'lineHeight': '1.5',
    })


def _note(text):
    return html.P(text, style={
        'fontSize': 11, 'color': '#666', 'fontStyle': 'italic',
        'margin': '4px 0 10px 0',
    })


def _sec_header(text):
    return html.Div(text, style={
        'fontSize': 13, 'fontWeight': '700', 'color': DARK_BLUE,
        'borderBottom': f'2px solid {BLUE}',
        'paddingBottom': 5, 'marginTop': 18, 'marginBottom': 10,
        'letterSpacing': '0.02em',
    })


# ─────────────────────────── SECTION BUILDERS ────────────────────────

def _build_section1(df, n):
    """Section 1 — Immunization Data Collection"""

    # Q1 — bucket free-text responses
    COL_Q1 = '3: 1. What types of information systems or tools capture/document information on immunizations administered in your jurisdiction (E.g., EMRs, Pharmacy Systems, Hospital Systems, CANImmunize, Direct Entry into immunization registry/repository, etc.? Please specify.'
    import re as _re
    Q1_BUCKETS = {
        'EMRs / Clinical Information Systems': [
            'ehr', 'emr', 'panorama', 'paris', 'cedar', 'telus chr', 'ism',
            'physician', 'clinical information',
        ],
        'Pharmacy Systems': [
            'pharmacy', 'drug information system', 'mckesson', 'kroll',
        ],
        'Hospital / Acute Care Systems': [
            'hospital', 'cerner', 'acute care',
        ],
        'Direct Entry into Registry': [
            'direct entry', 'direct batch', 'idsm', 'direct submission',
            'public health nurs', 'clerk', 'pharmacist',
        ],
        'Long Term Care / Home Care Systems': [
            'long term care', 'long-term care', 'home care', 'alayacare',
            'peoplesoft', 'employee health', 'community care',
        ],
        'Citizen / Patient Reporting Tools (e.g. CANImmunize)': [
            'canimmunize', 'mobile', 'm-imms', 'yellow card',
            'paper reciprocal', 'patient portal',
        ],
        'Reconciliation / Exchange Tools': [
            'phix', 'stix', 'icon', 'immunizations connecting',
            'public health information exchange', 'fax', 'csv file', 'batch submission',
        ],
    }
    if COL_Q1 in df.columns:
        q1_responses = df[COL_Q1].dropna().astype(str).str.lower()
        bucket_counts = {}
        for bucket, keywords in Q1_BUCKETS.items():
            count = int(q1_responses.apply(
                lambda r: any(kw in r for kw in keywords)
            ).sum())
            bucket_counts[bucket] = count
    else:
        bucket_counts = {b: 0 for b in Q1_BUCKETS}
    q1_tbl = _tbl(
        ['System Class', 'Function', 'Count'],
        [
            ['EMRs / Clinical Information Systems',       'Capture & Document', bucket_counts.get('EMRs / Clinical Information Systems', 0)],
            ['Pharmacy Systems',                          'Capture & Document', bucket_counts.get('Pharmacy Systems', 0)],
            ['Hospital / Acute Care Systems',             'Capture & Document', bucket_counts.get('Hospital / Acute Care Systems', 0)],
            ['Direct Entry into Registry',                'Document',           bucket_counts.get('Direct Entry into Registry', 0)],
            ['Long Term Care / Home Care Systems',        'Capture & Document', bucket_counts.get('Long Term Care / Home Care Systems', 0)],
            ['Citizen / Patient Reporting Tools',         'Document',           bucket_counts.get('Citizen / Patient Reporting Tools (e.g. CANImmunize)', 0)],
            ['Reconciliation / Exchange Tools',           'Exchange',           bucket_counts.get('Reconciliation / Exchange Tools', 0)],
        ]
    )

    # Q2
    COL_Q2 = '4: 2. Does your jurisdiction have an official provincial/territorial immunization registry/repository?'
    yes2, no2, _ = _yes_no_count(df, COL_Q2)
    q2_tbl = _tbl(
        ['Number of Respondents Reporting Official Registry',
         'Number of Respondents Reporting No Official Registry'],
        [[yes2, no2]]
    )

    # Q3
    COL_Q3 = '5: 3. Is your registry/repository implemented using Panorama?'
    yes3, no3, _ = _yes_no_count(df, COL_Q3)
    q3_tbl = _tbl(
        ['Registry/Repository Type', 'Count'],
        [
            ['Panorama', yes3],
            ['Non-Panorama', no3],
        ]
    )

    # Q4 — care setting capture
    Q4_SETTINGS = {
        'Public Health': (
            '8.1: 1_Immunization events are routinely captured',
            '8.1: 1_Immunization events are occasionally captured',
            '8.1: 1_Immunization events are rarely captured',
        ),
        'Primary Care': (
            '8.1: 1_Immunization events are routinely captured.1',
            '8.1: 1_Immunization events are occasionally captured.1',
            '8.1: 1_Immunization events are rarely captured.1',
        ),
        'Pharmacy': (
            '8.1: 1_Immunization events are routinely captured.2',
            '8.1: 1_Immunization events are occasionally captured.2',
            '8.1: 1_Immunization events are rarely captured.2',
        ),
        'Hospital': (
            '8.1: 1_Immunization events are routinely captured.3',
            '8.1: 1_Immunization events are occasionally captured.3',
            '8.1: 1_Immunization events are rarely captured.3',
        ),
        'Other (E.g., non Publicly Funded Vaccines)': (
            '8.1: 1_Immunization events are routinely captured.4',
            '8.1: 1_Immunization events are occasionally captured.4',
            '8.1: 1_Immunization events are rarely captured.4',
        ),
    }
    q4_rows = []
    for setting, (r_col, o_col, ra_col) in Q4_SETTINGS.items():
        q4_rows.append([
            setting,
            int(df[r_col].sum())  if r_col  in df.columns else 0,
            int(df[o_col].sum())  if o_col  in df.columns else 0,
            int(df[ra_col].sum()) if ra_col in df.columns else 0,
        ])
    q4_tbl = _tbl(
        ['Setting', 'Immunization events are routinely captured',
         'Immunization events are occasionally captured',
         'Immunization events are rarely captured'],
        q4_rows
    )

    return html.Div([
        _q_title('Q #1 — What types of information systems or tools capture/document information on immunizations administered in your jurisdiction?'),
        _note('Answers are free text. Responses coded into categories below.'),
        q1_tbl,
        _q_title('Q #2 — Does your jurisdiction have an official provincial/territorial immunization registry/repository?'),
        q2_tbl,
        _q_title('Q #3 — Is your registry/repository implemented using Panorama?'),
        _note('a. If yes, please indicate which version of Panorama are you using? b. If No, please list the system name(s) and version(s).'),
        q3_tbl,
        _q_title('Q #4 — To what extent are immunization events captured in the provincial/territorial immunization registry/repository for each of the following care settings?'),
        q4_tbl,
    ])


def _build_section2(df, n):
    """Section 2 — Immunization Data Storage"""

    # Q5 hosting
    COL_Q5 = '9: 5. Where is your immunization registry/repository hosted?'
    cloud  = int((df[COL_Q5].astype(str).str.strip() == 'Cloud').sum())      if COL_Q5 in df.columns else 0
    onprem = int((df[COL_Q5].astype(str).str.strip() == 'On-premise').sum()) if COL_Q5 in df.columns else 0
    hybrid = int((df[COL_Q5].astype(str).str.strip() == 'Hybrid').sum())     if COL_Q5 in df.columns else 0
    q5_tbl = _tbl(['Cloud', 'On Premise', 'Hybrid'], [[cloud, onprem, hybrid]])

    # Q6/Q7 controls
    COL_6A = '10: 6a. Is there Auditing of Logins in place for all registry/repository access?'
    COL_6B = '11: 6b. Is there logging of user activities in place for all registry/repository transactions?'
    COL_7  = '12: 7. To ensure reliability and availability of data in the registry/repository, are there backups and mechanisms for disaster recovery?'
    ctrl_rows = []
    for resp in ['Yes', 'No']:
        ctrl_rows.append([
            resp,
            int((df[COL_6A] == resp).sum()) if COL_6A in df.columns else 0,
            int((df[COL_6B] == resp).sum()) if COL_6B in df.columns else 0,
            int((df[COL_7]  == resp).sum()) if COL_7  in df.columns else 0,
        ])
    ctrl_rows.append([
        'No Response',
        df[COL_6A].isna().sum() if COL_6A in df.columns else 0,
        df[COL_6B].isna().sum() if COL_6B in df.columns else 0,
        df[COL_7].isna().sum()  if COL_7  in df.columns else 0,
    ])
    ctrl_tbl = _tbl(
        ['Response',
         'Q #6a — Is there Auditing of Logins in place for all registry/repository access?',
         'Q #6b — Is there logging of user activities in place for all registry/repository transactions?',
         'Q #7 — Are there backups and mechanisms for disaster recovery?'],
        ctrl_rows,
        wrap_headers=True,
    )

    return html.Div([
        _q_title('Q #5 — Where is your immunization registry/repository hosted?'),
        q5_tbl,
        _q_title('Controls (Q #6a, Q #6b, Q #7)'),
        ctrl_tbl,
    ])


def _build_section3(df, n):
    """Section 3 — Immunization Data Access"""

    # Q8/Q9
    COL_Q8 = '13: 8. Does your jurisdiction currently have a digital tool that allows citizens to access their immunization information from the provincial immunization registry/repository?'
    yes8, no8, _ = _yes_no_count(df, COL_Q8)
    other_sys = int((df['14: Patient can access via another system'] == 1).sum()) if '14: Patient can access via another system' in df.columns else 0
    pt_req    = int((df['14: Patient can Request a copy of their Immunization Data'] == 1).sum()) if '14: Patient can Request a copy of their Immunization Data' in df.columns else 0
    other_q9  = int(df['14: Other, please specify'].notna().sum()) if '14: Other, please specify' in df.columns else 0

    q89_tbl = _tbl(
        ['Access Method', 'Count', 'Percent'],
        [
            ['PT provided digital tool',                      yes8,     _pct(yes8, n)],
            ['Patient can access via another system',         other_sys, _pct(other_sys, n)],
            ['Patient request / copy of immunization data',   pt_req,   _pct(pt_req, n)],
            ['Other',                                         other_q9, _pct(other_q9, n)],
        ]
    )

    # Q10 API — exact notebook Cell 9 logic
    api_no = int((df['15: 9. Does your registry/repository have externally accessible Application Programming Interfaces (API) covering functionality needed to access and exchange immunization data?'].astype(str).str.strip() == 'No').sum()) if '15: 9. Does your registry/repository have externally accessible Application Programming Interfaces (API) covering functionality needed to access and exchange immunization data?' in df.columns else 0
    q10_tbl = _tbl(
        ['API Access', 'Count'],
        [
            ['REST',           _count_col(df, '16: REST')],
            ['SOAP',           _count_col(df, '16: SOAP')],
            ['AMQP',           _count_col(df, '16: AMQP')],
            ['Other protocol', _count_col(df, '16: Other, please specify')],
            ['SAML auth',      _count_col(df, '17: SAML')],
            ['OAuth auth',     _count_col(df, '17: OAuth')],
            ['Custom / Other auth', _count_col(df, '17: Other, please specify')],
            ['No API access',  api_no],
        ]
    )

    return html.Div([
        _q_title('Q #8 & Q #9 — Does your jurisdiction currently have a digital tool that allows citizens to access their immunization information? If no, how can citizens access their immunization information?'),
        q89_tbl,
        _q_title('Q #10 — Does your registry/repository have externally accessible APIs covering functionality needed to access and exchange immunization data? (Q #10a — API Protocol, Q #10b — API Authentication, Q #10c — Alternate access methods)'),
        q10_tbl,
        _note(f'{api_no} respondent(s) reported no API access.'),
    ])


def _build_section4(df, n):
    """Section 4 — Immunization Data Sharing"""

    # Q11a
    q11a_tbl = _tbl(
        ['Collection System Class', 'Number of systems sharing with registry'],
        [
            ['EMRs',             _count(df, '19: EMRs')],
            ['Pharmacy Systems', _count(df, '19: Pharmacy Systems')],
            ['Hospitals',        _count(df, '19: Hospital')],
            ['Long Term Care',   _count(df, '19: Long Term Care')],
            ['Other',            _count(df, '19: Other, please specify')],
        ]
    )

    # Q11b
    q11b_tbl = _tbl(
        ['Data Exchange Mechanism', 'Usage Count'],
        [
            ['Real-time HL7',           _count(df, '20: Real-time HL7')],
            ['FHIR API',                _count(df, '20: FHIR API')],
            ['Batch Upload',            _count(df, '20: Batch upload')],
            ['CSV / XML',               _count(df, '20: CSV/XML')],
            ['Manual entry via Portal', _count(df, '20: Manual entry via portal')],
            ['Other',                   _count(df, '20: Other, please specify')],
        ]
    )

    # Q12
    q12_tbl = _tbl(
        ['Data Exchange Format / Standard', 'Usage Count'],
        [
            ['HL7 FHIR',         _count(df, '21: HL7 FHIR')],
            ['HL7 v2',           _count(df, '21: HL7 v2')],
            ['XML',              _count(df, '21: XML')],
            ['JSON',             _count(df, '21: JSON')],
            ['Flat Files / CSV', _count(df, '21: Flat files / CSV')],
            ['N/A',              _count(df, '21: N/A')],
            ['Other',            _count(df, '21: Other, please specify')],
        ]
    )

    # Q13
    q13_tbl = _tbl(
        ['Data Standard', 'Usage Count'],
        [
            ['SNOMED CT',                                         _count(df, '22: SNOMED CT')],
            ['National Vaccine Catalogue',                        _count(df, '22: National Vaccine Catalogue')],
            ['Immunization Functional Registry Standards (CIRC)', _count(df, '22: Immunization Functional Registry Standards (CIRC)')],
            ['Other',                                             _count(df, '22: Other standard, please specify')],
        ]
    )

    # Q14
    q14_tbl = _tbl(
        ['Inter-provincial Data Sharing Process', 'Usage Count'],
        [
            ['Record/Data transfer to other provinces/territories when residents move',
             _count(df, '23: Record/Data transfer to other provinces/territories when residents move')],
            ['Record/Data intake from other provinces/territories for individuals vaccinated elsewhere',
             _count(df, '23: Record/Data intake from other provinces/territories for individuals vaccinated elsewhere')],
            ['Consent management for inter-jurisdictional immunization record/data sharing',
             _count(df, '23: Consent management for inter- jurisdictional immunization record/data sharing')],
            ['Consent management for immunization record/data sharing within the jurisdiction',
             _count(df, '23: Consent management for immunization record/data sharing within the jurisdiction')],
            ['Records provided to Public Health directly by individuals',
             _count(df, '23: Records provided to Public Health directly by individuals')],
            ['Other',
             _count(df, '23: Other standard, please specify')],
        ]
    )

    # Q15/15a — mutually exclusive buckets (notebook Cell 15 logic)
    COL_15  = '24: 14. Are you currently upgrading or replacing any components of your immunization registry/repository or its technical ecosystem? (e.g., hosting environment, data exchange standards, interfaces with EMRs/EHRs, or other major system changes that will impact immunization data collection and sharing)'
    COL_15A = '25: 14a. If not, have any decisions or plans being made towards future upgrading or replacing of any components of your immunization registry/repository or its technical ecosystem?'
    if COL_15 in df.columns and COL_15A in df.columns:
        s15  = df[COL_15].astype(str).str.strip()
        s15a = df[COL_15A].astype(str).str.strip()
        currently = int((s15 == 'Yes').sum())
        planning  = int(((s15 != 'Yes') & (s15a == 'Yes')).sum())
        neither   = int(((s15 != 'Yes') & (s15a != 'Yes')).sum())
    else:
        currently = planning = neither = 0
    q15_tbl = _tbl(
        ['Currently Upgrading', 'Planning to Upgrade', 'Not Upgrading or Planning to Upgrade'],
        [[currently, planning, neither]]
    )

    # Q16
    q16_tbl = _tbl(
        ['Roadmap Process', 'Usage Count'],
        [
            ['PS-CA',                                        _count(df, '26: Yes: PS-CA')],
            ['Pan-Canadian Health Data Content Framework',   _count(df, '26: Yes: Pan-Canadian Health Data Content Framework')],
            ['CA:FeX',                                       _count(df, '26: Yes: CA:FeX')],
            ['None of the Above',                            _count(df, '26: No')],
        ]
    )

    return html.Div([
        _q_title('Q #11a — Of those systems collecting immunization data, which ones report immunization data to your registry/repository?'),
        q11a_tbl,
        _q_title('Q #11b — What mechanism is used to exchange data with the registry?'),
        q11b_tbl,
        _q_title('Q #12 — If immunization data are exchanged electronically with your registry, which data exchange formats or standards are used?'),
        q12_tbl,
        _q_title('Q #13 — Which standards (e.g., terminology, data exchange) does your immunization registry/repository use? Please select all that apply.'),
        q13_tbl,
        _q_title('Q #14 — Which immunization record/data sharing or inter-provincial transfer processes does your jurisdiction have in place?'),
        q14_tbl,
        _q_title('Q #15 & Q #15a — Are you currently upgrading or replacing any components of your immunization registry/repository or its technical ecosystem? If not, have any decisions or plans been made towards future upgrading or replacing?'),
        q15_tbl,
        _q_title('Q #16 — Is your jurisdiction participating in the Interoperability Roadmap with CIHI and Infoway including PS-CA, Pan-Canadian Health Data Content Framework, CA:FeX?'),
        q16_tbl,
    ])


def _build_section5(df, n):
    """Section 5 — Immunization Data Maintenance"""

    # Q17 — free text, listed verbatim as in notebook Cell 17
    COL_Q17 = '27: 16. How is the quality of data recorded in your Immunization Registry/repository assessed?'
    if COL_Q17 in df.columns:
        q17_responses = df[COL_Q17].dropna().reset_index(drop=True)
        q17_tbl = _tbl(
            ['Response'],
            [[str(v)] for v in q17_responses]
        )
    else:
        q17_tbl = _note('No Q17 data found.')

    # Q18
    q18_tbl = _tbl(
        ['Process', 'Usage Count'],
        [
            ['Provider corrections',                       _count(df, '28: Provider corrections')],
            ['Manual updates made directly in the registry/repository', _count(df, '28: Manual updates made directly in the registry/repository')],
            ['Automated/manual duplicate resolution',      _count(df, '28: Automated/manual duplicate resolution')],
            ['Other reconciliation processes',             _count(df, '28: Other reconciliation processes, please specify')],
        ]
    )

    # Q19
    q19_tbl = _tbl(
        ['Process', 'Usage Count'],
        [
            ['Patient can update their immunization record',           _count(df, '29: Patient can update their immunization record')],
            ['Patient can request a change to their immunization record', _count(df, '29: Patient can request a change to their immunization record')],
            ['Patient cannot update or request a change',              _count(df, '29: Patient cannot update or request a change')],
            ['Other',                                                  _count(df, '29: Other, please specify')],
        ]
    )

    return html.Div([
        _q_title('Q #17 — How is the quality of data recorded in your Immunization Registry/repository assessed? (Free-text responses)'),
        _note('Answers are free text. Raw responses shown below.'),
        q17_tbl,
        _q_title('Q #18 — When data quality issues are identified, how are they remediated in your registry/repository? Please select all that apply.'),
        q18_tbl,
        _q_title('Q #19 — When a patient identifies data quality issues, how are they remediated in your registry/repository? Please select all that apply.'),
        q19_tbl,
    ])


def _build_section6(df, n):
    """Section 6 — Archiving"""

    # Q20
    COL_Q20 = '30: 19. Is Immunization data ever archived?'
    yes20, no20, blank20 = _yes_no_count(df, COL_Q20)
    q20_tbl = _tbl(
        ['Archive Method', 'Usage Count'],
        [
            ['Archived',     yes20],
            ['Not Archived', no20],
            ['No Response',  blank20],
        ]
    )

    # Q21 free text
    COL_Q21 = '31: 20. When and how is data archived in the immunization registry/repository?'
    if COL_Q21 in df.columns:
        q21_responses = df[COL_Q21].dropna().reset_index(drop=True)
        q21_tbl = _tbl(['Response'], [[str(v)] for v in q21_responses])
    else:
        q21_tbl = _note('No Q21 data found.')

    return html.Div([
        _q_title('Q #20 — Is Immunization data ever archived?'),
        q20_tbl,
        _q_title('Q #21 — When and how is data archived in the immunization registry/repository? (Free-text responses)'),
        _note('Methods extracted from free-text responses.'),
        q21_tbl,
    ])


def _build_part2(df, n):
    """Part 2 — Governance & Context"""

    # Q22
    q22_tbl = _tbl(
        ['Custodian', 'Usage Count'],
        [
            ['Ministry of Health',                                _count(df, '32: Ministry of Health')],
            ['Public Health/Office of the Medical Health Officer', _count(df, '32: Public Health/Office of the Medical Health Officer')],
            ['Central Health Authorities',                        _count(df, '32: Central Health Authorities')],
            ['Other',                                             _count(df, '32: Other, please specify')],
        ]
    )

    # Q23 — who administers (checkbox per setting)
    Q23_SETTINGS = [
        ('Public Health Office',    '33.1'),
        ('Primary Care',            '33.2'),
        ('Community Health Centre', '33.3'),
        ('School',                  '33.4'),
        ('Pharmacy',                '33.5'),
        ('Acute Care Facilities',   '33.6'),
        ('Long Term Care Facilities','33.7'),
        ('Other',                   '33.8'),
    ]
    q23_rows = []
    for setting, prefix in Q23_SETTINGS:
        # find matching col
        col = next((c for c in df.columns if str(c).split(':')[0].strip() == prefix), None)
        count = _count(df, col) if col else 0
        q23_rows.append([setting, count])
    q23_tbl = _tbl(['Setting', 'Count'], q23_rows)

    # Q24 — care settings by immunization type
    IMM_TYPES = ['Childhood Immunizations', 'Flu / COVID Immunizations', 'Travel Immunizations',
                 'Adult Immunizations', 'Adolescent Immunizations', 'High Risk Immunizations',
                 'Post-Exposure Immunizations']
    Q24_PREFIXES = ['34.1', '34.2', '34.3', '34.4', '34.5', '34.6', '34.7']
    q24_cols = []
    for prefix in Q24_PREFIXES:
        col = next((c for c in df.columns if str(c).split(':')[0].strip() == prefix), None)
        q24_cols.append(col)
    q24_settings = ['Public Health Office', 'Primary Care', 'Community Health Centre',
                    'School', 'Pharmacy', 'Acute Care Facilities', 'Other']
    # Q24 is complex free-text per cell; show counts of non-empty responses per type
    q24_rows = []
    for i, imm_type in enumerate(IMM_TYPES):
        col = q24_cols[i]
        count = int(df[col].notna().sum()) if col and col in df.columns else 0
        q24_rows.append([imm_type, count])
    q24_tbl = _tbl(['Immunization Type', 'Number of Jurisdictions Reporting'], q24_rows)

    # Q27
    q27_tbl = _tbl(
        ['Regulatory Framework', 'Usage Count'],
        [
            ['Provincial Immunization Manual',  _count(df, '37: Provincial Immunization Manual')],
            ['Data Sharing Agreements',          _count(df, '37: Data Sharing Agreements')],
            ['Immunization Data Policies',       _count(df, '37: Immunization Data Policies')],
            ['Immunization Data Procedures',     _count(df, '37: Immunization Data Procedures')],
            ['Other',                            _count(df, '37: Other, please specify')],
        ]
    )

    # Q28
    q28_tbl = _tbl(
        ['Challenge', 'Usage Count'],
        [
            ['Data Completeness',                              _count(df, '38: Data completeness')],
            ['Siloed/disconnected approaches to data stewardship', _count(df, '38: Siloed/disconnected approaches to data stewardship')],
            ['Legislative limitations',                        _count(df, '38: Legislative limitations')],
            ['Lack of system integration',                     _count(df, '38: Lack of system integration')],
            ['Other',                                          _count(df, '38: Other, please specify')],
        ]
    )

    return html.Div([
        _q_title('Q #22 — Who is the custodian/business owner of immunization registry/repository data in your jurisdiction? Please select all that apply.'),
        q22_tbl,
        _q_title('Q #23 — Who administers immunizations in each of the settings identified?'),
        q23_tbl,
        _q_title('Q #24 — Please list all care settings where the listed immunization types are administered.'),
        q24_tbl,
        _note('Q #25 (adverse events) and Q #26 (vaccine inventory) are free-text; detailed responses shown in the jurisdiction viewer.'),
        _q_title('Q #27 — What legislation, regulations, and agreements govern the sharing of immunization data in your jurisdiction?'),
        q27_tbl,
        _q_title('Q #28 — What clinical/business/technical challenges do you have in sharing immunization information? Please select all that apply.'),
        q28_tbl,
    ])


# ─────────────────────────── COLLAPSIBLE WRAPPER ─────────────────────

def _collapsible(section_id, title, content, bg_color=BLUE):
    return html.Div([
        html.Button(
            [html.Span('\u25b8 ', id=f'arrow-{section_id}'), title],
            id=f'btn-{section_id}',
            n_clicks=0,
            style={
                'width': '100%', 'textAlign': 'left',
                'backgroundColor': bg_color, 'color': '#FFFFFF',
                'border': 'none', 'padding': '9px 14px',
                'fontSize': 13, 'fontWeight': '600',
                'cursor': 'pointer', 'borderRadius': '4px 4px 0 0',
                'letterSpacing': '0.02em',
            }
        ),
        html.Div(
            content,
            id=f'body-{section_id}',
            style={
                'display': 'none', 'padding': '14px 16px',
                'border': f'1px solid {BORDER}', 'borderTop': 'none',
                'borderRadius': '0 0 4px 4px', 'backgroundColor': '#FAFCFF',
            }
        ),
    ], style={'marginBottom': 8})


# ─────────────────────────── MAIN ENTRY POINT ────────────────────────

SECTION_IDS = ['sec1', 'sec2', 'sec3', 'sec4', 'sec5', 'sec6', 'part2']

def build_summary_section(df):
    """
    Given the full survey DataFrame, return a collapsible Dash html.Div
    containing all summary tables organised by section, matching the
    PT Readiness Sub-Report appendices structure.
    """
    if df is None or df.empty:
        return html.Div()

    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    n = len(df)

    SECTIONS = [
        ('sec1', 'Section 1 — Immunization Data Collection',  _build_section1, BLUE),
        ('sec2', 'Section 2 — Immunization Data Storage',     _build_section2, BLUE),
        ('sec3', 'Section 3 — Immunization Data Access',      _build_section3, BLUE),
        ('sec4', 'Section 4 — Immunization Data Sharing',     _build_section4, BLUE),
        ('sec5', 'Section 5 — Immunization Data Maintenance', _build_section5, BLUE),
        ('sec6', 'Section 6 — Archiving',                     _build_section6, BLUE),
        ('part2','Part 2 — Governance & Context',             _build_part2,    '#5C4A1E'),
    ]

    part1_header = html.Div('Part 1 — Technical Readiness Assessment', style={
        'backgroundColor': PART_BG, 'color': '#FFFFFF',
        'fontSize': 14, 'fontWeight': '700',
        'padding': '10px 16px', 'borderRadius': 6,
        'marginBottom': 8, 'marginTop': 4, 'letterSpacing': '0.03em',
    })
    part2_header = html.Div('Part 2 — Governance & Context', style={
        'backgroundColor': PART2_BG, 'color': '#FFFFFF',
        'fontSize': 14, 'fontWeight': '700',
        'padding': '10px 16px', 'borderRadius': 6,
        'marginBottom': 8, 'marginTop': 16, 'letterSpacing': '0.03em',
    })

    part1_cards, part2_cards = [], []
    for sid, title, builder, color in SECTIONS:
        try:
            content = builder(df, n)
        except Exception as e:
            content = html.P(f'Error: {e}', style={'color': 'red', 'fontSize': 12})
        card = _collapsible(sid, title, content, bg_color=color)
        (part2_cards if sid == 'part2' else part1_cards).append(card)

    inner = html.Div(
        [part1_header, *part1_cards, part2_header, *part2_cards],
        id='summary-body',
        style={'display': 'none', 'marginTop': 8}
    )

    toggle_btn = html.Button(
        [html.Span('\u25b8 ', id='summary-arrow'),
         'Summary Tables \u2014 Survey Response Counts (Appendix C)'],
        id='summary-toggle',
        n_clicks=0,
        style={
            'width': '100%', 'textAlign': 'left',
            'backgroundColor': '#1A3A5C', 'color': '#FFFFFF',
            'border': 'none', 'padding': '11px 16px',
            'fontSize': 14, 'fontWeight': '700',
            'cursor': 'pointer', 'borderRadius': 6,
            'letterSpacing': '0.02em', 'marginBottom': 4,
        }
    )

    return html.Div([toggle_btn, inner], style={'marginBottom': 16})


# ─────────────────────────── CALLBACKS ───────────────────────────────

def register_callbacks(app):
    from dash import Input, Output, State

    @app.callback(
        Output('summary-body',  'style'),
        Output('summary-arrow', 'children'),
        Input('summary-toggle', 'n_clicks'),
        State('summary-body',   'style'),
        prevent_initial_call=True,
    )
    def toggle_summary(n, style):
        if style and style.get('display') == 'none':
            return {'display': 'block', 'marginTop': 8}, '\u25be '
        return {'display': 'none', 'marginTop': 8}, '\u25b8 '

    for sid in SECTION_IDS:
        @app.callback(
            Output(f'body-{sid}',  'style'),
            Output(f'arrow-{sid}', 'children'),
            Input(f'btn-{sid}',    'n_clicks'),
            State(f'body-{sid}',   'style'),
            prevent_initial_call=True,
        )
        def _toggle(n, style, _sid=sid):
            open_style = {
                'display': 'block', 'padding': '14px 16px',
                'border': f'1px solid {BORDER}', 'borderTop': 'none',
                'borderRadius': '0 0 4px 4px', 'backgroundColor': '#FAFCFF',
            }
            closed_style = {**open_style, 'display': 'none'}
            if style and style.get('display') == 'none':
                return open_style, '\u25be '
            return closed_style, '\u25b8 '