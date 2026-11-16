# Data provenance

The Australian Government Department of Health, Disability and Ageing released both workbooks on 10 August 2026.

| Local filename | Official release |
| --- | --- |
| `seifa.xlsx` | [SEIFA Summary, June quarter 2025–26](https://www.health.gov.au/resources/publications/medicare-quarterly-statistics-socio-economic-indexes-for-areas-seifa-summary-june-quarter-2025-26) |
| `primary.xlsx` | [Primary Care Service Type Summary, June quarter 2025–26](https://www.health.gov.au/resources/publications/medicare-quarterly-statistics-primary-care-service-type-summary-june-quarter-2025-26) |

`download_manifest.json` records the original URLs, sizes and checksums for these workbooks and contextual references. The original download filenames mention March, while the workbook contents cover April–June 2026. Run `python code/download.py` to retrieve verified inputs. If the publisher replaces a download, place the original frozen copy in this directory under its local filename and rerun the checksum step.

The workbooks remain available from their original publisher under the [Department's copyright terms](https://www.health.gov.au/using-our-websites/copyright). `mbs_mental_health_item_mapping.csv` records the study's manual Better Access item mapping for the November 2025 changes. It is contextual documentation for the scenario analysis and contains no item-level service counts.
