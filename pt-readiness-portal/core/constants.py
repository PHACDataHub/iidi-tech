"""
constants.py
────────────
Shared constants used across the PT Readiness Dashboard.
Covers colour tokens, jurisdiction mappings, column metadata,
section ordering, and score prefix maps.
"""

# ─────────────────────────── JURISDICTION ────────────────────────────

JUR_COL     = '2.0: Please indicate which jurisdiction you are representing'
UNKNOWN_JUR = 'No Jurisdiction'

PROVINCE_SHORT = {
    'British Columbia': 'BC', 'Alberta': 'AB', 'Saskatchewan': 'SK',
    'Manitoba': 'MB', 'Ontario': 'ON', 'Quebec': 'QC', 'Québec': 'QC',
    'New Brunswick': 'NB', 'Nova Scotia': 'NS', 'Prince Edward Island': 'PEI',
    'Newfoundland and Labrador': 'NL', 'Northwest Territories': 'NWT',
    'Nunavut': 'NU', 'Yukon': 'YT', UNKNOWN_JUR: 'N/A',
}


def short(name):
    """Return the 2-3 letter abbreviation for a jurisdiction name."""
    return PROVINCE_SHORT.get(str(name).strip(), str(name)[:3].upper())


# ─────────────────────────── COLOUR TOKENS ───────────────────────────

BLUE   = '#1F4E79'
MID    = '#2E75B6'
LIGHT  = '#D6E4F0'
GREEN  = '#375623'
LGREEN = '#D5E8D4'
ORANGE = '#C55A11'
RED    = '#C00000'
GREY   = '#595959'
LGREY  = '#F2F2F2'
WHITE  = '#FFFFFF'

PALETTE = [
    '#1F4E79', '#C55A11', '#375623', '#7030A0', '#1f6b4e',
    '#8B3A3A', '#2E6B8A', '#5C4A1E', '#4A235A', '#1A5276', '#888888',
]

# ─────────────────────────── SCORE RANGES ────────────────────────────
# Raw DCC range: −8 to +14
# Raw OC  range: −14 to +20  (Q6a and Q6b scored independently → wider range)

DCC_MIN, DCC_MAX = -8,  14
OC_MIN,  OC_MAX  = -14, 20

# ─────────────────────────── SECTION ORDER ───────────────────────────

SECTION_ORDER = [
    'Respondent & Jurisdiction',
    'Section 1 — Registry & Infrastructure',
    'Section 2 — Hosting, Security & DR',
    'Section 3 — Citizen Access & APIs',
    'Section 4 — System Integration',
    'Section 5 — Data Quality',
    'Section 6 — Archiving',
    'Part 2 — Governance & Custodianship',
    'Part 2 — Who Administers Immunizations',
    'Part 2 — Care Settings by Immunization Type',
    'Part 2 — Adverse Events & Vaccine Issues',
    'Part 2 — Policies & Agreements',
    'Part 2 — Challenges',
    'Other',
]

# Which sections belong to Part 1 vs Part 2 (used for section header banners)
PART_1_SECTIONS = {
    'Respondent & Jurisdiction',
    'Section 1 — Registry & Infrastructure',
    'Section 2 — Hosting, Security & DR',
    'Section 3 — Citizen Access & APIs',
    'Section 4 — System Integration',
    'Section 5 — Data Quality',
    'Section 6 — Archiving',
}
PART_2_SECTIONS = {
    'Part 2 — Governance & Custodianship',
    'Part 2 — Who Administers Immunizations',
    'Part 2 — Care Settings by Immunization Type',
    'Part 2 — Adverse Events & Vaccine Issues',
    'Part 2 — Policies & Agreements',
    'Part 2 — Challenges',
}

# ─────────────────────────── COLUMN METADATA ─────────────────────────
# Maps question prefix → (section_name, human-readable label)
# Used by assign_section(), get_col_label(), and the viewer.

