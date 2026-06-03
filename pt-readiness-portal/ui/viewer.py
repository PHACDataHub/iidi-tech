"""
viewer.py
─────────
Survey response viewer for the PT Readiness Dashboard.
Renders per-jurisdiction survey responses with rubric annotations,
score badges, checkbox groups, and section cards.

Public API
──────────
render_viewer(rows_list, raw_df, selected_sections)  →  html.Div
score_badges(dcc_signal, oc_signal)                  →  html.Span
_lighten(hex_color, factor)                          →  str
"""

import pandas as pd
from dash import html

from core.constants import (
    BLUE, MID, LIGHT, GREY, LGREY, WHITE,
    PALETTE,
    COL_META, SECTION_ORDER,
    PART_1_SECTIONS, PART_2_SECTIONS,
    PREFIX_TO_SCORE_KEY, SCORE_KEY_LABELS,
)
from core.scoring import score_row_breakdown, score_api_protocol, score_auth, score_10c

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

# ─────────────────────────── API & DATA EXCHANGE RENDERER ────────────
def _checkbox_item(label, checked, description=None):
    """Render a single checkbox item. Label on the left, box on the right."""
    box_style = {
        'width': 13, 'height': 13, 'borderRadius': 2,
        'border': '1.5px solid ' + ('#2E75B6' if checked else '#C0C0C0'),
        'backgroundColor': '#2E75B6' if checked else '#FFFFFF',
        'display': 'inline-flex', 'alignItems': 'center', 'justifyContent': 'center',
        'flexShrink': 0, 'marginTop': 1,
    }
    tick = html.Span(u'\u2713', style={
        'color': '#FFFFFF', 'fontSize': 9, 'lineHeight': 1, 'fontWeight': '700'
    }) if checked else None

    label_parts = [html.Span(label, style={
        'fontSize': 12,
        'color': '#111' if checked else '#999',
        'fontWeight': '600' if checked else '400',
    })]
    if description:
        label_parts.append(html.Span(
            u' \u2014 ' + description,
            style={'fontSize': 11, 'color': '#555', 'fontStyle': 'italic'}
        ))

    return html.Div([
        html.Div(label_parts, style={'flex': 1, 'display': 'flex',
                                      'flexWrap': 'wrap', 'alignItems': 'center'}),
        html.Div([tick] if tick else [], style=box_style),
    ], style={
        'display': 'flex', 'alignItems': 'flex-start', 'gap': 8,
        'padding': '3px 0', 'width': '100%',
    })


def _score_pill(score):
    """Small coloured pill showing a numeric score."""
    if score > 0:
        bg, fg, border = '#D5E8D4', '#375623', '#A9C9A0'
        txt = f'+{score}'
    elif score < 0:
        bg, fg, border = '#FFDCE1', '#C00000', '#F4A0A0'
        txt = str(score)
    else:
        bg, fg, border = '#FFF8DC', '#7F6B00', '#E0D080'
        txt = '0'
    return html.Span(txt, style={
        'display': 'inline-block', 'padding': '1px 7px', 'borderRadius': 8,
        'fontSize': 11, 'fontWeight': '700',
        'backgroundColor': bg, 'color': fg,
        'border': f'1px solid {border}', 'whiteSpace': 'nowrap',
    })


