"""
scoring.py
──────────
All scoring logic for the PT Readiness Dashboard.

Public API
──────────
score_row(row)              → (dcc_raw, oc_raw)
score_row_breakdown(row)    → dict of per-question (dcc, oc, signal) tuples
normalize_dcc(raw)          → float in [-1, 1]
normalize_oc(raw)           → float in [-1, 1]
readiness_band(dcc, oc)     → 'High' | 'Moderate' | 'Low' | 'Very Low'
deduplicate(df)             → cleaned DataFrame
calculate_scores(df)        → scores DataFrame
"""

import pandas as pd
from core.constants import (
    JUR_COL, UNKNOWN_JUR, PROVINCE_SHORT,
    DCC_MIN, DCC_MAX, OC_MIN, OC_MAX,
    PALETTE,
)


# ─────────────────────────── HELPERS ─────────────────────────────────

def short(name):
    return PROVINCE_SHORT.get(str(name).strip(), str(name)[:3].upper())


def normalize_dcc(raw):
    """Map raw DCC score to [-1, +1] using known min/max bounds."""
    mid  = (DCC_MAX + DCC_MIN) / 2   # 3.0
    half = (DCC_MAX - DCC_MIN) / 2   # 11.0
    return round((raw - mid) / half, 4)


def normalize_oc(raw):
    """Map raw OC score to [-1, +1] using known min/max bounds."""
    mid  = (OC_MAX + OC_MIN) / 2     # 3.0
    half = (OC_MAX - OC_MIN) / 2     # 17.0
    return round((raw - mid) / half, 4)


def readiness_band(dcc_s, oc_s):
    """Classify a jurisdiction into a readiness band based on raw scores."""
    avg = (dcc_s + oc_s) / 2
    if avg >= 8: return 'High'
    if avg >= 4: return 'Moderate'
    if avg >= 0: return 'Low'
    return 'Very Low'


# ─────────────────────────── Q10 SUB-SCORERS ─────────────────────────

def score_api_protocol(rest, soap, amqp, other):
    """Q10a — API protocol. Returns +2 for standard, -2 for custom/none."""
    if pd.notna(rest)  and rest  == 1: return 2
    if pd.notna(soap)  and soap  == 1: return 2
    if pd.notna(amqp)  and amqp  == 1: return 2
    if pd.notna(other) and str(other).strip() != '': return -2
    return -2


def score_auth(saml, oauth, other):
    """
    Q10b — API authentication.
    SAML / OAuth → +2.
    Free-text containing SAML / OAuth / OIDC → +2 (app extension beyond rubric).
    Custom or blank → -2.
    """
    if pd.notna(saml)  and saml  == 1: return 2
    if pd.notna(oauth) and oauth == 1: return 2
    if pd.notna(other) and str(other).strip() != '':
        upper = str(other).upper()
        if any(kw in upper for kw in ('SAML', 'OAUTH', 'OIDC')):
            return 2
        return -2
    return -2


def score_10c(no_val, not_sure, yes_val):
    """Q10c — other exchange interfaces. Yes → 0, No/Not sure/blank → -2."""
    if pd.notna(yes_val) and str(yes_val).strip() not in ('', '0', 'nan', '0.0'):
        try:
            return 0 if float(yes_val) != 0 else -2
        except (ValueError, TypeError):
            return 0
    if pd.notna(no_val)   and no_val   == 1: return -2
    if pd.notna(not_sure) and not_sure == 1: return -2
    return -2


# ─────────────────────────── ROW SCORERS ─────────────────────────────
# Survey column names are long; aliased once here for readability.

_Q2   = '4: 2. Does your jurisdiction have an official provincial/territorial immunization registry/repository?'
_Q3   = '5: 3. Is your registry/repository implemented using Panorama?'
_Q5   = '9: 5. Where is your immunization registry/repository hosted?'
_Q6A  = '10: 6a. Is there Auditing of Logins in place for all registry/repository access?'
_Q6B  = '11: 6b. Is there logging of user activities in place for all registry/repository transactions?'
_Q7   = '12: 7. To ensure reliability and availability of data in the registry/repository, are there backups and mechanisms for disaster recovery?'
_Q10  = '15: 9. Does your registry/repository have externally accessible Application Programming Interfaces (API) covering functionality needed to access and exchange immunization data?'
_Q14  = '24: 14. Are you currently upgrading or replacing any components of your immunization registry/repository or its technical ecosystem? (e.g., hosting environment, data exchange standards, interfaces with EMRs/EHRs, or other major system changes that will impact immunization data collection and sharing)'
_Q14A = '25: 14a. If not, have any decisions or plans being made towards future upgrading or replacing of any components of your immunization registry/repository or its technical ecosystem?'


