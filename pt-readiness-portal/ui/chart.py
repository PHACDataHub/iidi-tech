"""
chart.py
────────
Bubble chart (Adoption Complexity Matrix) for the PT Readiness Dashboard.

Public API
──────────
create_bubble_chart(scores_df)  → plotly Figure
"""

import plotly.graph_objects as go
import pandas as pd

from core.constants import PALETTE, LIGHT, GREY, WHITE


def create_bubble_chart(scores: pd.DataFrame) -> go.Figure:
    """
    Build the Adoption Complexity Matrix — a scatter/bubble chart with
    normalized DCC on the x-axis and normalized OC on the y-axis.

    Each jurisdiction is a labelled bubble coloured by its index in PALETTE.
    The four quadrants are lightly shaded to indicate readiness zones.
    """
    fig = go.Figure()

    if scores.empty:
        fig.add_annotation(
            text="Upload a CSV or Excel file to get started.",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=14, color=GREY),
        )
        fig.update_layout(plot_bgcolor=WHITE, paper_bgcolor=WHITE, height=560)
        return fig

    axis_range = [-1.15, 1.15]

    # Quadrant shading: (x0, y0, x1, y1, fill_colour)
    _quadrants = [
        (-1.15,  0,     0,    1.15, 'rgba(255,242,204,0.22)'),  # top-left:  moderate
        ( 0,     0,    1.15,  1.15, 'rgba(213,232,212,0.22)'),  # top-right: high
        (-1.15, -1.15,  0,    0,    'rgba(252,228,214,0.22)'),  # bot-left:  low
        ( 0,   -1.15,  1.15,  0,    'rgba(244,204,204,0.22)'),  # bot-right: very low
    ]
    for x0, y0, x1, y1, colour in _quadrants:
        fig.add_shape(
            type='rect', x0=x0, y0=y0, x1=x1, y1=y1,
            fillcolor=colour, line_width=0, layer='below',
        )

    fig.add_hline(y=0, line=dict(color='#BBBBBB', dash='dash', width=1))
    fig.add_vline(x=0, line=dict(color='#BBBBBB', dash='dash', width=1))

    for _, row in scores.iterrows():
        colour  = PALETTE[int(row['_color_idx']) % len(PALETTE)]
        x_pos   = row.get('_x', row['_dcc_norm'])
        y_pos   = row.get('_y', row['_oc_norm'])
        true_x  = row['_dcc_norm']
        true_y  = row['_oc_norm']
        raw_dcc = int(row['Data Connection Complexity'])
        raw_oc  = int(row['Operational Complexity'])

        # Draw a dotted line from true position to jittered position (if jitter applied)
        if abs(x_pos - true_x) > 0.001 or abs(y_pos - true_y) > 0.001:
            fig.add_shape(
                type='line', x0=true_x, y0=true_y, x1=x_pos, y1=y_pos,
                line=dict(color=colour, width=1, dash='dot'), layer='below',
            )

        hover = (
            f"<b>{row['Jurisdiction']}</b><br>"
            f"DCC: {raw_dcc}&nbsp;&nbsp;OC: {raw_oc}<br>"
            f"Readiness: {row['Readiness Band']}<br>"
            f"Respondent: {row.get('Respondent', '')}"
            "<extra></extra>"
        )

        fig.add_trace(go.Scatter(
            x=[x_pos], y=[y_pos],
            mode='markers+text',
            marker=dict(
                size=54, color=colour, opacity=0.93,
                line=dict(width=1.5, color='rgba(255,255,255,0.5)'),
            ),
            text=[row['Short']],
            textposition='middle center',
            textfont=dict(color=WHITE, size=12, family='Arial Black'),
            name=row['Jurisdiction'],
            hovertemplate=hover,
            showlegend=True,
        ))

    tick_vals  = [-1, -0.5, 0, 0.5, 1]
    tick_texts = ['-1', '-0.5', '0', '+0.5', '+1']

    fig.update_layout(
        xaxis=dict(
            title='Integration Simplicity →',
            zeroline=False, gridcolor='#EEEEEE', range=axis_range,
            tickvals=tick_vals, ticktext=tick_texts,
            title_font=dict(size=12), tickfont=dict(size=11),
        ),
        yaxis=dict(
            title='Operational Simplicity →',
            zeroline=False, gridcolor='#EEEEEE', range=axis_range,
            tickvals=tick_vals, ticktext=tick_texts,
            title_font=dict(size=12), tickfont=dict(size=11),
        ),
        plot_bgcolor=WHITE, paper_bgcolor=WHITE,
        legend=dict(
            title='Jurisdiction', font=dict(size=11),
            bgcolor='rgba(255,255,255,0.9)',
            bordercolor=LIGHT, borderwidth=1,
            x=1.01, xanchor='left', y=1, yanchor='top',
        ),
        height=600,
        margin=dict(l=60, r=180, t=30, b=60),
        hovermode='closest',
    )
    return fig