def _rubric_block(options, final_dcc=None, final_oc=None,
                  score_label='Score', section_final=None):
    """
    Amber rubric cell content.

    options       : list of (label, dcc, oc) tuples.
    final_dcc/oc  : sub-score or per-question score row (label = score_label).
    score_label   : label for the final_dcc/oc row  (default 'Score').
    section_final : dict with keys:
                      'formula'  str  e.g. 'min(10a, 10b, 10c)'
                      'if_yes'   int  computed value when Q10=Yes
                      'if_no'    int  value when Q10=No
                      'actual'   int  the actual computed score
                    When supplied a full-width section-score block is appended.
    """
    header = html.Div('RUBRIC', style={
        'fontSize': 9, 'fontWeight': '700', 'color': '#7A5C00',
        'letterSpacing': '0.07em', 'marginBottom': 5,
    })

    def _score_cell(val):
        if val is None:
            return html.Span('—', style={'fontSize': 11, 'color': '#B8960C'})
        return _score_pill(val)

    COL_W = {'width': 36, 'minWidth': 36, 'textAlign': 'center', 'flexShrink': 0}

    def _col_hdr(txt):
        return html.Div(txt, style={
            **COL_W,
            'fontSize': 9, 'fontWeight': '700', 'color': '#7A5C00',
            'letterSpacing': '0.05em',
        })

    # Table header row
    tbl_header = html.Div([
        html.Div('', style={'flex': 1}),
        _col_hdr('DCC'),
        _col_hdr('OC'),
    ], style={
        'display': 'flex', 'gap': 4, 'alignItems': 'center',
        'paddingBottom': 3, 'borderBottom': '1px solid #E8D070', 'marginBottom': 3,
    })

    # One row per option
    opt_rows = []
    for label, dcc_v, oc_v in options:
        opt_rows.append(html.Div([
            html.Span(label, style={
                'flex': 1, 'fontSize': 11, 'color': '#5A3E00', 'lineHeight': '1.4',
            }),
            html.Div(_score_cell(dcc_v), style=COL_W),
            html.Div(_score_cell(oc_v),  style=COL_W),
        ], style={
            'display': 'flex', 'gap': 4, 'alignItems': 'center',
            'padding': '2px 0', 'borderBottom': '1px solid #F5E8A0',
        }))

    children = [header, tbl_header] + opt_rows

    # Per-question score row
    if final_dcc is not None and final_oc is not None:
        children.append(html.Div([
            html.Span(score_label, style={
                'flex': 1, 'fontSize': 11, 'color': '#7A5C00', 'fontWeight': '700',
            }),
            html.Div(_score_pill(final_dcc), style=COL_W),
            html.Div(_score_pill(final_oc),  style=COL_W),
        ], style={
            'display': 'flex', 'gap': 4, 'alignItems': 'center',
            'padding': '4px 0 2px',
            'borderTop': '1px solid #E8D070', 'marginTop': 3,
        }))

    # Section-level final block (Q10c only)
    if section_final is not None:
        formula    = section_final.get('formula', '')
        if_yes     = section_final.get('if_yes')
        if_no      = section_final.get('if_no', -2)
        actual_dcc = section_final.get('actual_dcc')
        actual_oc  = section_final.get('actual_oc')
        active     = section_final.get('active', '')   # 'Yes', 'No', or ''

        yes_active = active == 'Yes'
        no_active  = active == 'No'

        def _sf_row(label, dcc_v, oc_v, bold=False, greyed=False):
            text_color  = '#C8B89A' if greyed else ('#5C3A00' if bold else '#7A5C00')
            pill_or_dash = (lambda v: html.Span(
                '—', style={'fontSize': 11, 'color': '#D4C4A0', 'textAlign': 'center',
                                  'display': 'block'})
            ) if greyed else _score_cell
            return html.Div([
                html.Span(label, style={
                    'flex': 1, 'fontSize': 10, 'color': text_color,
                    'fontWeight': '700' if bold else '400',
                    'fontStyle': 'italic' if not bold and not greyed else 'normal',
                }),
                html.Div(pill_or_dash(dcc_v), style=COL_W),
                html.Div(pill_or_dash(oc_v),  style=COL_W),
            ], style={'display': 'flex', 'gap': 4, 'alignItems': 'center', 'padding': '2px 0'})

        children.append(html.Div([
            html.Span('Q10 Final Score', style={
                'fontSize': 10, 'fontWeight': '700', 'color': '#5C3A00',
                'display': 'block', 'marginBottom': 5,
            }),
            # column headers
            html.Div([
                html.Div('', style={'flex': 1}),
                html.Div('DCC', style={**COL_W, 'fontSize': 9, 'fontWeight': '700',
                                        'color': '#7A5C00', 'letterSpacing': '0.05em'}),
                html.Div('OC',  style={**COL_W, 'fontSize': 9, 'fontWeight': '700',
                                        'color': '#7A5C00', 'letterSpacing': '0.05em'}),
            ], style={'display': 'flex', 'gap': 4,
                      'paddingBottom': 3, 'borderBottom': '1px solid #E8D070', 'marginBottom': 3}),
            _sf_row('If Yes: %s' % formula, if_yes, if_yes, greyed=no_active),
            _sf_row('If No', if_no, if_no, greyed=yes_active),
            html.Div(style={'borderTop': '1px solid #C8A000', 'margin': '4px 0'}),
            _sf_row('Final Score', actual_dcc, actual_oc, bold=True),
        ], style={
            'marginTop': 6,
            'borderTop': '2px solid #C8A000',
            'backgroundColor': '#FFF3CC',
            'borderRadius': 4, 'padding': '6px 8px',
        }))

    return html.Div(children)