def _q2_score(row):
    val = str(row.get(_Q2, '')).strip()
    return 2 if val == 'Yes' else -2


def _q3_score(row):
    val = str(row.get(_Q3, '')).strip()
    return 2 if val == 'Yes' else (-2 if val == 'No' else 0)


def _q5_score(row):
    val = str(row.get(_Q5, '')).strip().lower()
    return 2 if val == 'cloud' else (-2 if val in ('on-premise', 'hybrid') else 0)


def _q6_scores(row):
    """
    Q6a and Q6b — Audit & Logging. DCC = 0, OC = ±2 each, scored independently.
    Both Yes → +4 OC total. Either No → that question contributes -2.
    """
    audit   = str(row.get(_Q6A, '')).strip()
    logging = str(row.get(_Q6B, '')).strip()
    return (2 if audit == 'Yes' else -2), (2 if logging == 'Yes' else -2)


def _q7_oc(row):
    val = str(row.get(_Q7, '')).strip()
    return 2 if val == 'Yes' else -2


def _q10_score(row):
    """
    Q10 scoring:
      Yes → min(10a, 10b)            — must have both valid protocol and auth
      No  → max(-2, 10c)             — 0 if alternate interfaces exist, -2 otherwise
      Blank/other → 0
    """
    val = str(row.get(_Q10, '')).strip()
    if val == 'Yes':
        s10a = score_api_protocol(
            row.get('16: REST'), row.get('16: SOAP'),
            row.get('16: AMQP'), row.get('16: Other, please specify'),
        )
        s10b = score_auth(
            row.get('17: SAML'), row.get('17: OAuth'),
            row.get('17: Other, please specify'),
        )
        return min(s10a, s10b)
    if val == 'No':
        s10c = score_10c(row.get('18: No'), row.get('18: No sure'), row.get('18: Yes'))
        return max(-2, s10c)
    return 0


def _q14_scores(row):
    """Returns (q14_score, q14a_score) — mutually exclusive."""
    q14  = str(row.get(_Q14,  '')).strip()
    q14a = str(row.get(_Q14A, '')).strip()
    if q14 == 'Yes':  return 2, 0
    if q14a == 'Yes': return 0, 2
    return 0, 0


def _q16_score(row):
    keys = (
        '26: Yes: PS-CA',
        '26: Yes: Pan-Canadian Health Data Content Framework',
        '26: Yes: CA:FeX ',
    )
    any_yes = any(pd.notna(row.get(k)) and row.get(k) == 1 for k in keys)
    return 2 if any_yes else 0


def score_row(row):
    """
    Score a single survey row.
    Returns (dcc_raw, oc_raw) as integers.
    """
    q2        = _q2_score(row)
    q3        = _q3_score(row)
    q5        = _q5_score(row)
    q6a, q6b  = _q6_scores(row)
    q7        = _q7_oc(row)
    q10       = _q10_score(row)
    q14, q14a = _q14_scores(row)
    q16       = _q16_score(row)

    dcc = q2 + q3 + q5 + 0   + 0   + q10 + q14 + q14a + q16
    oc  = q2 + q3 + q5 + q6a + q6b + q7  + q10 + q14  + q14a + q16
    return dcc, oc


