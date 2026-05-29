"""
appendix_d.py
─────────────
Appendix D — Jurisdiction-Level Breakdown
"""

import pandas as pd
from dash import html, dcc, dash_table
from dash.dependencies import Input, Output, State

BLUE   = '#2E75B6'
DARK   = '#1F4E79'
GREEN  = '#375623'
WHITE  = '#FFFFFF'
LIGHT  = '#D6E4F0'
LGREY  = '#F2F7FB'
LGREEN = '#E2EFDA'
RED    = '#C00000'
GREY   = '#595959'


def _section_header(title, subtitle=None):
    return html.Div([
        html.Div(title, style={
            'background': DARK, 'color': '#fff',
            'padding': '12px 24px', 'borderRadius': '6px 6px 0 0',
            'fontSize': 18, 'fontWeight': 'bold',
        }),
        *([] if not subtitle else [html.Div(subtitle, style={
            'background': '#EBF3FB', 'color': DARK,
            'padding': '8px 24px', 'fontSize': 13,
            'borderBottom': f'1px solid {LIGHT}',
        })]),
    ])


def _score_table():
    return dash_table.DataTable(
        id='d-score-table',
        columns=[
            {'name': 'Jurisdiction',  'id': 'Jurisdiction'},
            {'name': 'Respondent',    'id': 'Respondent'},
            {'name': 'DCC (raw)',     'id': 'Data Connection Complexity'},
            {'name': 'OC (raw)',      'id': 'Operational Complexity'},
            {'name': 'DCC (norm.)',   'id': 'DCC (normalized)'},
            {'name': 'OC (norm.)',    'id': 'OC (normalized)'},
            {'name': 'Readiness Band','id': 'Readiness Band'},
        ],
        data=[],
        style_header={
            'backgroundColor': BLUE, 'color': WHITE,
            'fontWeight': 'bold', 'fontSize': 12, 'textAlign': 'center',
        },
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
            {'if': {'filter_query': '{DCC (normalized)} > 0',
                    'column_id': 'DCC (normalized)'}, 'color': GREEN, 'fontWeight': 'bold'},
            {'if': {'filter_query': '{DCC (normalized)} < 0',
                    'column_id': 'DCC (normalized)'}, 'color': RED, 'fontWeight': 'bold'},
            {'if': {'filter_query': '{OC (normalized)} > 0',
                    'column_id': 'OC (normalized)'}, 'color': GREEN, 'fontWeight': 'bold'},
            {'if': {'filter_query': '{OC (normalized)} < 0',
                    'column_id': 'OC (normalized)'}, 'color': RED, 'fontWeight': 'bold'},
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
    )


def build_appendix_d(initial_scores, initial_raw, jur_col):
    jur_options = (
        [{'label': j, 'value': j}
         for j in sorted(initial_raw[jur_col].dropna().unique())]
        if not initial_raw.empty else []
    )
    default_jur = jur_options[0]['value'] if jur_options else None

    return html.Div([

        # ── D3: Jurisdiction Viewer (top) ────────────────────────────
        html.Div([
            _section_header(
                'D3 \u00a0 Jurisdiction Survey Response Viewer',
                'Select a jurisdiction to view their full survey responses with rubric annotations',
            ),
            html.Div([
                html.Div([
                    html.Label('Jurisdiction:', style={
                        'fontWeight': 'bold', 'marginRight': 8,
                        'fontSize': 13, 'color': GREY,
                    }),
                    dcc.Dropdown(
                        id='d-jurisdiction-dropdown',
                        options=jur_options,
                        value=default_jur,
                        placeholder='Choose a jurisdiction\u2026',
                        clearable=False,
                        style={'width': 320, 'display': 'inline-block', 'fontSize': 13},
                    ),
                ], style={'marginBottom': 10}),
                html.Div(id='d-section-filter'),
            ], style={
                'padding': '14px 16px', 'backgroundColor': '#FAFAFA',
                'border': f'1px solid {LIGHT}', 'borderTop': 'none', 'borderBottom': 'none',
            }),
            html.Div(id='d-viewer-content', style={
                'maxHeight': 680, 'overflowY': 'auto',
                'border': f'1px solid {LIGHT}', 'borderTop': 'none',
                'borderRadius': '0 0 6px 6px', 'backgroundColor': WHITE,
            }),
        ], style={'marginBottom': 28}),

        # ── D1: Scoring Grid ─────────────────────────────────────────
        html.Div([
            _section_header(
                'D1 \u00a0 Technical Readiness Scores',
                'Raw and normalized DCC / OC scores per jurisdiction',
            ),
            html.Div(
                _score_table(),
                style={
                    'padding': '16px', 'backgroundColor': WHITE,
                    'border': f'1px solid {LIGHT}',
                    'borderTop': 'none', 'borderRadius': '0 0 6px 6px',
                }
            ),
        ], style={'marginBottom': 28}),

        # ── D2: Adoption Complexity Matrix ───────────────────────────
        html.Div([
            _section_header(
                'D2 \u00a0 Adoption Complexity Matrix',
                'DCC vs OC \u2014 bubble size proportional to normalized score magnitude',
            ),
            html.Div(
                dcc.Graph(id='d-bubble-chart', figure={},
                          style={'width': '100%', 'minHeight': 420}),
                style={
                    'padding': '8px 0', 'backgroundColor': WHITE,
                    'border': f'1px solid {LIGHT}',
                    'borderTop': 'none', 'borderRadius': '0 0 6px 6px',
                }
            ),
        ], style={'marginBottom': 28}),

    ], id='appendix-d', style={'fontFamily': "'Segoe UI', Arial, sans-serif"})


