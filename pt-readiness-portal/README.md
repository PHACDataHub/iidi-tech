# PT Readiness Portal

A dashboard for reviewing provincial and territorial (PT) immunization registry readiness survey responses. It scores each jurisdiction's technical complexity and visualizes the results.

**Live at:** https://pt-readiness-portal.federal.iidi.beta.phac.gc.ca/

---

## What it does

Upload a survey export (CSV or Excel) and the app gives you three things:

**1. Survey Response Viewer**
Select a jurisdiction from the dropdown to browse their full survey response. Questions are grouped into labelled sections (e.g. _Q5 – Hosting_, _Q9 – API & Data Exchange_) and checkbox answers are shown as pills rather than raw 0/1 values. Use the collapsible _Filter question sections_ panel to show only the sections you care about.

**2. Technical Readiness Scores table**
Each jurisdiction is scored on two dimensions — Data Connection Complexity (DCC) and Operational Complexity (OC) — and assigned a readiness band (High / Moderate / Low / Very Low). Scores are colour-coded for quick scanning.

**3. Adoption Complexity Matrix**
A scatter plot with DCC on the x-axis and OC on the y-axis. Each bubble is one jurisdiction, labelled with its province abbreviation. Hover over a bubble to see the full name, exact scores, and respondent. If two jurisdictions land on the same coordinates, they are jittered slightly and connected back to the true point with a dotted line so neither is hidden.

---

## Scoring methodology

Scores are calculated from a subset of the survey questions. The full rubric is documented on SharePoint — **accessible on the HC network with an HC account only:**

> 📄 **Scoring Rubric:** `[SharePoint link here](https://022gc-my.sharepoint.com/:x:/r/personal/william_brierley_hc-sc_gc_ca/Documents/PT%20Readiness%20Measurement%20Methodology.xlsx?d=w8305050ab0914c87a5345d6434fc0063&csf=1&web=1&e=lazo8u)`
>
> 📓 **Additional analysis diagrams and notebooks:** [Colab version to run](https://colab.research.google.com/drive/1ID9StC9CFHDHXyDAd2q8rU92D7EvHp5h?usp=sharing) and [Github hosted version](https://github.com/PHACDataHub/iidi-tech/blob/iidi-cobra/pt-readiness-portal/PT%20Readiness.ipynb)

Brief summary of the scored questions:

| Question | What it measures                       | DCC                                         | OC                                          |
| -------- | -------------------------------------- | ------------------------------------------- | ------------------------------------------- |
| Q2       | Official registry exists               | Yes +2 / No −2                              | Yes +2 / No −2                              |
| Q3       | Panorama implementation                | Yes +2 / No −2                              | Yes +2 / No −2                              |
| Q5       | Hosting environment                    | Cloud +2 / On-Prem or Hybrid −2             | Cloud +2 / On-Prem or Hybrid −2             |
| Q6       | Audit & activity logging               | always 0                                    | Both Yes +2 / else −2                       |
| Q7       | Backup & disaster recovery             | always 0                                    | Yes +2 / No −2                              |
| Q10      | External APIs                          | No −2 / Yes → min(protocol, auth, fallback) | No −2 / Yes → min(protocol, auth, fallback) |
| Q15/15a  | Upgrading components                   | Yes +2 / No 0; 15a Yes +2 / No 0            | Yes +2 / No 0; 15a Yes +2 / No 0            |
| Q16      | Interoperability roadmap participation | Any Yes +2 / else 0                         | Any Yes +2 / else                           |

Q10 is scored as the minimum of three sub-scores: protocol (REST/SOAP/AMQP → +2, Other → −2), authentication method (SAML/OAuth/AMQP → +2, Other → −2), and whether other data exchange interfaces exist (Yes → +2, No/Not sure → −2).

All other questions contribute 0 to both dimensions.

---

## Deduplication logic

- If the **same person** submits twice for the same jurisdiction, only their **latest submission** is kept.
- If **two different people** submit for the same jurisdiction, both responses are kept and shown side-by-side in the viewer. Both responses are also scored separately and appear as separate rows in the table and bubbles in the chart.
- Rows with **no jurisdiction filled in** are shown in the viewer under \_"No Jurisdiction".

---

## Adding a new chart or table

All visualizations live in `app.py`. The general pattern is:

**Step 1 — Write a builder function** that takes the `scores` DataFrame and returns a Plotly figure or a Dash HTML component:

```python
def create_my_new_chart(scores):
    fig = go.Figure()
    # ... build your figure using scores columns:
    # 'Jurisdiction', 'Data Connection Complexity', 'Operational Complexity', 'Readiness Band'
    fig.update_layout(...)
    return fig
```

**Step 2 — Add it to the layout** in `app.layout`, after the existing chart:

```python
html.Hr(),
html.H3("My New Chart", style={'color': BLUE, 'textAlign': 'center', ...}),
dcc.Graph(id='my-new-chart', figure=create_my_new_chart(initial_scores)),
```

**Step 3 — Wire it to the upload callback** so it updates when a new file is uploaded. In `on_upload()`, add it to the `Output` list and return value:

```python
@app.callback(
    ...
    Output('my-new-chart', 'figure'),   # add this
    Input('upload-data', 'contents'),
    ...
)
def on_upload(contents, filename):
    ...
    return (
        ...,
        create_my_new_chart(scores),    # add this at the matching position
    )
```

For a **table** instead of a chart, use `dash_table.DataTable` with `id='my-new-table'` in the layout and `Output('my-new-table', 'data')` in the callback, returning `scores[your_cols].to_dict('records')`.

---

## Running locally

```bash
pip install -r requirements.txt
python app.py
# → http://localhost:8050
```

Set `SURVEY_CSV` to auto-load a file on startup without uploading:

```bash
SURVEY_CSV=/path/to/responses.xlsx python app.py
```

**`requirements.txt`**

```
pandas==2.2.2
numpy==1.26.4
dash==2.17.1
plotly==5.22.0
openpyxl==3.1.2
```

---

## File structure

```
app.py              # entire application — scoring, layout, callbacks
requirements.txt    # Python dependencies
Dockerfile          # builds the container (exposes port 8050)
```
