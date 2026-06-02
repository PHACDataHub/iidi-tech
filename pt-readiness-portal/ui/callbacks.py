"""
callbacks.py
────────────
All Dash callback definitions for the PT Readiness Dashboard.
Registered via register_all(app, initial_raw, initial_scores).

Callbacks defined here:
  switch_panel   — URL routing + sidebar button → show/hide panels
  update_url     — sidebar button click → push URL
  on_upload      — file upload → update all stores and UI
  update_viewer  — jurisdiction / section filter → render viewer (legacy)
"""

import pandas as pd
from dash import ctx, html
from dash.dependencies import Input, Output, State

from core.constants import BLUE, MID, LIGHT, GREY, PALETTE, JUR_COL, SECTION_ORDER
from core.data      import parse_upload, prepare_data
from ui.chart     import create_bubble_chart
from ui.pages.appendix_c import build_appendix_c
from ui.layout    import build_section_filter


# ─────────────────────────── ROUTING ─────────────────────────────────

_ROUTE_MAP = {
    '/':           'b',
    '/appendix-b': 'b',
    '/appendix-c': 'c',
    '/appendix-d': 'd',
}
_BTN_MAP = {
    'sidebar-btn-b': 'b',
    'sidebar-btn-c': 'c',
    'sidebar-btn-d': 'd',
}

_BTN_ACTIVE = {
    'width': '100%', 'textAlign': 'left', 'border': 'none',
    'padding': '9px 14px', 'fontSize': 13, 'fontWeight': '700',
    'cursor': 'pointer', 'borderRadius': 6, 'marginBottom': 4,
    'backgroundColor': '#2E75B6', 'color': '#FFFFFF',
    'borderLeft': '4px solid #1A3A5C',
}
_BTN_IDLE = {
    'width': '100%', 'textAlign': 'left', 'border': 'none',
    'padding': '9px 14px', 'fontSize': 13, 'fontWeight': '400',
    'cursor': 'pointer', 'borderRadius': 6, 'marginBottom': 4,
    'backgroundColor': '#EDF4FB', 'color': '#1F4E79',
    'borderLeft': '4px solid transparent',
}

_SHOW = {'display': 'block'}
_HIDE = {'display': 'none'}


def _panel_outputs(panel: str):
    """Return the 6-tuple of styles for panels and sidebar buttons."""
    mapping = {
        'b': (_SHOW, _HIDE, _HIDE, _BTN_ACTIVE, _BTN_IDLE,   _BTN_IDLE),
        'c': (_HIDE, _SHOW, _HIDE, _BTN_IDLE,   _BTN_ACTIVE, _BTN_IDLE),
        'd': (_HIDE, _HIDE, _SHOW, _BTN_IDLE,   _BTN_IDLE,   _BTN_ACTIVE),
    }
    return mapping.get(panel, mapping['b'])


# ─────────────────────────── DISPLAY HELPERS ─────────────────────────

def _lighten(hex_color: str, factor: float = 0.45) -> str:
    """Lighten a hex colour by blending it toward white."""
    h = hex_color.lstrip('#')
    r, g, b = (int(h[i:i+2], 16) for i in (0, 2, 4))
    r2 = int(r + (255 - r) * factor)
    g2 = int(g + (255 - g) * factor)
    b2 = int(b + (255 - b) * factor)
    return f'#{r2:02X}{g2:02X}{b2:02X}'


def _round_norm_cols(df: pd.DataFrame) -> pd.DataFrame:
    """Round normalized score columns to 3 d.p. before sending to DataTable."""
    out = df.copy()
    for col in ('DCC (normalized)', 'OC (normalized)'):
        if col in out.columns:
            out[col] = out[col].round(3)
    return out


# ─────────────────────────── REGISTRATION ────────────────────────────

