"""
sidebar.py
──────────
Right-hand sticky sidebar for the PT Readiness Dashboard.
Three buttons switch between Appendix B, C, and D panels.
"""

from dash import html

BLUE  = '#2E75B6'
DARK  = '#1F4E79'
LIGHT = '#D6E4F0'
WHITE = '#FFFFFF'

BTN_ACTIVE = {
    'width': '100%', 'textAlign': 'left', 'border': 'none',
    'padding': '9px 14px', 'fontSize': 13, 'fontWeight': '700',
    'cursor': 'pointer', 'borderRadius': 6, 'marginBottom': 4,
    'backgroundColor': BLUE, 'color': WHITE,
    'borderLeft': f'4px solid {DARK}',
}
BTN_IDLE = {
    'width': '100%', 'textAlign': 'left', 'border': 'none',
    'padding': '9px 14px', 'fontSize': 13, 'fontWeight': '400',
    'cursor': 'pointer', 'borderRadius': 6, 'marginBottom': 4,
    'backgroundColor': '#EDF4FB', 'color': DARK,
    'borderLeft': '4px solid transparent',
}

_SECTIONS = [
    ('sidebar-btn-b', 'Appendix B', 'Scoring Methodology & Rubric', [
        'Overview',
        'Scoring Structure',
        'Scoring Rules',
        'Interpretation Guide',
        'Methodological Notes',
    ]),
    ('sidebar-btn-c', 'Appendix C', 'Survey Response Summary Tables', [
        'Section 1 — Data Collection',
        'Section 2 — Data Storage',
        'Section 3 — Data Access',
        'Section 4 — Data Sharing',
        'Section 5 — Data Quality',
        'Section 6 — Archiving',
        'Part 2 — Governance',
    ]),
    ('sidebar-btn-d', 'Appendix D', 'Jurisdiction-Level Breakdown', [
        'D1 — Scoring Grid',
        'D2 — Complexity Matrix',
        'D3 — Response Viewer',
    ]),
]


def build_sidebar():
    children = [
        html.Div('Contents', style={
            'fontSize': 10, 'fontWeight': '700', 'color': DARK,
            'textTransform': 'uppercase', 'letterSpacing': '0.1em',
            'marginBottom': 10, 'paddingBottom': 6,
            'borderBottom': f'2px solid {BLUE}',
        }),
    ]

    for btn_id, label, subtitle, sub_items in _SECTIONS:
        # Main button — active state set by default only for B
        active = btn_id == 'sidebar-btn-b'
        route_map = {
            'sidebar-btn-b': '/appendix-b',
            'sidebar-btn-c': '/appendix-c',
            'sidebar-btn-d': '/appendix-d',
        }
        children.append(
            html.Button(
                [
                    html.Div(label, style={'fontSize': 13, 'fontWeight': '700'}),
                    html.Div(subtitle, style={
                        'fontSize': 10, 'opacity': 0.75,
                        'marginTop': 2, 'fontWeight': '400',
                        'whiteSpace': 'normal', 'lineHeight': '1.3',
                    }),
                ],
                id=btn_id,
                n_clicks=0,
                title=route_map.get(btn_id, ''),
                style=BTN_ACTIVE if active else BTN_IDLE,
            )
        )
        # Sub-items (static, decorative)
        children.append(html.Div([
            html.Div(item, style={
                'fontSize': 10, 'color': '#666',
                'padding': '2px 0 2px 18px',
                'borderLeft': f'2px solid {LIGHT}',
                'marginLeft': 8, 'lineHeight': '1.5',
            })
            for item in sub_items
        ], style={'marginBottom': 8}))

    return html.Div(children, style={
        'position': 'sticky',
        'top': 20,
        'width': 200,
        'minWidth': 200,
        'flexShrink': 0,
        'background': WHITE,
        'border': f'1px solid {LIGHT}',
        'borderRadius': 8,
        'padding': '14px 12px',
        'alignSelf': 'flex-start',
        'maxHeight': 'calc(100vh - 40px)',
        'overflowY': 'auto',
        'fontFamily': "'Segoe UI', Arial, sans-serif",
        'boxShadow': '0 2px 8px rgba(0,0,0,0.07)',
        'marginLeft': 24,
        'marginTop': 20,
    })