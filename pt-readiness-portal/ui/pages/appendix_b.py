"""
appendix_b.py
─────────────
Appendix B — Scoring Methodology & Rubric
Renders the scoring methodology as a styled Dash component,
matching the notebook Cell 0 HTML design exactly.

Usage in app.py:
    from ui.pages.appendix_b import build_appendix_b
    # place build_appendix_b() in layout
"""

from dash import html

# ─────────────────────────── STYLE TOKENS ────────────────────────────
DARK   = '#1F4E79'
BLUE   = '#2E75B6'
GREEN  = '#375623'
ORANGE = '#C55A11'
LGREY  = '#F2F7FB'
BORDER = '#D6E4F0'

def _css(d):
    return d

# ─────────────────────────── PRIMITIVES ──────────────────────────────

def _section_header(num, title):
    return html.Div([
        html.Span(f'{num}\u00a0\u00a0', style={'opacity': '0.85'}),
        title,
    ], style={
        'background': DARK, 'color': '#fff',
        'padding': '12px 24px', 'borderRadius': 6,
        'fontSize': 18, 'fontWeight': 'bold',
        'margin': '36px 0 16px 0',
    })


def _subsection(title):
    return html.Div(title, style={
        'color': DARK, 'fontSize': 16, 'fontWeight': 'bold',
        'margin': '24px 0 10px 0',
        'borderLeft': f'4px solid {BLUE}', 'paddingLeft': 12,
    })


def _subsubsection(title):
    return html.Div(title, style={
        'color': GREEN, 'fontSize': 14, 'fontWeight': 'bold',
        'margin': '18px 0 8px 0',
    })


def _p(text):
    return html.P(text, style={'fontSize': 13, 'lineHeight': '1.7', 'margin': '8px 0'})


def _callout(text, variant='blue'):
    colors = {
        'blue':   ('#EBF3FB', BLUE,   DARK),
        'green':  ('#EBF7EE', GREEN,  GREEN),
        'orange': ('#FEF3EB', ORANGE, '#7F3A00'),
    }
    bg, border, fg = colors.get(variant, colors['blue'])
    # text can be a list [strong_part, rest_part] or a plain string
    if isinstance(text, list):
        children = text
    else:
        children = [text]
    return html.Div(children, style={
        'padding': '14px 20px',
        'borderRadius': '0 6px 6px 0',
        'margin': '14px 0',
        'fontSize': 13, 'lineHeight': '1.7',
        'background': bg,
        'borderLeft': f'5px solid {border}',
        'color': fg,
    })


def _code(text):
    return html.Code(text, style={
        'background': '#EBF3FB', 'color': ORANGE,
        'padding': '2px 6px', 'borderRadius': 3, 'fontSize': 12,
    })


def _score_pill(val, label=None):
    """Coloured score cell for tables."""
    if val is None:
        txt = label or '—'
        fg, bg = '#595959', 'transparent'
    elif isinstance(val, str) and val.startswith('min'):
        txt = val
        fg, bg = '#595959', 'transparent'
    elif val > 0:
        txt = f'+{val}' if label is None else label
        fg, bg = GREEN, 'transparent'
    elif val < 0:
        txt = str(val) if label is None else label
        fg, bg = '#C00000', 'transparent'
    else:
        txt = '0' if label is None else label
        fg, bg = '#595959', 'transparent'
    return html.Td(txt, style={
        'color': fg, 'fontWeight': 'bold',
        'textAlign': 'center', 'fontSize': 13,
        'padding': '9px 14px',
        'borderBottom': f'1px solid {BORDER}',
    })


def _td(text, alt=False):
    return html.Td(str(text), style={
        'padding': '9px 14px',
        'borderBottom': f'1px solid {BORDER}',
        'fontSize': 13,
        'backgroundColor': LGREY if alt else '#fff',
    })


def _th(text):
    return html.Th(text, style={
        'padding': '10px 14px', 'textAlign': 'left',
        'fontWeight': 600, 'fontSize': 13,
        'backgroundColor': DARK, 'color': '#fff',
    })