def _citizen_access_checkboxes(row_s):
    """
    Returns [(label, checkbox_div, rubric_el), ...] for Q8 and Q9.
    Q8: Yes / No checkbox.
    Q9: shown when Q8 = No — Patient can access via another system /
        Patient can Request a copy / Other (free text).
    """
    def _is_checked(col):
        v = row_s.get(col)
        try:
            return pd.notna(v) and float(v) == 1.0
        except Exception:
            return False

    def _text(col):
        v = row_s.get(col)
        if pd.isna(v) or str(v).strip() in ['', 'nan', '0', '0.0']:
            return None
        return str(v).strip()

    def _checkboxes(*items):
        return html.Div(
            [_checkbox_item(*item) for item in items],
            style={'display': 'flex', 'flexDirection': 'column', 'gap': 2, 'width': '100%'}
        )

    q8_val  = str(row_s.get('13: 8. Does your jurisdiction currently have a digital tool that allows citizens to access their immunization information from the provincial immunization registry/repository?', '') or '').strip()
    other_q9 = _text('14: Other, please specify')

    # Q8 row
    q8_checkboxes = _checkboxes(('Yes', q8_val == 'Yes'), ('No', q8_val == 'No'))
    q8_rubric = _rubric_block(
        [('Yes', 0, 0), ('No', 0, 0)],
        final_dcc=0, final_oc=0,
    )

    # Q9 row — options only meaningful when Q8 = No
    q9_checkboxes = _checkboxes(
        ('Patient can access via another system', _is_checked('14: Patient can access via another system')),
        ('Patient can request a copy of their immunization data', _is_checked('14: Patient can Request a copy of their Immunization Data')),
        ('Other', bool(other_q9), other_q9) if other_q9 else ('Other', False),
    )
    q9_rubric = _rubric_block(
        [('Any option', 0, 0)],
        final_dcc=0, final_oc=0,
    )

    return [
        (
            'Q8 — Digital tool for citizen access?',
            q8_checkboxes,
            q8_rubric,
        ),
        (
            'Q9 — If no digital tool, how can citizens access their immunization information?',
            q9_checkboxes,
            q9_rubric,
        ),
    ]


def _section4_checkboxes(row_s):
    """
    Render Q11a, Q11b, Q12, Q13, Q14 as checkbox groups with no rubric card.
    Returns [(label, checkbox_div, None), ...]
    """
    def _is_checked(col):
        v = row_s.get(col)
        try:
            return pd.notna(v) and float(v) == 1.0
        except Exception:
            return False

    def _text(col):
        v = row_s.get(col)
        if pd.isna(v) or str(v).strip() in ['', 'nan', '0', '0.0']:
            return None
        return str(v).strip()

    def _checkboxes(*items):
        return html.Div(
            [_checkbox_item(*item) for item in items],
            style={'display': 'flex', 'flexDirection': 'column', 'gap': 2, 'width': '100%'}
        )

    other_q11a = _text('19: Other, please specify')
    other_q11b = _text('20: Other, please specify')
    other_q12  = _text('21: Other, please specify')
    other_q13  = _text('22: Other standard, please specify')
    other_q14  = _text('23: Other standard, please specify')

    return [
        (
            'Q11a — Which systems report immunization data to the registry?',
            _checkboxes(
                ('EMRs',                           _is_checked('19: EMRs')),
                ('Pharmacy Systems',               _is_checked('19: Pharmacy Systems ')),
                ('Hospital',                       _is_checked('19: Hospital')),
                ('Long Term Care',                 _is_checked('19: Long Term Care')),
                ('Other', bool(other_q11a), other_q11a) if other_q11a else ('Other', False),
            ),
            None,
        ),
        (
            'Q11b — By what mechanism?',
            _checkboxes(
                ('Real-time HL7',                  _is_checked('20: Real-time HL7 ')),
                ('FHIR API',                       _is_checked('20: FHIR API')),
                ('Batch upload',                   _is_checked('20: Batch upload ')),
                ('CSV/XML',                        _is_checked('20: CSV/XML')),
                ('Manual entry via portal',        _is_checked('20: Manual entry via portal')),
                ('Other', bool(other_q11b), other_q11b) if other_q11b else ('Other', False),
            ),
            None,
        ),
        (
            'Q12 — Data exchange formats / standards used',
            _checkboxes(
                ('HL7 FHIR',                       _is_checked('21: HL7 FHIR')),
                ('HL7 v2',                         _is_checked('21: HL7 v2')),
                ('XML',                            _is_checked('21: XML')),
                ('JSON',                           _is_checked('21: JSON')),
                ('Flat files / CSV',               _is_checked('21: Flat files / CSV')),
                ('N/A',                            _is_checked('21: N/A')),
                ('Other', bool(other_q12), other_q12) if other_q12 else ('Other', False),
            ),
            None,
        ),
        (
            'Q13 — Terminology and data exchange standards used',
            _checkboxes(
                ('SNOMED CT',                                         _is_checked('22: SNOMED CT')),
                ('National Vaccine Catalogue',                        _is_checked('22: National Vaccine Catalogue')),
                ('Immunization Functional Registry Standards (CIRC)', _is_checked('22: Immunization Functional Registry Standards (CIRC)')),
                ('Other', bool(other_q13), other_q13) if other_q13 else ('Other', False),
            ),
            None,
        ),
        (
            'Q14 — Immunization data sharing / transfer processes in place',
            _checkboxes(
                ('Data transfer to other PT when residents move',            _is_checked('23: Record/Data transfer to other provinces/territories when residents move')),
                ('Data intake from other PT for out-of-province vaccinations', _is_checked('23: Record/Data intake from other provinces/territories for individuals vaccinated elsewhere ')),
                ('Consent management — inter-jurisdictional sharing',   _is_checked('23: Consent management for inter- jurisdictional immunization record/data sharing ')),
                ('Consent management — within jurisdiction',            _is_checked('23: Consent management for immunization record/data sharing within the jurisdiction')),
                ('Records provided directly by individuals',                 _is_checked('23: Records provided to Public Health directly by individuals')),
                ('Other', bool(other_q14), other_q14) if other_q14 else ('Other', False),
            ),
            None,
        ),
    ]


