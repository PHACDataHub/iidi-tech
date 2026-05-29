"""
appendix_c.py
─────────────
Appendix C — Survey Response Summary Tables
Re-export of summary_tables.py under the appendix naming convention.

Usage in app.py:
    from appendix_c import build_appendix_c, register_callbacks_c
"""

from summary_tables import build_summary_section, register_callbacks


def build_appendix_c(df):
    """Return the Appendix C summary tables Div."""
    from dash import html
    div = build_summary_section(df)
    # Wrap with appendix anchor id
    div.id = 'appendix-c'
    return div


def register_callbacks_c(app):
    register_callbacks(app)