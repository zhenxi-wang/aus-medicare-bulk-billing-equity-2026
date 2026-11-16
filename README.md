# Australian Medicare bulk-billing coverage by attendance level, 2021–2026

This repository reproduces the analysis of bulk-billing coverage for Level B and pooled Levels C/D/E general practice attendances, using national Australian Medicare administrative summaries through April–June 2026. The primary series covers people aged 16–64 years and is indexed by claim-processing quarter. The segmented regression estimates a temporal contrast with 18 quarterly observations and two complete follow-up quarters.

## Reproduce the analysis

Use Python 3.12. Commands from the repository root:

```sh
python -m pip install -r requirements.txt
python code/download.py
python code/extract.py
python code/analyze.py
python code/validate.py
python code/figures.py
python code/draw_figure1.py . figures
python code/draw_figure2.py . figures
python code/draw_figure3.py . figures
```

The first download step fetches two Departmental workbooks or verifies existing copies against the frozen byte counts and SHA-256 checksums. See [data provenance](data/README.md) for source links and saved-copy instructions. Extraction produces the worksheet CSVs and attendance-category definitions locally. The model and figures run offline once the inputs and Python packages are available.

The plotting script generates the reference main and supplementary figures and creates the `figures/` directory. The three `draw_figureN.py` scripts generate the revised main figures as vector PDFs and 600 dpi TIFFs. The statistical validation script independently reconstructs key estimates and checks workbook margins.

## Repository contents

- [code](code/README.md) contains extraction, analysis, validation and plotting scripts.
- [data](data/README.md) records the published input URLs, retrieved versions and mental-health item mapping.
- [results](results/README.md) contains the aggregate numerical outputs and validation report.
- [PROTOCOL.md](PROTOCOL.md) records the internal analysis plan.
- [ANALYSIS_DEVIATIONS.md](ANALYSIS_DEVIATIONS.md) documents clarifications, corrections and post hoc revisions.

The source workbooks contain published aggregate service counts. The coverage measures count attendances. Patient contributions use the Department's distinct out-of-hospital denominators. Results do not identify individual consultations or measure a causal effect of the reforms.