def _section5_checkboxes(row_s):
    """
    Render Q18 and Q19 as checkbox groups matching the Section 4 pattern.
    Returns [(label, checkbox_div, None), ...]
    Q17 (free-text) and Q20/Q21 (archiving) are left to the default renderer.
    """
    def _is_checked(col):
        v = row_s.get(col)
        try:
            return pd.notna(v) and float(v) == 1.0
        except Exception:
            return False

    def _text(col):
        v = row_s.get(col)
        if pd.isna(v) or str(v).strip() in ['', 'nan', '0', '0.0']:
            return None
        return str(v).strip()

    def _checkboxes(*items):
        return html.Div(
            [_checkbox_item(*item) for item in items],
            style={'display': 'flex', 'flexDirection': 'column', 'gap': 2, 'width': '100%'}
        )

    other_q18 = _text('28: Other reconciliation processes, please specify')
    other_q19 = _text('29: Other, please specify')

    return [
        (
            'Q18 — When data quality issues are identified, how are they remediated?',
            _checkboxes(
                ('Provider corrections',
                    _is_checked('28: Provider corrections')),
                ('Manual updates made directly in the registry/repository',
                    _is_checked('28: Manual updates made directly in the registry/repository')),
                ('Automated/manual duplicate resolution',
                    _is_checked('28: Automated/manual duplicate resolution')),
                ('Other', bool(other_q18), other_q18) if other_q18 else ('Other', False),
            ),
            None,
        ),
        (
            'Q19 — When a patient identifies data quality issues, how are they remediated?',
            _checkboxes(
                ('Patient can update their immunization record',
                    _is_checked('29: Patient can update their immunization record')),
                ('Patient can request a change to their immunization record',
                    _is_checked('29: Patient can request a change to their immunization record')),
                ('Patient cannot update or request a change',
                    _is_checked('29: Patient cannot update or request a change')),
                ('Other', bool(other_q19), other_q19) if other_q19 else ('Other', False),
            ),
            None,
        ),
    ]



def _q16_checkboxes(row_s):
    """Render Q16 interoperability roadmap as checkboxes."""
    def _is_checked(col):
        v = row_s.get(col)
        try:
            return pd.notna(v) and float(v) == 1.0
        except Exception:
            return False

    def _checkboxes(*items):
        return html.Div(
            [_checkbox_item(*item) for item in items],
            style={'display': 'flex', 'flexDirection': 'column', 'gap': 2, 'width': '100%'}
        )

    return _checkboxes(
        ('Yes — PS-CA',                                   _is_checked('26: Yes: PS-CA')),
        ('Yes — Pan-Canadian Health Data Content Framework', _is_checked('26: Yes: Pan-Canadian Health Data Content Framework')),
        ('Yes — CA:FeX',                                  _is_checked('26: Yes: CA:FeX ')),
        ('No',                                                  _is_checked('26: No')),
    )


