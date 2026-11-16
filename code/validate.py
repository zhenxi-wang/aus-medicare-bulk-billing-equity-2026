"""Independent mathematical and source-margin reconciliation of the final analysis."""
from pathlib import Path
import json,hashlib
import numpy as np
import pandas as pd
from statsmodels.stats.sandwich_covariance import S_hac_simple
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'results'
checks=[]
for a in json.loads((ROOT/'data/download_manifest.json').read_text()):
 if a['file'] not in {'seifa.xlsx', 'primary.xlsx'}: continue
 p=ROOT/'data'/a['file'];assert hashlib.sha256(p.read_bytes()).hexdigest()==a['sha256']
checks.append('Both analysis-workbook SHA-256 digests verified.')
d=pd.read_csv(R/'model_diagnostics.csv');q=pd.PeriodIndex(d.period,freq='Q')
X=np.column_stack([np.ones(len(d)),d.t,*[(q.quarter==k).astype(float) for k in [2,3,4]],(d.t>=10).astype(float),np.maximum(d.t-10,0),(d.t>=18).astype(float)])
b=np.linalg.lstsq(X,d.gap,rcond=None)[0];residual=d.gap-X@b
score=np.zeros((20,8));score[d.t.astype(int)]=X*residual.to_numpy()[:,None]
bread=np.linalg.inv(X.T@X);cov=bread@S_hac_simple(score,nlags=4)@bread*18/10
se=np.sqrt(np.diag(cov));reported=pd.read_csv(R/'model_coefficients.csv')
assert np.allclose(b,reported.estimate,atol=1e-10)
assert np.allclose(se,reported.se,atol=1e-9)
checks.append('Independent numpy least-squares coefficients and statsmodels complete-grid HAC agree for all eight coefficients and SEs to 1e-9.')
s=pd.read_csv(R/'seifa_clean.csv');state=pd.read_csv(R/'state_clean.csv')
x=s[(s.age=='All Age Groups')&(s.seifa=='Australia')&s.kind.isin(['B','C','D','E'])].merge(state[(state.state=='Australia')&state.kind.isin(['B','C','D','E'])],on=['period','kind'],suffixes=('_seifa','_state'))
assert len(x)==71
assert (x.n_seifa==x.n_state).all() and (x.bb_seifa==x.bb_state).all()
checks.append('National State and SEIFA workbook counts and bulk-billed counts agree exactly in all 71 overlapping level-quarters.')
a=s[(s.seifa=='Australia')&s.kind.isin(['B','C','D','E'])]
g=a[a.age!='All Age Groups'].groupby(['period','kind'])[['n','bb']].sum();tot=a[a.age=='All Age Groups'].set_index(['period','kind'])[['n','bb']]
assert np.allclose(g,tot.reindex(g.index))
checks.append('Age margins reconcile exactly with national totals.')
for p in ['2025Q2','2026Q2']:
 for k in ['B','C','D','E']:
  a=s[(s.period==p)&(s.age=='16 to 64')&(s.kind==k)]
  assert a[a.seifa!='Australia'].n.sum()==a[a.seifa=='Australia'].n.sum()
checks.append('Five quintiles plus unassigned SEIFA reconcile with national counts for all final-period levels.')

# Reconstruct revision outputs independently from primary regression rows and source counts.
projection = pd.read_csv(R/'pretrend_projections.csv').set_index('period')
pre = d.t < 17
historical = np.linalg.lstsq(X[pre, :-1], d.loc[pre, 'gap'], rcond=None)[0]
post_periods = d.loc[~pre, 'period']
predicted = X[~pre, :-1] @ historical
assert np.allclose(projection.loc[post_periods, 'mean'], predicted)
deviations = d.loc[~pre, 'gap'].to_numpy() - predicted
assert np.allclose(projection.loc[post_periods, 'observed_minus_projection'], deviations)
case_models = pd.read_csv(R/'revision_model_comparisons.csv').tail(2)
assert np.allclose(case_models.estimate, deviations)
checks.append('Independent historical projections and single-quarter estimates reconcile with the observed post-quarter deviations.')

june = ['2025Q2', '2026Q2']
adult = s[(s.age == '16 to 64') & s.kind.isin(['B', 'C', 'D', 'E']) & s.period.isin(june)]
national = adult[adult.seifa == 'Australia'].set_index(['period', 'kind'])
pooled = national.loc[(slice(None), ['C', 'D', 'E']), :].groupby('period')[['n', 'bb']].sum()
pooled_coverage = 100 * pooled.bb / pooled.n
decomposition = pd.read_csv(R/'level_mix_decomposition.csv')
assert np.isclose(decomposition.total_pp.sum(), pooled_coverage.diff().iloc[-1])
assert np.allclose(decomposition.within_level_pp + decomposition.service_mix_pp, decomposition.total_pp)
assert np.isclose(decomposition.weight_2025.sum(), 1) and np.isclose(decomposition.weight_2026.sum(), 1)
checks.append('Length-tier decomposition exactly reconciles to the observed C/D/E coverage change before rounding.')

cells = adult[~adult.seifa.isin(['Australia', 'No SEIFA Score'])].copy()
cells['category'] = cells.kind.map({'B':'Standard', 'C':'Longer', 'D':'Longer', 'E':'Longer'})
cells = cells.groupby(['period', 'category', 'seifa'])[['n', 'bb']].sum()
baseline = cells.loc[('2025Q2', 'Standard'), 'n']
adult_standardised = pd.read_csv(R/'adult_seifa_standardized.csv')
assert len(baseline) == 5 and len(adult_standardised) == 4
for row in adult_standardised.itertuples():
 a = cells.loc[(row.period, row.category)]
 assert np.isclose(np.average(100*a.bb/a.n, weights=baseline.reindex(a.index)), row.rate)
checks.append('Five-quintile age-16–64 standardisation independently reconstructed from the source-count extract.')

scenarios = pd.read_csv(R/'mental_health_recoding_scenarios.csv')
assert len(scenarios) == 12
observed = pooled.loc['2026Q2']
assert np.allclose(scenarios.remaining_coverage_pct/100 * (observed.n-scenarios.services_removed),
                   observed.bb-scenarios.assumed_bulk_bill_probability*scenarios.services_removed)
assert np.allclose(scenarios.loc[scenarios.services_removed == 0, 'remaining_coverage_pct'], pooled_coverage.iloc[-1])
checks.append('Scenario numerators, denominators and zero-removal coverage reconcile to exact counts.')

(R/'validation_report.json').write_text(json.dumps({'status':'PASS','checks':checks},indent=2))
print('\n'.join(checks))