def _scoring_table(rows):
    """Table with Response | DCC | OC | Rationale columns."""
    head = html.Thead(html.Tr([
        _th('Response'), _th('DCC'), _th('OC'), _th('Rationale')
    ]))
    body_rows = []
    for i, (resp, dcc, oc, rationale) in enumerate(rows):
        body_rows.append(html.Tr([
            _td(resp, alt=i % 2 == 1),
            _score_pill(dcc),
            _score_pill(oc),
            html.Td(rationale, style={
                'color': '#555', 'fontSize': 12,
                'padding': '9px 14px',
                'borderBottom': f'1px solid {BORDER}',
                'backgroundColor': LGREY if i % 2 == 1 else '#fff',
            }),
        ]))
    return html.Table([head, html.Tbody(body_rows)], style={
        'borderCollapse': 'collapse', 'width': '100%',
        'margin': '12px 0 20px 0', 'fontSize': 13,
    })


def _subscore_table(rows):
    """Sub-component table: Sub-question | Criteria | Score | Rationale."""
    head = html.Thead(html.Tr([
        _th('Sub-question'), _th('Criteria'), _th('Score'), _th('Rationale')
    ]), style={'background': BLUE})
    body_rows = []
    for i, (subq, criteria, score, rationale) in enumerate(rows):
        body_rows.append(html.Tr([
            html.Td(subq, style={
                'padding': '9px 14px', 'fontSize': 13,
                'borderBottom': f'1px solid {BORDER}',
                'fontWeight': '600' if subq else 'normal',
            }),
            _td(criteria, alt=i % 2 == 1),
            _score_pill(score),
            html.Td(rationale, style={
                'color': '#555', 'fontSize': 12,
                'padding': '9px 14px',
                'borderBottom': f'1px solid {BORDER}',
            }),
        ]))
    return html.Table([head, html.Tbody(body_rows)], style={
        'borderCollapse': 'collapse', 'width': '100%',
        'margin': '12px 0 20px 0',
    })


def _hr():
    return html.Hr(style={
        'border': 'none', 'borderTop': f'2px solid {BORDER}',
        'margin': '32px 0',
    })


def _badge(text, variant='moderate'):
    styles = {
        'high':     ('#D5E8D4', GREEN),
        'moderate': ('#FFF2CC', '#7F6000'),
        'low':      ('#FCE4D6', ORANGE),
        'vlow':     ('#F4CCCC', '#C00000'),
    }
    bg, fg = styles.get(variant, styles['moderate'])
    return html.Span(text, style={
        'padding': '4px 12px', 'borderRadius': 12,
        'fontSize': 12, 'fontWeight': 'bold',
        'display': 'inline-block',
        'background': bg, 'color': fg,
    })


# ─────────────────────────── MAIN BUILDER ────────────────────────────