def _api_checkboxes(row_s):
    """
    Return per-question data for the API & Data Exchange section.
    Each entry is (question_label, checkbox_div, rubric_element).
    """
    def _is_checked(col):
        v = row_s.get(col)
        try:
            return pd.notna(v) and float(v) == 1.0
        except Exception:
            return False

    def _text(col):
        v = row_s.get(col)
        if pd.isna(v) or str(v).strip() in ['', 'nan', '0', '0.0']:
            return None
        return str(v).strip()

    def _checkboxes(*items):
        return html.Div(
            [_checkbox_item(*item) for item in items],
            style={'display': 'flex', 'flexDirection': 'column', 'gap': 2, 'width': '100%'}
        )

    q10_val = str(row_s.get(
        '15: 9. Does your registry/repository have externally accessible Application'
        ' Programming Interfaces (API) covering functionality needed to access and'
        ' exchange immunization data?') or '').strip()

    other_protocol = _text('16: Other, please specify')
    other_auth     = _text('17: Other, please specify')
    yes_desc       = _text('18: Yes')

    # ── Compute sub-scores ───────────────────────────────────────────
    s10a = score_api_protocol(
        row_s.get('16: REST'), row_s.get('16: SOAP'),
        row_s.get('16: AMQP'), row_s.get('16: Other, please specify')
    )
    s10b = score_auth(
        row_s.get('17: SAML'), row_s.get('17: OAuth'),
        row_s.get('17: Other, please specify')
    )
    s10c = score_10c(
        row_s.get('18: No '), row_s.get('18: No sure'), row_s.get('18: Yes')
    )

    if q10_val == 'No':
        q10_final = -2
    elif q10_val == 'Yes':
        q10_final = min(s10a, s10b, s10c)
    else:
        q10_final = 0

    # DCC and OC are the same for Q10
    final_dcc = q10_final
    final_oc  = q10_final

    return [
        (
            'Q10 — API exists?',
            _checkboxes(('Yes', q10_val == 'Yes'), ('No', q10_val == 'No')),
            _rubric_block(
                [('Yes → min(10a, 10b, 10c)', None, None), ('No', -2, -2), ('Blank', 0, 0)],
            ),
        ),
        (
            'Q10a — API protocol(s) used',
            _checkboxes(
                ('REST', _is_checked('16: REST')),
                ('SOAP', _is_checked('16: SOAP')),
                ('AMQP', _is_checked('16: AMQP')),
                ('Other', bool(other_protocol), other_protocol) if other_protocol
                    else ('Other', False),
            ),
            _rubric_block(
                [('REST', 2, 2), ('SOAP', 2, 2), ('AMQP', 2, 2), ('Other / None', -2, -2)],
                final_dcc=s10a if q10_val == 'Yes' else None,
                final_oc=s10a if q10_val == 'Yes' else None,
                score_label='Sub-score',
            ),
        ),
        (
            'Q10b — API authentication method(s)',
            _checkboxes(
                ('SAML',  _is_checked('17: SAML')),
                ('OAuth', _is_checked('17: OAuth')),
                ('Other', bool(other_auth), other_auth) if other_auth
                    else ('Other', False),
            ),
            _rubric_block(
                [('SAML', 2, 2), ('OAuth', 2, 2), ('Other w/ SAML/OIDC', 2, 2), ('Custom / Blank', -2, -2)],
                final_dcc=s10b if q10_val == 'Yes' else None,
                final_oc=s10b if q10_val == 'Yes' else None,
                score_label='Sub-score',
            ),
        ),
        (
            'Q10c — If no APIs, other data exchange interfaces/protocols supported?',
            _checkboxes(
                ('Yes',      bool(yes_desc), yes_desc) if yes_desc else ('Yes', False),
                ('No',       _is_checked('18: No ')),
                ('Not sure', _is_checked('18: No sure')),
            ),
            _rubric_block(
                [('Yes', 2, 2), ('No', -2, -2), ('Not sure', -2, -2)],
                final_dcc=s10c if q10_val == 'Yes' else None,
                final_oc=s10c if q10_val == 'Yes' else None,
                score_label='Sub-score',
                section_final={
                    'formula': 'min(%s, %s, %s)' % (s10a, s10b, s10c) if q10_val == 'Yes' else 'N/A',
                    'if_yes': min(s10a, s10b, s10c) if q10_val == 'Yes' else None,
                    'if_no': -2,
                    'actual_dcc': final_dcc,
                    'actual_oc':  final_oc,
                    'active': q10_val,  # 'Yes', 'No', or ''
                },
            ),
        ),
    ]