def score_row_breakdown(row):
    """
    Score a single survey row, returning a dict of per-question breakdowns.
    Each entry: score_key → (dcc_raw, oc_raw, signal)
    where signal is 'positive' | 'negative' | 'neutral'.

    Used by the viewer to annotate each question card with its rubric score.
    """
    def _sig(dcc_v, oc_v):
        val = dcc_v if dcc_v is not None else (oc_v or 0)
        if oc_v is not None and dcc_v is not None:
            val = (dcc_v + oc_v) / 2
        return 'positive' if val > 0 else ('negative' if val < 0 else 'neutral')

    q2        = _q2_score(row)
    q3        = _q3_score(row)
    q5        = _q5_score(row)
    q6a, q6b  = _q6_scores(row)
    q7        = _q7_oc(row)
    q10       = _q10_score(row)
    q14, q14a = _q14_scores(row)
    q16       = _q16_score(row)

    return {
        'q2':   (q2,  q2,  _sig(q2,  q2)),
        'q3':   (q3,  q3,  _sig(q3,  q3)),
        'q5':   (q5,  q5,  _sig(q5,  q5)),
        'q6a':  (0,   q6a, _sig(None, q6a)),
        'q6b':  (0,   q6b, _sig(None, q6b)),
        'q6':   (0,   q6a + q6b, _sig(None, q6a + q6b)),
        'q7':   (0,   q7,  _sig(None, q7)),
        'q10':  (q10, q10, _sig(q10, q10)),
        'q14':  (q14,  q14,  _sig(q14,  q14)),
        'q14a': (q14a, q14a, _sig(q14a, q14a)),
        'q16':  (q16, q16, _sig(q16, q16)),
    }


# ─────────────────────────── DATA PIPELINE ───────────────────────────

def deduplicate(df):
    """
    Normalise jurisdiction column and remove duplicate respondents,
    keeping only the most recent submission per (Respondent, Jurisdiction) pair.
    """
    df = df.copy()
    df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
    df[JUR_COL] = df[JUR_COL].fillna(UNKNOWN_JUR)
    df = (df
          .sort_values('Date')
          .drop_duplicates(subset=['Respondent', JUR_COL], keep='last'))
    df['Date'] = df['Date'].dt.strftime('%d/%m/%Y %H:%M:%S').fillna('')
    return df.reset_index(drop=True)


def calculate_scores(df):
    """
    Run the full scoring pipeline over a cleaned survey DataFrame.

    Returns a scores DataFrame with columns:
        Jurisdiction, Short, Respondent,
        Data Connection Complexity, Operational Complexity,
        DCC (normalized), OC (normalized),
        _dcc_norm, _oc_norm,
        Readiness Band, _color_idx
    """
    records = []
    jur_color_idx = {}
    color_counter = [0]

    for _, row in df.iterrows():
        jur = str(row.get(JUR_COL, UNKNOWN_JUR)).strip()
        if jur == UNKNOWN_JUR:
            continue

        dcc_raw, oc_raw = score_row(row)
        dcc_norm = normalize_dcc(dcc_raw)
        oc_norm  = normalize_oc(oc_raw)

        if jur not in jur_color_idx:
            jur_color_idx[jur] = color_counter[0]
            color_counter[0]  += 1

        records.append({
            'Jurisdiction':              jur,
            'Short':                     short(jur),
            'Respondent':                str(row.get('Respondent', '')).strip(),
            'Data Connection Complexity': dcc_raw,
            'Operational Complexity':     oc_raw,
            'DCC (normalized)':          round(dcc_norm, 3),
            'OC (normalized)':           round(oc_norm,  3),
            '_dcc_norm':                 dcc_norm,
            '_oc_norm':                  oc_norm,
            'Readiness Band':            readiness_band(dcc_raw, oc_raw),
            '_color_idx':                jur_color_idx[jur],
        })

    result = pd.DataFrame(records)
    if result.empty:
        return result

    # ── Radial jitter for overlapping bubbles ─────────────────────────
    # Bubbles at identical (dcc_norm, oc_norm) are fanned out in a circle
    # so each label remains readable. A dotted line in chart.py connects
    # the jittered position back to the true position.
    import math
    JITTER_RADIUS = 0.08   # normalised units — small enough to stay in quadrant

    result['_x'] = result['_dcc_norm']
    result['_y'] = result['_oc_norm']

    groups = result.groupby(['_dcc_norm', '_oc_norm'])
    for (cx, cy), idx in groups.groups.items():
        if len(idx) < 2:
            continue
        n = len(idx)
        for i, row_i in enumerate(idx):
            angle = (2 * math.pi * i / n) - (math.pi / 2)   # start at top
            result.at[row_i, '_x'] = cx + JITTER_RADIUS * math.cos(angle)
            result.at[row_i, '_y'] = cy + JITTER_RADIUS * math.sin(angle)

    return result