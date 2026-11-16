# Analysis protocol — recorded 12 November 2026

## Question and scope
Did financial protection for longer GP attendances recover to the same extent as standard attendances around Australia's November 2025 universal bulk-billing expansion? Describe duration gradients by age, area disadvantage and rurality, and distinguish billing-code redistribution from clinical activity.

Data feasibility inspection has identified official Medicare quarterly files through June 2026 and their variable structure. National overall bulk-billing summaries and the first few total-GP rows were inspected. No duration-specific contrasts or model results have been examined. This is an internally timestamped protocol, not prospective public registration. Universal novelty and significance are not guaranteed.

## Data
Official Department of Health, Disability and Ageing August 2026 release. Primary: SEIFA workbook, July 2021–June 2026, GP attendance category × age × quintile × quarter. Secondary: primary-care service-type workbook (state, Modified Monash); concession workbook for policy context. Do not conflate overlapping aggregates with independent observations.

## Definitions
Standard = Level B; longer = sum of Levels C, D and E (E zero before introduction). Main population ages 16–64, national aggregate. Financial protection = bulk-billed services / all services. Duration gap = longer minus standard, percentage points (negative means lower coverage for longer). Financial burden = published average out-of-hospital patient contribution across all services; conditional gap is separately reported. Do not derive the out-of-hospital burden by multiplying all-setting bulk-billing rates and conditional gap fees. All prices are nominal Australian dollars.

## Primary analysis
1. Report exact administrative counts, rates and duration gaps in April–June 2025 and April–June 2026, plus their year-on-year changes. No binomial uncertainty or tests treating millions of claims as independent samples.
2. Model the national quarterly duration gap for ages 16–64 using OLS: intercept, linear time, quarter-of-year fixed effects, a November 2023 step and post-November-2023 trend, and a post-November-2025 step. Exclude October–December 2023 and October–December 2025 as mixed-exposure quarters. Treat January–March 2024 as the first full 2023-reform quarter and January–March 2026 as first full 2025-reform quarter. Primary inference: Newey–West HAC lag 4, small-sample correction, t reference with residual degrees of freedom. Short follow-up and differential pre-trends prevent a strong causal claim; the post coefficient is an adjusted temporal contrast. No post-2025 slope is fitted with two full quarters.

## Prespecified secondary analyses
- Same duration gap by three age bands, five SEIFA quintiles (national age 16–64) and seven Modified Monash categories (all ages); assess descriptive direction and magnitude. No individual income, disease severity, sex, need or practice-level inference.
- Disaggregate C, D and E to expose duration gradient. Long-service share among B+C+D+E, stratified by bulk-billed vs patient-billed, is a billing mix indicator, not actual consultation time or quality.
- Sensitivity to coding substitution: combine longer consultations plus GP mental health categories and compare with B; describe combined service volumes because dedicated mental health items changed November 2025. Cannot fully identify clinical substitution without person/item linkage.
- Sensitivity models: HAC lags 1 and 2; no 2023 slope; recent period beginning January 2024 with quarter fixed effects, trend and post step; exclude Level E throughout; longer composition held at April–June 2025 C/D/E weights (where estimable); unadjusted same-quarter change. Report all, including null and conflicting results.
- June 2026 versus June 2025 fixed age×quintile standardisation of national B and longer rates; use 2025 B cell volumes as common standard. Exclude unknown SEIFA; report coverage.

## Multiplicity and interpretation
One primary model contrast. Secondary comparisons are descriptive; any secondary P-values are exploratory. Avoid selecting outcome, subgroup, window or covariance estimator by significance. State that aggregate data cannot measure unmet need, patient-level transitions, actual minutes, clinical outcomes or effects solely attributable to the reform. Audit all sums, missing cells, category definitions and coding changes. Preserve raw files, hashes and reproducible code. Manuscript under 5000 main-text words, verified references, high-resolution figures, full supplement.