COL_META = {
    'Respondent': ('Respondent & Jurisdiction', 'Respondent ID'),
    'Date':       ('Respondent & Jurisdiction', 'Submission Date'),
    '1':          ('Respondent & Jurisdiction', 'Name / Email'),
    '2.0':        ('Respondent & Jurisdiction', 'Jurisdiction'),

    '3':    ('Section 1 — Registry & Infrastructure',
             'Q1 — What types of information systems capture immunization data?'),
    '4':    ('Section 1 — Registry & Infrastructure',
             'Q2 — Does your jurisdiction have an official immunization registry/repository?'),
    '5':    ('Section 1 — Registry & Infrastructure',
             'Q3 — Is your registry implemented using Panorama?'),
    '6':    ('Section 1 — Registry & Infrastructure', 'Q3 — Panorama version'),
    '7':    ('Section 1 — Registry & Infrastructure',
             'Q3 — Non-Panorama system name(s) and version(s)'),
    '8.1':  ('Section 1 — Registry & Infrastructure', None),
    '8.2.1':('Section 1 — Registry & Infrastructure', 'Public Health — additional notes'),
    '8.2.2':('Section 1 — Registry & Infrastructure', 'Primary Care — additional notes'),
    '8.2.3':('Section 1 — Registry & Infrastructure', 'Pharmacy — additional notes'),
    '8.2.4':('Section 1 — Registry & Infrastructure', 'Hospital — additional notes'),
    '8.2.5':('Section 1 — Registry & Infrastructure', 'Other — additional notes'),

    '9':    ('Section 2 — Hosting, Security & DR',
             'Q5 — Where is the registry/repository hosted?'),
    '10':   ('Section 2 — Hosting, Security & DR',
             'Q6a — Auditing of logins in place?'),
    '11':   ('Section 2 — Hosting, Security & DR',
             'Q6b — Logging of user activities in place?'),
    '12':   ('Section 2 — Hosting, Security & DR',
             'Q7 — Backups and disaster recovery mechanisms in place?'),

    '13':   ('Section 3 — Citizen Access & APIs',
             'Q8 — Digital tool for citizens to access their immunization records?'),
    '14':   ('Section 3 — Citizen Access & APIs',
             'Q9 — If no, how can citizens access their immunization information?'),
    '15':   ('Section 3 — Citizen Access & APIs',
             'Q10 — Does the registry have externally accessible APIs?'),
    '16':   ('Section 3 — Citizen Access & APIs', 'Q10a — API protocol(s) used'),
    '17':   ('Section 3 — Citizen Access & APIs', 'Q10b — API authentication method(s)'),
    '18':   ('Section 3 — Citizen Access & APIs',
             'Q10c — If no APIs, other data exchange interfaces/protocols supported?'),

    '19':   ('Section 4 — System Integration',
             'Q11a — Which systems report immunization data to the registry?'),
    '20':   ('Section 4 — System Integration', 'Q11b — Reporting mechanism(s)'),
    '21':   ('Section 4 — System Integration', 'Q12 — Data exchange formats/standards used'),
    '22':   ('Section 4 — System Integration',
             'Q13 — Terminology and data exchange standards used'),
    '23':   ('Section 4 — System Integration',
             'Q14 — Immunization data sharing/transfer processes in place'),
    '24':   ('Section 4 — System Integration',
             'Q15 — Currently upgrading or replacing registry components?'),
    '25':   ('Section 4 — System Integration',
             'Q15a — Plans to upgrade or replace registry components in future?'),
    '26':   ('Section 4 — System Integration',
             'Q16 — Participating in Interoperability Roadmap (PS-CA / Pan-Canadian HDCF / CA:FeX)?'),

    '27':   ('Section 5 — Data Quality', 'Q17 — How is registry data quality assessed?'),
    '28':   ('Section 5 — Data Quality',
             'Q18 — How are provider-identified data quality issues remediated?'),
    '29':   ('Section 5 — Data Quality',
             'Q19 — How can patients update or correct their immunization record?'),

    '30':   ('Section 6 — Archiving', 'Q20 — Is immunization data ever archived?'),
    '31':   ('Section 6 — Archiving', 'Q21 — When and how is data archived?'),

    '32':   ('Part 2 — Governance & Custodianship',
             'Q22 — Who is the custodian/business owner of immunization data?'),
    '33.1': ('Part 2 — Who Administers Immunizations', 'Public Health Office'),
    '33.2': ('Part 2 — Who Administers Immunizations', 'Primary Care'),
    '33.3': ('Part 2 — Who Administers Immunizations', 'Community Health Centre'),
    '33.4': ('Part 2 — Who Administers Immunizations', 'School'),
    '33.5': ('Part 2 — Who Administers Immunizations', 'Pharmacy'),
    '33.6': ('Part 2 — Who Administers Immunizations', 'Acute Care Facilities'),
    '33.7': ('Part 2 — Who Administers Immunizations', 'Long Term Care Facilities'),
    '33.8': ('Part 2 — Who Administers Immunizations', 'Other'),
    '34.1': ('Part 2 — Care Settings by Immunization Type', 'Childhood Immunizations'),
    '34.2': ('Part 2 — Care Settings by Immunization Type', 'Flu / COVID Immunizations'),
    '34.3': ('Part 2 — Care Settings by Immunization Type', 'Travel Immunizations'),
    '34.4': ('Part 2 — Care Settings by Immunization Type', 'Adult Immunizations'),
    '34.5': ('Part 2 — Care Settings by Immunization Type', 'Adolescent Immunizations'),
    '34.6': ('Part 2 — Care Settings by Immunization Type', 'High Risk Immunizations'),
    '34.7': ('Part 2 — Care Settings by Immunization Type', 'Post-Exposure Immunizations'),
    '35':   ('Part 2 — Adverse Events & Vaccine Issues',
             'Q25 — How are adverse events recorded and shared with providers?'),
    '36':   ('Part 2 — Adverse Events & Vaccine Issues',
             'Q26 — How are vaccine inventory issues (spoilage, wastage) recorded?'),
    '37':   ('Part 2 — Policies & Agreements',
             'Q27 — Policies, procedures or agreements guiding data sharing'),
    '38':   ('Part 2 — Challenges',
             'Q28 — Clinical / business / technical challenges in sharing immunization data'),
}

# ─────────────────────────── SCORE METADATA ──────────────────────────
# Maps column prefix → which score key it feeds (used by viewer badges)

PREFIX_TO_SCORE_KEY = {
    '4':  'q2',  '5':  'q3',  '9':  'q5',
    '10': 'q6',  '11': 'q6',  '12': 'q7',
    '15': 'q10', '16': 'q10', '17': 'q10', '18': 'q10',
    '24': 'q14', '25': 'q14a', '26': 'q16',
}

SCORE_KEY_LABELS = {
    'q2':   'Registry existence',
    'q3':   'Panorama usage',
    'q5':   'Hosting model',
    'q6':   'Security & logging',
    'q7':   'Backup & DR',
    'q10':  'API readiness',
    'q14':  'Active upgrades',
    'q14a': 'Upgrade plans',
    'q16':  'Interop roadmap',
}