def register_callbacks_d(app, render_viewer_fn, score_row_breakdown_fn,
                          calculate_scores_fn, jur_col,
                          scores_store_id='scores-store',
                          raw_store_id='raw-data-store'):

    @app.callback(
        Output('d-score-table', 'data'),
        Output('d-bubble-chart', 'figure'),
        Input(scores_store_id, 'data'),
    )
    def update_d_score_table(scores_json):
        if not scores_json:
            return [], {}
        scores = pd.read_json(scores_json, orient='split')
        display_cols = [
            'Jurisdiction', 'Respondent',
            'Data Connection Complexity', 'Operational Complexity',
            'DCC (normalized)', 'OC (normalized)', 'Readiness Band',
        ]
        if not scores.empty:
            disp = scores[[c for c in display_cols if c in scores.columns]].copy()
            for c in ['DCC (normalized)', 'OC (normalized)']:
                if c in disp.columns:
                    disp[c] = disp[c].round(3)
            rows = disp.to_dict('records')
        else:
            rows = []
        from app import create_bubble_chart
        return rows, create_bubble_chart(scores)

    @app.callback(
        Output('d-jurisdiction-dropdown', 'options'),
        Output('d-jurisdiction-dropdown', 'value'),
        Input(raw_store_id, 'data'),
    )
    def update_d_dropdown(raw_json):
        if not raw_json:
            return [], None
        raw = pd.read_json(raw_json, orient='split')
        if raw.empty or jur_col not in raw.columns:
            return [], None
        opts = [{'label': j, 'value': j}
                for j in sorted(raw[jur_col].dropna().unique())]
        return opts, (opts[0]['value'] if opts else None)

    @app.callback(
        Output('d-section-filter',  'children'),
        Output('d-viewer-content',  'children'),
        Input('d-jurisdiction-dropdown', 'value'),
        State(raw_store_id,    'data'),
        State(scores_store_id, 'data'),
        prevent_initial_call=False,
    )
    def update_d_viewer(jur, raw_json, scores_json):
        if not jur or not raw_json:
            return '', html.Div(
                'Upload a file to view jurisdiction responses.',
                style={'padding': 20, 'color': '#888', 'fontStyle': 'italic', 'fontSize': 13},
            )
        raw  = pd.read_json(raw_json, orient='split')
        rows = raw[raw[jur_col] == jur]
        if rows.empty:
            return '', html.P('No data for this jurisdiction.',
                              style={'padding': 16, 'color': '#888'})

        from app import COL_META, SECTION_ORDER, PALETTE, _lighten, BLUE as APP_BLUE

        jur_color_map = {}
        for ci, j in enumerate(raw[jur_col].unique()):
            jur_color_map[str(j).strip()] = PALETTE[ci % len(PALETTE)]
        accent = jur_color_map.get(str(jur).strip(), APP_BLUE)

        if len(rows) == 1:
            rows_list = [(rows.iloc[0], '', accent)]
        else:
            shades = [accent, _lighten(accent, 0.40)]
            rows_list = [
                (row_s, f'Respondent {i+1}', shades[i % len(shades)])
                for i, (_, row_s) in enumerate(rows.iterrows())
            ]

        viewer = render_viewer_fn(rows_list, raw, selected_sections=None)

        sections_present = set()
        for col in raw.columns:
            prefix = str(col).split(':')[0].strip()
            if prefix in COL_META:
                sections_present.add(COL_META[prefix][0])

        section_filter = html.Div([
            html.Span('Sections: ', style={
                'fontSize': 12, 'color': GREY, 'fontWeight': 'bold', 'marginRight': 6,
            }),
            *[
                html.Span(
                    s.split('\u2014')[-1].strip() if '\u2014' in s else s,
                    style={
                        'fontSize': 11, 'padding': '2px 8px',
                        'background': '#EBF3FB', 'color': DARK,
                        'borderRadius': 10, 'marginRight': 4,
                        'display': 'inline-block',
                    }
                )
                for s in SECTION_ORDER if s in sections_present
            ],
        ])

        return section_filter, viewer