# ─────────────────────────── RUBRIC DEFINITIONS ──────────────────────
def _build_rubric(prefix, row_s, breakdowns):
    """
    Return a _rubric_block() element for the given column prefix and row,
    or None if that column has no rubric.
    breakdowns: list of score_row_breakdown dicts (one per respondent).
    """
    bd = breakdowns[0]  # use first respondent for score display

    def _dcc(key): return bd.get(key, (0, 0, 'neutral'))[0]
    def _oc(key):  return bd.get(key, (0, 0, 'neutral'))[1]

    # ── Q2: Registry existence ──────────────────────────────────────
    if prefix == '4':
        v = _dcc('q2')
        return _rubric_block(
            [('Yes', 2, 2), ('No', -2, -2)],
            final_dcc=v, final_oc=_oc('q2'),
        )

    # ── Q3: Panorama ───────────────────────────────────────────────
    if prefix == '5':
        v = _dcc('q3')
        return _rubric_block(
            [('Yes', 2, 2), ('No', -2, -2), ('Blank', 0, 0)],
            final_dcc=v, final_oc=_oc('q3'),
        )

    # ── Q5: Hosting ────────────────────────────────────────────────
    if prefix == '9':
        v = _dcc('q5')
        return _rubric_block(
            [('Cloud', 2, 2), ('On-premise / Hybrid', -2, -2), ('Blank', 0, 0)],
            final_dcc=v, final_oc=_oc('q5'),
        )

    # ── Q6a: Audit logins (OC only, scored independently) ─────────
    if prefix == '10':
        oc_v = _oc('q6a')
        return _rubric_block(
            [('Yes', 0, 2), ('No', 0, -2)],
            final_dcc=0, final_oc=oc_v,
        )

    # ── Q6b: Activity logging (OC only, scored independently) ──────
    if prefix == '11':
        oc_v = _oc('q6b')
        return _rubric_block(
            [('Yes', 0, 2), ('No', 0, -2)],
            final_dcc=0, final_oc=oc_v,
        )

    # ── Q7: Disaster recovery (OC only) ───────────────────────────
    if prefix == '12':
        oc_v = _oc('q7')
        return _rubric_block(
            [('Yes', 0, 2), ('No', 0, -2)],
            final_dcc=0, final_oc=oc_v,
        )

    # ── Q14: Active upgrades ───────────────────────────────────────
    if prefix == '24':
        v = _dcc('q14')
        return _rubric_block(
            [('Yes', 2, 2), ('No', 0, 0)],
            final_dcc=v, final_oc=_oc('q14'),
        )

    # ── Q14a: Upgrade plans ────────────────────────────────────────
    if prefix == '25':
        v = _dcc('q14a')
        return _rubric_block(
            [('Yes', 2, 2), ('No / Blank', 0, 0)],
            final_dcc=v, final_oc=_oc('q14a'),
        )

    # ── Q16: Interop roadmap (PS-CA / Pan-Canadian HDCF / CA:FeX) ─
    if prefix == '26':
        v = _dcc('q16')
        return _rubric_block(
            [('Any Yes (PS-CA / HDCF / CA:FeX)', 2, 2), ('None', 0, 0)],
            final_dcc=v, final_oc=_oc('q16'),
        )

    return None


