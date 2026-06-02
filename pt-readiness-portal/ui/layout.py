"""
layout.py
─────────
Assembles the full Dash layout for the PT Readiness Dashboard.
All visual structure lives here; business logic stays in other modules.

Public API
──────────
build_layout(initial_raw, initial_scores)  →  html.Div (app.layout)
build_section_filter(sections_present)     →  html.Details widget
"""

import pandas as pd
from dash import dcc, html, dash_table

from core.constants import BLUE, MID, LIGHT, GREY, WHITE, SECTION_ORDER, JUR_COL
from ui.chart     import create_bubble_chart
from ui.pages.appendix_b import build_appendix_b
from ui.pages.appendix_c import build_appendix_c
from ui.pages.appendix_d import build_appendix_d
from ui.sidebar    import build_sidebar


# ─────────────────────────── SECTION FILTER ──────────────────────────

def build_section_filter(sections_present: list) -> html.Details:
    """
    Build the collapsible section-filter checklist shown above the viewer.
    Sections are displayed in rubric order; unknown sections appended at the end.
    """
    ordered  = [s for s in SECTION_ORDER if s in sections_present]
    ordered += [s for s in sections_present if s not in SECTION_ORDER]
    options  = [{'label': s, 'value': s} for s in ordered]

    return html.Details([
        html.Summary('⚙ Filter question sections', style={
            'cursor': 'pointer', 'fontWeight': '600', 'color': BLUE, 'fontSize': 13,
            'padding': '7px 12px', 'backgroundColor': '#EDF4FB',
            'borderRadius': '5px 5px 0 0', 'listStyle': 'none', 'userSelect': 'none',
        }),
        html.Div([
            html.Span('Select which sections to display:', style={
                'fontSize': 11, 'color': GREY, 'display': 'block', 'marginBottom': 6,
            }),
            dcc.Checklist(
                id='section-checklist',
                options=options,
                value=[s['value'] for s in options],
                labelStyle={
                    'display': 'inline-flex', 'alignItems': 'center',
                    'marginRight': 14, 'marginBottom': 4,
                    'fontSize': 12, 'cursor': 'pointer', 'color': '#222',
                },
                inputStyle={'marginRight': 4, 'accentColor': BLUE},
            ),
        ], style={
            'padding': '10px 14px', 'border': f'1px solid {LIGHT}',
            'borderTop': 'none', 'borderRadius': '0 0 5px 5px', 'background': '#FAFCFF',
        }),
    ], style={'border': f'1px solid {LIGHT}', 'borderRadius': 6, 'marginBottom': 12})


# ─────────────────────────── HIDDEN STORES & STUBS ───────────────────

def _build_stores(initial_raw: pd.DataFrame, initial_scores: pd.DataFrame) -> html.Div:
    """
    Invisible Div holding dcc.Store components and legacy callback stubs.
    display:none so nothing renders on screen.
    """
    return html.Div([
        dcc.Store(id='scores-store',
                  data=initial_scores.to_json(date_format='iso', orient='split')),
        dcc.Store(id='raw-data-store',
                  data=initial_raw.to_json(date_format='iso', orient='split')),
        # Legacy stubs — required by existing callbacks but not visible
        html.Div(id='raw-data-table',            style={'display': 'none'}),
        html.Div(id='section-filter-container',  style={'display': 'none'}),
        dcc.Dropdown(id='raw-jurisdiction-dropdown',        style={'display': 'none'}),
        dcc.Dropdown(id='raw-jurisdiction-dropdown-hidden', style={'display': 'none'}),
        html.Div(dash_table.DataTable(id='summary-table'),  style={'display': 'none'}),
        dcc.Graph(id='bubble-chart',
                  figure=create_bubble_chart(initial_scores),
                  style={'display': 'none'}),
    ], style={'display': 'none'})


# ─────────────────────────── UPLOAD BAR ──────────────────────────────

def _build_upload_bar() -> html.Div:
    """
    Persistent file upload bar, always visible regardless of active panel.
    Uploads feed the shared stores and propagate to all appendices.
    """
    return html.Div([
        dcc.Upload(
            id='upload-data',
            children=html.Div([
                '\U0001f4c2  Drag & drop or ',
                html.A('select a CSV / Excel file',
                       style={'color': BLUE, 'textDecoration': 'underline'}),
            ]),
            style={
                'flex': 1, 'height': '42px', 'lineHeight': '42px',
                'borderWidth': '1.5px', 'borderStyle': 'dashed', 'borderRadius': 6,
                'textAlign': 'center', 'color': GREY,
                'backgroundColor': '#FAFAFA', 'fontSize': 13, 'cursor': 'pointer',
            },
            multiple=False,
        ),
        html.Div(id='upload-status', style={
            'fontSize': 12, 'color': '#375623', 'fontWeight': '600',
            'padding': '0 14px', 'whiteSpace': 'nowrap', 'alignSelf': 'center',
        }),
    ], style={
        'display': 'flex', 'gap': 12, 'alignItems': 'stretch',
        'padding': '10px 28px', 'backgroundColor': '#EDF4FB',
        'borderBottom': f'1px solid {LIGHT}',
    })


# ─────────────────────────── HEADER BAR ──────────────────────────────

def _build_header() -> html.Div:
    return html.Div([
        html.H1('PT Readiness Dashboard', style={
            'color': WHITE, 'margin': 0, 'fontSize': 22,
            'fontWeight': '700', 'letterSpacing': '0.02em',
        }),
    ], style={
        'background': f'linear-gradient(135deg, #1A3A5C 0%, {MID} 100%)',
        'padding': '14px 28px',
    })


# ─────────────────────────── PANELS ──────────────────────────────────

def _build_panels(initial_raw: pd.DataFrame,
                  initial_scores: pd.DataFrame) -> list:
    """
    Build the three appendix panels.
    Only panel-b is visible on initial load; the routing callback switches them.
    """
    panel_b = html.Div(
        [build_appendix_b()],
        id='panel-b',
        style={'display': 'block'},
    )
    panel_c = html.Div(
        [html.Div(id='summary-tables-container')],
        id='panel-c',
        style={'display': 'none'},
    )
    panel_d = html.Div(
        [build_appendix_d(initial_scores, initial_raw, JUR_COL)],
        id='panel-d',
        style={'display': 'none'},
    )
    return [panel_b, panel_c, panel_d]


# ─────────────────────────── MAIN LAYOUT ─────────────────────────────

def build_layout(initial_raw: pd.DataFrame,
                 initial_scores: pd.DataFrame) -> html.Div:
    """
    Assemble and return the top-level Dash layout.

    Structure:
        dcc.Location      (URL routing — invisible)
        stores + stubs    (invisible)
        header bar
        upload bar        (always visible — shared across all panels)
        body
          ├── content     (panel-b / panel-c / panel-d)
          └── sidebar     (sticky right-hand nav)
    """
    return html.Div([
        dcc.Location(id='url', refresh=False),
        _build_stores(initial_raw, initial_scores),
        _build_header(),
        _build_upload_bar(),
        html.Div([
            html.Div(
                _build_panels(initial_raw, initial_scores),
                style={'flex': 1, 'minWidth': 0, 'padding': '20px 0'},
            ),
            build_sidebar(),
        ], style={
            'display': 'flex', 'gap': 0, 'alignItems': 'flex-start',
            'maxWidth': 1320, 'margin': '0 auto', 'padding': '0 20px',
        }),
    ], style={
        'fontFamily': "'Segoe UI', Arial, sans-serif",
        'backgroundColor': '#F5F7FA',
        'minHeight': '100vh',
    })