def build_appendix_b():
    """Return the full Appendix B rubric as a Dash html.Div."""

    # ── Title block ──────────────────────────────────────────────────
    title_block = html.Div([
        html.H1('Provincial/Territorial Immunization Readiness Assessment',
                style={'margin': '0 0 8px 0', 'fontSize': 26,
                       'fontWeight': 'bold', 'letterSpacing': 0.5}),
        html.Div('Scoring Methodology & Rubric',
                 style={'fontSize': 14, 'opacity': 0.85, 'margin': '4px 0'}),
        html.Div('Appendix B — Technical Reference',
                 style={'fontSize': 12, 'opacity': 0.65, 'marginTop': 14,
                        'borderTop': '1px solid rgba(255,255,255,0.3)',
                        'paddingTop': 10}),
    ], style={
        'background': f'linear-gradient(135deg, {DARK} 0%, {BLUE} 100%)',
        'color': '#fff', 'padding': '36px 40px',
        'borderRadius': 10, 'marginBottom': 32,
    })

    # ── Section 1: Overview ──────────────────────────────────────────
    overview_cards = html.Div([
        html.Div([
            html.Div('\U0001f4e1\u00a0\u00a0Data Connection Complexity (DCC)',
                     style={'fontWeight': 'bold', 'fontSize': 14,
                            'marginBottom': 6, 'color': DARK}),
            _p('Technical effort required to establish and maintain data connections '
               'between the provincial/territorial immunization registry and the platform. '
               'Higher scores indicate simpler, lower-effort connections.'),
        ], style={
            'flex': 1, 'borderRadius': 8, 'padding': '20px 22px',
            'background': '#EBF3FB', 'borderTop': f'5px solid {BLUE}',
        }),
        html.Div([
            html.Div('\u2699\ufe0f\u00a0\u00a0Operational Complexity (OC)',
                     style={'fontWeight': 'bold', 'fontSize': 14,
                            'marginBottom': 6, 'color': GREEN}),
            _p('Ongoing operational effort required to support data exchange, '
               'incident management, and system maintenance post-integration. '
               'Higher scores indicate lower ongoing operational overhead.'),
        ], style={
            'flex': 1, 'borderRadius': 8, 'padding': '20px 22px',
            'background': '#EBF7EE', 'borderTop': f'5px solid {GREEN}',
        }),
    ], style={'display': 'flex', 'gap': 18, 'margin': '18px 0 24px 0'})

    # ── Section 2: Scoring structure table ──────────────────────────
    struct_head = html.Thead(html.Tr([_th('Section'), _th('Content'), _th('Scoring Impact')]))
    struct_rows = [
        ('Section 1 \u2014 Registry Architecture',   'Questions 2, 3',    'DCC + OC'),
        ('Section 2 \u2014 Technical Infrastructure','Questions 5, 6, 7', 'DCC + OC'),
        ('Section 3 \u2014 External Access & APIs',  'Question 10',       'DCC + OC'),
        ('Section 4 \u2014 Internal Data Flows',     'Informational',     'Score\u00a0=\u00a00'),
        ('Section 5 \u2014 Data Quality Processes',  'Informational',     'Score\u00a0=\u00a00'),
        ('Section 6 \u2014 Archiving & Governance',  'Informational',     'Score\u00a0=\u00a00'),
        ('Part 2 \u2014 Operational Context',        'Informational',     'Score\u00a0=\u00a00'),
    ]
    struct_body = html.Tbody([
        html.Tr([_td(s, alt=i%2==1), _td(c, alt=i%2==1), _td(sc, alt=i%2==1)])
        for i, (s, c, sc) in enumerate(struct_rows)
    ])
    struct_table = html.Table([struct_head, struct_body], style={
        'borderCollapse': 'collapse', 'width': '100%',
        'margin': '12px 0 20px 0', 'fontSize': 13,
    })

    # ── Section 3: Question-by-question rules ────────────────────────

    # Score range callout
    range_table_head = html.Thead(html.Tr([
        _th('Dimension'), _th('Min'), _th('Max'), _th('Note')
    ]))
    range_table_body = html.Tbody([
        html.Tr([_td('DCC'), _score_pill(-8), _score_pill(14), _td('Q6, Q7 do not contribute to DCC')]),
        html.Tr([_td('OC', alt=True),  _score_pill(-14), _score_pill(20), _td('Q6a and Q6b scored independently', alt=True)]),
    ])
    range_table = html.Table([range_table_head, range_table_body], style={
        'borderCollapse': 'collapse', 'width': '100%',
        'margin': '12px 0 20px 0', 'fontSize': 13,
    })

    q2 = _scoring_table([
        ('Yes', 2,  2,  'Single connection point; no data resolution processes required.'),
        ('No',  -2, -2, 'Possible need for multiple connections; data resolution processes likely required.'),
    ])

    q3 = _scoring_table([
        ('Yes',   2,  2,  'Suite of pre-built connectors available; connector maintained by the platform.'),
        ('No',    -2, -2, 'Custom connector likely required; connector maintained by the PT.'),
        ('Blank', 0,  0,  'No registry present; not applicable.'),
    ])

    q5 = _scoring_table([
        ('Cloud',      2,  2,  'Fewer networking issues; network operations largely outsourced.'),
        ('On-premise', -2, -2, 'Potential network complexity; potential network operations complexity.'),
        ('Hybrid',     -2, -2, 'Potential network complexity; potential network operations complexity.'),
        ('Blank',      0,  0,  'No response; not scored.'),
    ])

    q6 = _scoring_table([
        ('Q6a = Yes',  0, 2,  'No impact on connection; facilitates incident management.'),
        ('Q6a = No',   0, -2, 'No impact on connection; complicates incident management.'),
        ('Q6b = Yes',  0, 2,  'No impact on connection; facilitates incident management.'),
        ('Q6b = No',   0, -2, 'No impact on connection; complicates incident management.'),
    ])

    q7 = _scoring_table([
        ('Yes', 0, 2,  'No impact on connection; facilitates incident management.'),
        ('No',  0, -2, 'No impact on connection; complicates incident management.'),
    ])

    q10_top = _scoring_table([
        ('Yes', None, None, 'Score = min(10a, 10b) — minimum of protocol and authentication sub-scores.'),
        ('No',  None, None, 'Score = max(\u22122, 10c) — lifted to 0 if alternate exchange exists, otherwise \u22122.'),
    ])

    q10_sub = _subscore_table([
        ('Q10a \u2014 API Protocol', 'REST, SOAP, or AMQP (one or more)', 2,
         'Platform supports all standard API protocols.'),
        ('', 'Custom / Other protocol', -2,
         'Custom connectors will be required.'),
        ('Q10b \u2014 Authentication', 'SAML or OAuth (one or both)', 2,
         'Platform supports SAML and OAuth.'),
        ('', 'Free-text containing SAML/OIDC/OAuth', 2,
         'App extension: recognised as standard auth.'),
        ('', 'Custom / Other or blank', -2,
         'Custom connectors will be required.'),
        ('Q10c \u2014 Alternative Exchange\n(Q10 = No only)', 'Yes — alternate interface described', 0,
         'Alternate mechanism exists; penalty lifted.'),
        ('', 'No / Not sure', -2,
         'No confirmed alternate data exchange mechanism.'),
    ])

    q14 = html.Table([
        html.Thead(html.Tr([_th('Scenario'), _th('DCC'), _th('OC'), _th('Rationale')])),
        html.Tbody([
            html.Tr([
                _td('Currently upgrading (Q15 = Yes)'),
                _score_pill(2), _score_pill(2),
                _td('Introduces possibility to add APIs; potential to align with platform.'),
            ]),
            html.Tr([
                _td('Not upgrading, but future plans exist (Q15a = Yes)', alt=True),
                _score_pill(2), _score_pill(2),
                _td('Introduces possibility to add APIs; potential to align with platform.', alt=True),
            ]),
            html.Tr([
                _td('No current or planned upgrades'),
                _score_pill(0), _score_pill(0),
                _td('Status quo maintained.'),
            ]),
        ]),
    ], style={'borderCollapse': 'collapse', 'width': '100%',
              'margin': '12px 0 20px 0', 'fontSize': 13})

    q16 = _scoring_table([
        ('Participating in PS-CA, Pan-Canadian HDCF, or CA:FeX', 2, 2,
         'Plans align with national interoperability direction.'),
        ('No participation in any initiative', 0, 0,
         'Status quo maintained.'),
    ])

    # ── Section 4: Interpretation guide ─────────────────────────────
    interp_cards = html.Div([
        html.Div([
            html.Div('\u2265\u00a06', style={'fontSize': 18, 'fontWeight': 'bold', 'marginBottom': 4}),
            html.Div('High Readiness',   style={'fontSize': 13, 'fontWeight': 'bold', 'marginBottom': 4}),
            html.Div('Favourable conditions. Lower anticipated integration effort.',
                     style={'fontSize': 12, 'opacity': 0.85}),
        ], style={'flex': 1, 'minWidth': 160, 'borderRadius': 6,
                  'padding': '14px 18px', 'background': '#D5E8D4', 'color': GREEN,
                  'textAlign': 'center'}),
        html.Div([
            html.Div('0 \u2013 5', style={'fontSize': 18, 'fontWeight': 'bold', 'marginBottom': 4}),
            html.Div('Moderate Readiness', style={'fontSize': 13, 'fontWeight': 'bold', 'marginBottom': 4}),
            html.Div('Average conditions. Some customization or coordination required.',
                     style={'fontSize': 12, 'opacity': 0.85}),
        ], style={'flex': 1, 'minWidth': 160, 'borderRadius': 6,
                  'padding': '14px 18px', 'background': '#FFF2CC', 'color': '#7F6000',
                  'textAlign': 'center'}),
        html.Div([
            html.Div('\u22125 \u2013 \u22121', style={'fontSize': 18, 'fontWeight': 'bold', 'marginBottom': 4}),
            html.Div('Low Readiness', style={'fontSize': 13, 'fontWeight': 'bold', 'marginBottom': 4}),
            html.Div('Below average. Notable effort required for integration.',
                     style={'fontSize': 12, 'opacity': 0.85}),
        ], style={'flex': 1, 'minWidth': 160, 'borderRadius': 6,
                  'padding': '14px 18px', 'background': '#FCE4D6', 'color': ORANGE,
                  'textAlign': 'center'}),
        html.Div([
            html.Div('< \u22125', style={'fontSize': 18, 'fontWeight': 'bold', 'marginBottom': 4}),
            html.Div('Very Low Readiness', style={'fontSize': 13, 'fontWeight': 'bold', 'marginBottom': 4}),
            html.Div('Challenging conditions. Significant additional effort likely needed.',
                     style={'fontSize': 12, 'opacity': 0.85}),
        ], style={'flex': 1, 'minWidth': 160, 'borderRadius': 6,
                  'padding': '14px 18px', 'background': '#F4CCCC', 'color': '#C00000',
                  'textAlign': 'center'}),
    ], style={'display': 'flex', 'gap': 12, 'margin': '14px 0', 'flexWrap': 'wrap'})

    # ── Assemble ─────────────────────────────────────────────────────
    return html.Div([
        title_block,

        # 1 Overview
        _section_header(1, 'Overview'),
        _p('This report presents the results of the PT Technical Readiness Assessment, conducted to '
           'evaluate the readiness of Canadian provinces and territories to connect with the platform. '
           'Readiness is evaluated across two independent dimensions:'),
        overview_cards,
        _callout([
            html.Strong('Scoring Direction: '),
            'Higher positive scores indicate greater readiness \u2014 simpler connection requirements '
            'and lower operational overhead. Negative scores indicate conditions that will require '
            'additional effort to resolve prior to or during integration.',
        ], 'blue'),
        _hr(),

        # 2 Scoring structure
        _section_header(2, 'Scoring Structure'),
        _p('Questions are organized into six sections. Only a subset contribute directly to the '
           'scoring model. The remainder capture contextual information for product requirements analysis.'),
        struct_table,
        _subsection('Score Ranges'),
        range_table,
        _hr(),

        # 3 Scoring rules
        _section_header(3, 'Question-by-Question Scoring Rules'),

        _subsection('Q2 \u2014 Official Provincial/Territorial Immunization Registry'),
        q2,

        _subsection('Q3 \u2014 Panorama Implementation'),
        q3,

        _subsection('Q5 \u2014 Hosting Environment'),
        q5,

        _subsection('Q6 \u2014 Audit & Logging Mechanisms'),
        _callout([
            html.Strong('Scoring change: '),
            'Q6a (audit of logins) and Q6b (logging of user activities) are scored independently. '
            'Each contributes \u00b12 to OC separately, giving a combined Q6 range of \u22124 to +4.',
        ], 'orange'),
        q6,

        _subsection('Q7 \u2014 Backups & Disaster Recovery'),
        q7,

        _subsection('Q10 \u2014 Externally Accessible APIs'),
        q10_top,
        _subsubsection('Q10 Sub-component Scores'),
        q10_sub,
        _callout([
            html.Strong('Calculation logic: '),
            'When Q10 = Yes, the final score is the ',
            html.Strong('minimum'),
            ' of sub-components 10a and 10b — a single weak component (e.g., custom authentication) '
            'appropriately constrains the overall score. '
            'When Q10 = No, sub-component 10c is evaluated: if an alternate exchange interface is '
            'confirmed the score is ',
            _code('max(\u22122, 0) = 0'),
            '; otherwise it remains ',
            _code('\u22122'),
            '.',
        ], 'blue'),

        _subsection('Q15 & Q15a \u2014 System Upgrading Plans'),
        q14,

        _subsection('Q16 \u2014 Interoperability Roadmap Participation'),
        q16,
        _hr(),

        # 4 Interpretation
        _section_header(4, 'Score Interpretation Guide'),
        interp_cards,
        _hr(),

        # 5 Methodological notes
        _section_header(5, 'Methodological Notes'),
        _callout([
            html.Strong('Q10c scoring '),
            '— applicable only when Q10 = No. A confirmed alternate exchange interface scores ',
            _code('0'),
            ' (penalty lifted via ',
            _code('max(\u22122, 0)'),
            '). \u201cNot sure\u201d and \u201cNo\u201d responses score ',
            _code('\u22122'),
            ', reflecting the absence of a confirmed alternative.',
        ], 'orange'),
        _callout([
            html.Strong('Missing or incomplete responses '),
            'are excluded from scoring to avoid introducing bias through imputed values.',
        ], 'orange'),
        _callout([
            html.Strong('Sections 4, 5, 6, and Part 2 '),
            'are reserved for Product Requirements Analysis. These questions do not affect '
            'complexity scores but provide essential context for implementation planning.',
        ], 'blue'),

    ], id='appendix-b', style={
        'fontFamily': "'Segoe UI', Arial, sans-serif",
        'maxWidth': 960, 'margin': '0 auto',
        'color': '#333', 'padding': '0 4px',
    })