def register_all(app, initial_raw: pd.DataFrame, initial_scores: pd.DataFrame):
    """Register all callbacks on the given Dash app instance."""

    from ui.viewer import render_viewer
    from core.scoring import score_row_breakdown, calculate_scores
    from ui.pages.appendix_c import register_callbacks_c
    from ui.pages.appendix_d import register_callbacks_d

    # ── Third-party appendix callbacks ───────────────────────────────
    register_callbacks_c(app)
    register_callbacks_d(
        app, render_viewer, score_row_breakdown,
        calculate_scores, JUR_COL,
        scores_store_id='scores-store',
        raw_store_id='raw-data-store',
    )

    # ── Routing: URL / sidebar button → panel visibility ─────────────
    @app.callback(
        Output('panel-b', 'style'),
        Output('panel-c', 'style'),
        Output('panel-d', 'style'),
        Output('sidebar-btn-b', 'style'),
        Output('sidebar-btn-c', 'style'),
        Output('sidebar-btn-d', 'style'),
        Input('url', 'pathname'),
        Input('sidebar-btn-b', 'n_clicks'),
        Input('sidebar-btn-c', 'n_clicks'),
        Input('sidebar-btn-d', 'n_clicks'),
        prevent_initial_call=False,
    )
    def switch_panel(pathname, _nb, _nc, _nd):
        triggered = ctx.triggered_id or 'url'
        if triggered == 'url':
            panel = _ROUTE_MAP.get(pathname or '/', 'b')
        else:
            panel = _BTN_MAP.get(triggered, 'b')
        return _panel_outputs(panel)

    # ── Routing: sidebar button click → push URL ──────────────────────
    @app.callback(
        Output('url', 'pathname'),
        Input('sidebar-btn-b', 'n_clicks'),
        Input('sidebar-btn-c', 'n_clicks'),
        Input('sidebar-btn-d', 'n_clicks'),
        prevent_initial_call=True,
    )
    def update_url(_nb, _nc, _nd):
        routes = {
            'sidebar-btn-b': '/appendix-b',
            'sidebar-btn-c': '/appendix-c',
            'sidebar-btn-d': '/appendix-d',
        }
        return routes.get(ctx.triggered_id, '/appendix-b')

    # ── File upload → update all stores and dependent UI ─────────────
    @app.callback(
        Output('scores-store',                'data'),
        Output('raw-data-store',              'data'),
        Output('summary-table',               'data'),
        Output('bubble-chart',                'figure'),
        Output('raw-jurisdiction-dropdown',   'options'),
        Output('raw-jurisdiction-dropdown',   'value'),
        Output('section-filter-container',    'children'),
        Output('summary-tables-container',    'children'),
        Output('upload-status',               'children'),
        Input('upload-data', 'contents'),
        State('upload-data', 'filename'),
        prevent_initial_call=False,
    )
    def on_upload(contents, filename):
        raw_df           = parse_upload(contents, filename) if contents else initial_raw
        clean_df, scores = prepare_data(raw_df)

        # Score table rows (rounded for display)
        display_cols = [
            'Jurisdiction', 'Respondent',
            'Data Connection Complexity', 'Operational Complexity',
            'DCC (normalized)', 'OC (normalized)', 'Readiness Band',
        ]
        table_rows = (
            _round_norm_cols(scores[display_cols]).to_dict('records')
            if not scores.empty else []
        )

        # Jurisdiction dropdown options
        all_jurs    = list(clean_df[JUR_COL].unique()) if not clean_df.empty else []
        jur_options = [{'label': j, 'value': j} for j in all_jurs]
        jur_value   = all_jurs[0] if all_jurs else None

        # Section filter widget
        from core.constants import COL_META
        seen_sections = []
        for col in (clean_df.columns if not clean_df.empty else []):
            prefix = str(col).split(':')[0].strip()
            sec    = COL_META.get(prefix, ('Other', None))[0]
            if sec not in seen_sections:
                seen_sections.append(sec)
        section_ui = build_section_filter(seen_sections)

        # Upload status badge
        n_jurs = len(all_jurs)
        status = (
            f'\u2705  {filename}  \u2014  '
            f'{n_jurs} jurisdiction{"s" if n_jurs != 1 else ""} loaded'
            if contents and filename else ''
        )

        return (
            scores.to_json(date_format='iso', orient='split'),
            clean_df.to_json(date_format='iso', orient='split'),
            table_rows,
            create_bubble_chart(scores),
            jur_options, jur_value,
            section_ui,
            build_appendix_c(clean_df),
            status,
        )

    # ── Legacy viewer (used by hidden raw-data-table stub) ────────────
    @app.callback(
        Output('raw-data-table', 'children'),
        Input('raw-jurisdiction-dropdown', 'value'),
        Input('section-checklist', 'value'),
        State('raw-data-store', 'data'),
        prevent_initial_call=False,
    )
    def update_viewer(jurisdiction, selected_sections, raw_json):
        if not raw_json or not jurisdiction:
            return html.Div(
                'Upload a file and select a jurisdiction.',
                style={'color': GREY, 'padding': 20,
                       'fontStyle': 'italic', 'fontSize': 13},
            )

        raw_df  = pd.read_json(raw_json, orient='split')
        matched = raw_df[raw_df[JUR_COL] == jurisdiction]

        if matched.empty:
            return html.Div(f'No data for {jurisdiction}.',
                            style={'color': GREY, 'padding': 16})

        jur_color_map = {
            str(jur).strip(): PALETTE[ci % len(PALETTE)]
            for ci, jur in enumerate(raw_df[JUR_COL].unique())
        }
        accent = jur_color_map.get(str(jurisdiction).strip(), BLUE)

        if len(matched) == 1:
            rows_list = [(matched.iloc[0], '', accent)]
            header    = None
        else:
            shades    = [accent, _lighten(accent, 0.40)]
            rows_list = [
                (row_s, f"Respondent {i+1} ({str(row_s.get('Date','')).strip()})",
                 shades[i % len(shades)])
                for i, (_, row_s) in enumerate(matched.iterrows())
            ]
            header = html.Div([
                html.Div(
                    'Two respondents submitted for this province — differences highlighted',
                    style={
                        'background': '#F0F7FF', 'border': f'1px solid {MID}',
                        'borderRadius': 5, 'padding': '7px 14px', 'marginBottom': 8,
                        'fontSize': 12, 'color': BLUE, 'fontWeight': '600',
                    }
                ),
                html.Div([
                    html.Div([
                        html.Span('●', style={
                            'color': rows_list[i][2], 'marginRight': 5, 'fontSize': 16,
                        }),
                        html.Span(rows_list[i][1], style={
                            'fontSize': 12, 'fontWeight': '600',
                        }),
                    ], style={'flex': 1, 'paddingLeft': 8 if i > 0 else 0})
                    for i in range(len(rows_list))
                ], style={'display': 'flex', 'gap': 8,
                          'marginBottom': 8, 'paddingLeft': '30%'}),
            ])

        content = render_viewer(rows_list, raw_df, selected_sections or [])
        return html.Div([header, content] if header else [content])