# ─────────────────────────── VIEWER ─────────────────────────────────
def _field_row(label, val_cells, is_diff, rows_list, badge=None, rubric=None):
    """
    label    : question label shown on the left
    val_cells: list of response cells (one per respondent)
    badge    : optional score badge appended to the label
    rubric   : optional string shown in a right-hand rubric column
    """
    label_content = [
        html.Span(label, style={'fontSize': 12, 'color': '#2E75B6', 'fontWeight': '600'}),
    ]
    if badge is not None:
        label_content.append(badge)

    label_el = html.Div(label_content, style={
        'flex': '0 0 28%', 'wordBreak': 'break-word', 'paddingTop': 2,
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

    children = [label_el, val_el]

    if rubric is not None:
        # rubric can be a plain string or a pre-built html element
        rubric_content = rubric if not isinstance(rubric, str) else html.Span(
            rubric, style={'fontSize': 11, 'color': '#5A3E00', 'lineHeight': '1.45'}
        )
        rubric_el = html.Div(rubric_content, style={
            'flex': '0 0 22%', 'backgroundColor': '#FFFCEF',
            'border': '1px solid #E8D070', 'borderRadius': 4,
            'padding': '5px 8px', 'wordBreak': 'break-word',
        })
        children.append(rubric_el)

    return html.Div(children, style={
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

    # Enforce rubric section order; append any unknown sections at the end
    known_order = SECTION_ORDER
    sections_order = (
        [s for s in known_order if s in sections_map] +
        [s for s in sections_order if s not in known_order]
    )
    if selected_sections:
        sections_order = [s for s in sections_order if s in selected_sections]

    # Track which score keys have already had a badge shown (per-section render pass)
    # so we don't show the badge on every sub-column of the same scored question.
    # We reset this per section card.

    cards = []
    _part_emitted = {'p1': False, 'p2': False}

    def _part_header(label, color):
        return html.Div(label, style={
            'fontSize': 13, 'fontWeight': '700', 'color': '#FFFFFF',
            'backgroundColor': color,
            'padding': '8px 14px', 'borderRadius': 6,
            'marginBottom': 6, 'marginTop': 10,
            'letterSpacing': '0.03em',
        })

    for sec in sections_order:
        cols = sections_map.get(sec, [])
        row_els = []
        rendered_bin_groups = set()
        imm_capture_rendered = False
        shown_score_keys = set()   # reset per section card

        # ── Section 3: Citizen Access & APIs — render Q8/Q9 + Q10 ─────
        _API_PREFIXES = {'15', '16', '17', '18'}
        _CITIZEN_PREFIXES = {'13', '14'}
        if sec == 'Section 3 — Citizen Access & APIs' and any(
            col.split(':')[0].strip() in (_API_PREFIXES | _CITIZEN_PREFIXES) for col in cols
        ):
            # ── Q8 / Q9 citizen access checkboxes ───────────────────
            if any(col.split(':')[0].strip() in _CITIZEN_PREFIXES for col in cols):
                per_citizen = [_citizen_access_checkboxes(row_s) for row_s, _, _ in rows_list]
                for qi in range(len(per_citizen[0])):
                    q_label   = per_citizen[0][qi][0]
                    val_cells = [per_citizen[ri][qi][1] for ri in range(len(rows_list))]
                    rubric    = per_citizen[0][qi][2]
                    row_els.append(_field_row(q_label, val_cells, is_diff, rows_list,
                                              badge=None, rubric=rubric))

            # ── Q10 API checkboxes ───────────────────────────────────
            if any(col.split(':')[0].strip() in _API_PREFIXES for col in cols):
                per_respondent = [_api_checkboxes(row_s) for row_s, _, _ in rows_list]
                num_questions = len(per_respondent[0])
                for qi in range(num_questions):
                    q_label   = per_respondent[0][qi][0]
                    val_cells = [per_respondent[ri][qi][1] for ri in range(len(rows_list))]
                    rubric    = per_respondent[0][qi][2]
                    row_els.append(_field_row(q_label, val_cells, is_diff, rows_list,
                                              badge=None, rubric=rubric))

            if row_els:
                _SECTION_BADGE_KEYS = {
                    'Section 2 — Hosting, Security & DR': 'q6',
                    'Section 3 — Citizen Access & APIs': 'q10',
                }
                def _sig_from(v): return 'positive' if v > 0 else ('negative' if v < 0 else 'neutral')
                sec_badge = None
                sec_score_key = _SECTION_BADGE_KEYS.get(sec)
                if sec_score_key:
                    tup = breakdowns[0].get(sec_score_key, (0, 0, 'neutral'))
                    sec_badge = score_badges(_sig_from(tup[0]), _sig_from(tup[1]))
                header_children = [
                    html.Span(sec.replace('Part 2 — ', ''), style={'textTransform': 'uppercase', 'letterSpacing': '0.04em'}),
                ]
                if sec_badge:
                    header_children.append(sec_badge)
                # Emit Part 1 header if not yet done
                if sec in PART_1_SECTIONS and not _part_emitted['p1']:
                    _part_emitted['p1'] = True
                    cards.append(_part_header('Part 1 — Registry Assessment', BLUE))
                elif sec in PART_2_SECTIONS and not _part_emitted['p2']:
                    _part_emitted['p2'] = True
                    cards.append(_part_header('Part 2 — Governance & Context', '#5C4A1E'))

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
                    'marginLeft': 12,
                }))
            continue  # skip to next section

        # ── Section 4: System Integration Q11–Q14 checkbox intercept ────
        _S4_PREFIXES = {'19', '20', '21', '22', '23'}
        if sec == 'Section 4 — System Integration' and any(
            col.split(':')[0].strip() in _S4_PREFIXES for col in cols
        ):
            per_s4 = [_section4_checkboxes(row_s) for row_s, _, _ in rows_list]
            for qi in range(len(per_s4[0])):
                q_label   = per_s4[0][qi][0]
                val_cells = [per_s4[ri][qi][1] for ri in range(len(rows_list))]
                row_els.append(_field_row(q_label, val_cells, is_diff, rows_list,
                                          badge=None, rubric=None))
            # fall through — let remaining cols (Q15, Q15a, Q16) render normally below

        # ── Section 5: Data Quality — Q18/Q19 checkbox intercept ────────
        _S5_CB_PREFIXES = {'28', '29'}
        if sec == 'Section 5 — Data Quality' and any(
            col.split(':')[0].strip() in _S5_CB_PREFIXES for col in cols
        ):
            per_s5 = [_section5_checkboxes(row_s) for row_s, _, _ in rows_list]
            for qi in range(len(per_s5[0])):
                q_label   = per_s5[0][qi][0]
                val_cells = [per_s5[ri][qi][1] for ri in range(len(rows_list))]
                row_els.append(_field_row(q_label, val_cells, is_diff, rows_list,
                                          badge=None, rubric=None))
            # fall through — let Q17 (prefix 27) render as free-text below

        for col in cols:
            prefix = col.split(':')[0].strip()

            # skip prefixes already rendered as checkboxes in the S5 block
            if sec == 'Section 5 — Data Quality' and prefix in _S5_CB_PREFIXES:
                continue

            # skip prefixes already rendered as checkboxes in the S4 block
            if sec == 'Section 4 — System Integration' and prefix in _S4_PREFIXES:
                continue

            # ── Q16: interoperability roadmap checkboxes (rubric card kept) ────
            if prefix == '26':
                if '26' not in rendered_bin_groups:
                    rendered_bin_groups.add('26')
                    val_cells = [_q16_checkboxes(row_s) for row_s, _, _ in rows_list]
                    rubric_el = _build_rubric('26', rows_list[0][0], breakdowns)
                    row_els.append(_field_row(
                        'Q16 — Participating in Interoperability Roadmap (PS-CA / Pan-Canadian HDCF / CA:FeX)?',
                        val_cells, is_diff, rows_list, badge=None, rubric=rubric_el,
                    ))
                continue

            # ── Q22 / Q27 / Q28: Part 2 checkbox groups ──────────────
            _P2_CB_META = {
                '32': ('Q22 — Who is the custodian/business owner of immunization data?',
                       [('Ministry of Health',                                '32: Ministry of Health'),
                        ('Public Health / Office of the Medical Health Officer', '32: Public Health/Office of the Medical Health Officer'),
                        ('Central Health Authorities',                        '32: Central Health Authorities'),
                        ('Other',                                             '32: Other, please specify')]),
                '37': ('Q27 — Policies, procedures or agreements guiding data sharing',
                       [('Provincial Immunization Manual',   '37: Provincial Immunization Manual'),
                        ('Data Sharing Agreements',          '37: Data Sharing Agreements'),
                        ('Immunization Data Policies',       '37: Immunization Data Policies'),
                        ('Immunization Data Procedures',     '37: Immunization Data Procedures'),
                        ('Other',                            '37: Other, please specify')]),
                '38': ('Q28 — Clinical / business / technical challenges in sharing immunization data',
                       [('Data completeness',                                   '38: Data completeness'),
                        ('Siloed / disconnected approaches to data stewardship','38: Siloed/disconnected approaches to data stewardship'),
                        ('Legislative limitations',                             '38: Legislative limitations'),
                        ('Lack of system integration',                          '38: Lack of system integration'),
                        ('Other',                                               '38: Other, please specify')]),
            }
            if prefix in _P2_CB_META and prefix not in rendered_bin_groups:
                rendered_bin_groups.add(prefix)
                q_label, option_cols = _P2_CB_META[prefix]

                def _make_p2_cb(row_s, opts=option_cols):
                    def _is_checked(c):
                        v = row_s.get(c)
                        try:    return pd.notna(v) and float(v) == 1.0
                        except: return False
                    def _text(c):
                        v = row_s.get(c)
                        if pd.isna(v) or str(v).strip() in ['', 'nan', '0', '0.0']:
                            return None
                        return str(v).strip()
                    items = []
                    for lbl, c in opts:
                        raw_val = row_s.get(c)
                        try:
                            is_binary = pd.notna(raw_val) and float(raw_val) in (0.0, 1.0)
                        except:
                            is_binary = False
                        if is_binary:
                            items.append(_checkbox_item(lbl, _is_checked(c)))
                        else:
                            freetext = _text(c)
                            items.append(_checkbox_item(lbl, bool(freetext), freetext))
                    return html.Div(items,
                                    style={'display': 'flex', 'flexDirection': 'column',
                                           'gap': 2, 'width': '100%'})

                val_cells = [_make_p2_cb(row_s) for row_s, _, _ in rows_list]
                row_els.append(_field_row(q_label, val_cells, is_diff, rows_list,
                                          badge=None, rubric=None))
                continue

            if prefix in _P2_CB_META:   # sibling columns of an already-rendered group
                continue


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

                rubric_el = _build_rubric(prefix, rows_list[0][0], breakdowns)
                row_els.append(_field_row(label, val_cells, is_diff, rows_list,
                                          badge=badge, rubric=rubric_el))

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

                rubric_el = _build_rubric(prefix, rows_list[0][0], breakdowns)
                row_els.append(_field_row(label, val_cells, is_diff, rows_list,
                                          badge=badge, rubric=rubric_el))

        if row_els:
            # For sections whose score combines multiple columns (q6, q10),
            # show the DCC/OC badge in the section header instead of a field row.
            _SECTION_BADGE_KEYS = {
                'Section 2 — Hosting, Security & DR': 'q6',
                'Section 3 — Citizen Access & APIs': 'q10',
            }
            def _sig_from(v): return 'positive' if v > 0 else ('negative' if v < 0 else 'neutral')
            sec_badge = None
            sec_score_key = _SECTION_BADGE_KEYS.get(sec)
            if sec_score_key:
                tup = breakdowns[0].get(sec_score_key, (0, 0, 'neutral'))
                sec_badge = score_badges(_sig_from(tup[0]), _sig_from(tup[1]))

            header_children = [
                html.Span(sec.replace('Part 2 — ', ''), style={'textTransform': 'uppercase', 'letterSpacing': '0.04em'}),
            ]
            if sec_badge:
                header_children.append(sec_badge)

            # ── Emit Part header if needed ───────────────────────
            if sec in PART_1_SECTIONS and not _part_emitted['p1']:
                _part_emitted['p1'] = True
                cards.append(_part_header('Part 1 — Registry Assessment', BLUE))
            elif sec in PART_2_SECTIONS and not _part_emitted['p2']:
                _part_emitted['p2'] = True
                cards.append(_part_header('Part 2 — Governance & Context', '#5C4A1E'))

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
                'marginLeft': 12,
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