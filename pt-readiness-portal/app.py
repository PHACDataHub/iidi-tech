"""
app.py
──────
PT Readiness Dashboard — application entry point.

Responsibilities:
  - Create the Dash app instance
  - Assemble the layout (delegated to ui/layout.py)
  - Register all callbacks (delegated to ui/callbacks.py)
  - Expose the WSGI server object for deployment

Project layout:
  app.py                 — entry point (this file)
  core/
    constants.py         — colour tokens, column metadata, section ordering
    scoring.py           — rubric scoring logic (score_row, calculate_scores, …)
    data.py              — file parsing, env-var loading, prepare_data pipeline
  ui/
    layout.py            — Dash layout assembly
    callbacks.py         — all @app.callback definitions
    chart.py             — bubble chart (Adoption Complexity Matrix)
    viewer.py            — survey response viewer, checkbox renderers, rubric cards
    sidebar.py           — sticky right-hand navigation sidebar
    pages/
      appendix_b.py      — scoring methodology & rubric (Appendix B)
      appendix_c.py      — summary tables (Appendix C)
      appendix_d.py      — jurisdiction breakdown, scoring grid, chart (Appendix D)
      summary_tables.py  — survey response count tables (Q1–Q28)
"""

import dash

from core.data   import try_load_default, prepare_data
from ui.layout   import build_layout
import ui.callbacks as callbacks

# ─────────────────────────── APP INSTANCE ────────────────────────────

app = dash.Dash(
    __name__,
    title='PT Readiness Dashboard',
    suppress_callback_exceptions=True,
)
server = app.server   # expose for gunicorn / Flask deployment


@server.route('/healthcheck')
def healthcheck():
    return 'ok', 200


# ─────────────────────────── STARTUP DATA ────────────────────────────
# Pre-load from SURVEY_CSV env var if available; otherwise start empty.

initial_raw, initial_scores = prepare_data(try_load_default())


# ─────────────────────────── LAYOUT & CALLBACKS ──────────────────────

app.layout = build_layout(initial_raw, initial_scores)
callbacks.register_all(app, initial_raw, initial_scores)


# ─────────────────────────── ENTRY POINT ─────────────────────────────

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8050, debug=False)