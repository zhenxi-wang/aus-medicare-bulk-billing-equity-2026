"""Analysis of official Medicare aggregates; inferential unit is quarter, not claim."""
from pathlib import Path
import json, re
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.stats.stattools import durbin_watson

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'results'
B='GP NRA-Level-B-Standard'; C='GP NRA-Level-C-Long'; D='GP NRA-Level-D-Prolonged'; E='GP NRA-Level-E-Extended'; M='GP NRA-Mental Health Care'
KINDS={B:'B',C:'C',D:'D',E:'E',M:'MH','Total GP Non-Referred Attendances':'Total'}
def load(file,kind):
 d=pd.read_csv(ROOT/'data'/file,skiprows=4).iloc[:,:17]
 d=d[d.iloc[:,0].astype(str).str.match(r'^20\d\d-\d\d Q')].copy()
 cols=['quarter',('type' if kind=='seifa' else 'state' if kind=='state' else 'mmm'),'age' if kind=='seifa' else 'broad','seifa' if kind=='seifa' else 'type','n','benefit','bb','pb','bb_benefit','pb_benefit','rate_published','conditional_gap','burden','schedule','fee','bb_fee','pb_fee']
 if kind=='mmm':cols=cols[:1]+['mmm','broad','type']+cols[4:]
 d.columns=cols
 for x in cols[4:]:d[x]=pd.to_numeric(d[x],errors='coerce')
 fy=d.quarter.str[:4].astype(int);fq=d.quarter.str.extract(r'Q(\d)')[0].astype(int)
 cy=fy+(fq>=3).astype(int);cq=((fq+1)%4)+1
 d['period']=pd.PeriodIndex.from_fields(year=cy,quarter=cq,freq='Q');d['t']=[x.ordinal-pd.Period('2021Q3').ordinal for x in d.period]
 d['kind']=d.type.map(KINDS);d['rate']=100*d.bb/d.n
 return d

seifa=load('seifa_0.csv','seifa'); state=load('primary_0.csv','state'); mmm=load('primary_1.csv','mmm')
for label,d in [('seifa',seifa),('state',state),('mmm',mmm)]:
 d.to_csv(OUT/(label+'_clean.csv'),index=False)
 assert np.nanmax(abs(d.n-d.bb-d.pb))<.1
 assert np.nanmax(abs(d.rate/100-d.rate_published))<1e-10

def series(d,group=['period','t'],long=['C','D','E']):
 x=d[d.kind.isin(['B']+long)].copy()
 x['category']=np.where(x.kind=='B','Standard','Longer')
 z=x.groupby(group+['category'],observed=True)[['n','bb','pb']].sum().reset_index()
 z['rate']=100*z.bb/z.n
 w=z.pivot(index=group,columns='category',values='rate').reset_index();w['gap']=w.Longer-w.Standard
 return z,w

nat=seifa[(seifa.age=='16 to 64')&(seifa.seifa=='Australia')]
nat_all=seifa[(seifa.age=='All Age Groups')&(seifa.seifa=='Australia')]
z,w=series(nat); z.to_csv(OUT/'main_series.csv',index=False);w.to_csv(OUT/'main_gap.csv',index=False)

def regression_data(w, recent=False, slope=True, include_post=True):
 a=w[~w.period.isin([pd.Period('2023Q4'),pd.Period('2025Q4')])].sort_values('t').copy()
 if recent:a=a[a.period>=pd.Period('2024Q1')]
 X=pd.DataFrame({'const':1.,'t':a.t.astype(float)},index=a.index)
 for q in [2,3,4]:X['q'+str(q)]=(a.period.apply(lambda p:p.quarter)==q).astype(float)
 if not recent:
  X['step2023']=(a.period>=pd.Period('2024Q1')).astype(float)
  if slope:X['trend2023']=np.maximum(a.t-(pd.Period('2024Q1').ordinal-pd.Period('2021Q3').ordinal),0)
 if include_post:X['post']=(a.period>=pd.Period('2026Q1')).astype(float)
 return a, X.loc[:,(X!=0).any(axis=0)]

def fit(w,label,lag=4,recent=False,slope=True):
 a,X=regression_data(w,recent,slope)
 model=sm.OLS(a.gap,X).fit()
 # Calendar-aware Newey-West: excluded implementation quarters remain gaps.
 # Equivalently insert zero score vectors on a complete quarterly grid.
 # Adjacent retained rows must not be mistaken for adjacent calendar quarters.
 xx=X.to_numpy(dtype=float);scores=xx*model.resid.to_numpy()[:,None]
 meat=scores.T@scores;times=a.t.to_numpy();n,k=xx.shape
 for h in range(1,lag+1):
  for i in range(n):
   for j0 in range(i):
    if times[i]-times[j0]==h:
     v=np.outer(scores[i],scores[j0]);meat+=(1-h/(lag+1))*(v+v.T)
 bread=np.linalg.inv(xx.T@xx);cov=bread@meat@bread*n/(n-k)
 se=np.sqrt(np.maximum(np.diag(cov),0));par=model.params.to_numpy()
 crit=stats.t.ppf(.975,n-k);low=par-crit*se;high=par+crit*se;pv=2*stats.t.sf(abs(par/se),n-k)
 j=list(X.columns).index('post');lo,hi=low[j],high[j]
 r=dict(label=label,estimate=float(par[j]),se=float(se[j]),lower=float(lo),upper=float(hi),p=float(pv[j]),n_quarters=n,df=float(n-k),lag=lag,r2=float(model.rsquared))
 if label=='Primary':
  a['fitted']=model.fittedvalues;a['residual']=model.resid;a['no_step_projection']=a.fitted-X.post*model.params['post']
  influence=model.get_influence()
  a['leverage']=influence.hat_matrix_diag
  a['cooks_distance']=influence.cooks_distance[0]
  a.to_csv(OUT/'model_diagnostics.csv',index=False)
  coef=pd.DataFrame({'term':X.columns,'estimate':par,'se':se,'lower':low,'upper':high,'p':pv})
  coef.to_csv(OUT/'model_coefficients.csv',index=False)
  (OUT/'model_summary.txt').write_text('OLS coefficients; calendar-quarter Newey-West covariance, Bartlett lag 4; n/(n-k) correction; t reference df=10\n'+coef.to_string(index=False),encoding='utf8')
 return r

models=[fit(w,'Primary'),fit(w,'HAC lag 1',1),fit(w,'HAC lag 2',2),fit(w,'No 2023 slope',4,slope=False),fit(w,'January 2024 onward',2,recent=True)]
for label,kinds in [('Exclude Level E',['C','D']),('Longer plus GP mental health',['C','D','E','MH'])]:
 _,ww=series(nat,long=kinds);models.append(fit(ww,label));ww.to_csv(OUT/('series_'+label[:6].replace(' ','_')+'.csv'),index=False)

# Hold the C/D/E composition at April-June 2025. Absent E before introduction is not imputed.
base=nat[(nat.period==pd.Period('2025Q2'))&nat.kind.isin(['C','D','E'])].set_index('kind').n
weights=base/base.sum();fixed=[]
for p,a in nat.groupby('period'):
 a=a.set_index('kind')
 if not all(k in a.index for k in weights.index):continue
 fixed.append(dict(period=p,t=a.t.iloc[0],gap=sum(a.loc[k,'rate']*v for k,v in weights.items())-a.loc['B','rate']))
fixed=pd.DataFrame(fixed);fixed.to_csv(OUT/'fixed_duration_mix.csv',index=False)
# Only available since late 2023: fit same recent-window model, explicitly marked.
models.append(fit(fixed,'Fixed C/D/E mix, January 2024 onward',2,recent=True))
pd.DataFrame(models).to_csv(OUT/'sensitivity_models.csv',index=False)

contrasts=[]
def describe(d,label,subgroup):
 zz,ww=series(d)
 for p in ['2025Q2','2026Q2']:
  a=zz[zz.period==pd.Period(p)].set_index('category');v=ww[ww.period==pd.Period(p)].iloc[0]
  contrasts.append(dict(dimension=label,subgroup=subgroup,period=p,standard_n=int(a.loc['Standard','n']),standard_bb=int(a.loc['Standard','bb']),standard_rate=float(v.Standard),longer_n=int(a.loc['Longer','n']),longer_bb=int(a.loc['Longer','bb']),longer_rate=float(v.Longer),gap=float(v.gap)))
describe(nat,'National','16–64 years')
for age in ['Under 16','16 to 64','Over 64','All Age Groups']:
 describe(seifa[(seifa.age==age)&(seifa.seifa=='Australia')],'Age',age)
for q in sorted(seifa.seifa.unique()):
 if q in ['Australia','No SEIFA Score']:continue
 describe(seifa[(seifa.age=='16 to 64')&(seifa.seifa==q)],'SEIFA',q)
for m in sorted(mmm.mmm.unique()):
 if m=='Australia':continue
 describe(mmm[mmm.mmm==m],'MMM all ages',m)
contrasts=pd.DataFrame(contrasts);contrasts.to_csv(OUT/'contrasts.csv',index=False)

# Exact cost metrics remain separate by billing level: outpatient denominators not published for pooled levels.
cost=seifa[(seifa.seifa=='Australia')&seifa.kind.isin(['B','C','D','E'])&seifa.period.isin([pd.Period('2025Q2'),pd.Period('2026Q2')])]
cost[['period','age','kind','n','bb','rate','conditional_gap','burden']].to_csv(OUT/'costs_by_level.csv',index=False)

# Billing mix and coding-change sensitivity, never equated with clinical minutes.
mix=[]
for p,a in nat.groupby('period'):
 a=a.set_index('kind');l=a.loc[a.index.isin(['C','D','E'])]
 b=a.loc['B'];mh=a.loc['MH']
 for payer in ['n','bb','pb']:
  mix.append(dict(period=str(p),payer=payer,standard=float(b[payer]),longer=float(l[payer].sum()),mental_health=float(mh[payer]),long_share=100*l[payer].sum()/(l[payer].sum()+b[payer]),combined_long_mh=float(l[payer].sum()+mh[payer])))
pd.DataFrame(mix).to_csv(OUT/'billing_mix.csv',index=False)

# Common standard population: 2025Q2 Level-B age x known-SEIFA counts.
known=seifa[~seifa.seifa.isin(['Australia','No SEIFA Score']) & (seifa.age!='All Age Groups')]
wt=known[(known.period==pd.Period('2025Q2'))&(known.kind=='B')].set_index(['age','seifa']).n
wt=wt/wt.sum();standardized=[]
for p in [pd.Period('2025Q2'),pd.Period('2026Q2')]:
 for cat,kinds in [('Standard',['B']),('Longer',['C','D','E'])]:
  a=known[(known.period==p)&known.kind.isin(kinds)].groupby(['age','seifa'])[['n','bb']].sum()
  assert set(a.index)==set(wt.index)
  standardized.append(dict(period=str(p),category=cat,rate=float((100*a.bb/a.n*wt).sum())))
pd.DataFrame(standardized).to_csv(OUT/'standardized_rates.csv',index=False)

def revision_diagnostics():
    a, design = regression_data(w, include_post=False)
    is_pre = a.period < pd.Period('2025Q4')
    historical = sm.OLS(a.loc[is_pre, 'gap'], design.loc[is_pre]).fit()
    projection = historical.get_prediction(design).summary_frame()
    projection['period'] = a.period
    projection['t'] = a.t
    projection['observed'] = a.gap
    projection['observed_minus_projection'] = a.gap - projection['mean']
    projection['phase'] = np.where(is_pre, 'Pre-period fit', 'Post-period projection')
    projection.to_csv(OUT/'pretrend_projections.csv', index=False)

    diagnostics = pd.read_csv(OUT/'model_diagnostics.csv')
    residuals = diagnostics.residual.to_numpy()
    times = diagnostics.t.to_numpy()
    energy = np.dot(residuals, residuals)
    distance = times[:, None] - times[None, :]
    cross_products = np.outer(residuals, residuals)
    calendar_acf = []
    for lag in range(1, 5):
        pairs = distance == lag
        calendar_acf.append({'lag': lag, 'pairs': int(pairs.sum()),
                             'acf': cross_products[pairs].sum() / energy})
    pd.DataFrame(calendar_acf).to_csv(OUT/'calendar_residual_acf.csv', index=False)
    # Retained-row DW and Q are descriptive references and cross two gaps.
    serial = {
        'durbin_watson_retained_rows': float(durbin_watson(residuals)),
        'ljung_box_q2_retained_rows': float(acorr_ljungbox(residuals, lags=[2]).lb_stat.iloc[0]),
        'pre_fit_n': int(is_pre.sum()),
        'pre_fit_df': int(historical.df_resid),
    }
    (OUT/'revision_diagnostics.json').write_text(json.dumps(serial, indent=2), encoding='utf8')

    a, design = regression_data(w)
    conventional = sm.OLS(a.gap, design).fit()
    lo, hi = conventional.conf_int().loc['post']
    comparisons = [dict(models[0], label='Primary model, conventional OLS SE',
                        se=conventional.bse.post, lower=lo, upper=hi,
                        p=conventional.pvalues.post, lag=None)]
    comparisons.extend(models[:5])
    for kept, removed in [('2026Q1', '2026Q2'), ('2026Q2', '2026Q1')]:
        comparisons.append(fit(w[w.period != pd.Period(removed)], f'Only {kept} retained'))
    pd.DataFrame(comparisons).to_csv(OUT/'revision_model_comparisons.csv', index=False)

def revision_composition():
    levels = nat[nat.kind.isin(['B', 'C', 'D', 'E'])][['period', 'kind', 'n', 'bb', 'rate']].copy()
    b_rates = levels.loc[levels.kind == 'B'].set_index('period').rate
    levels['gap_vs_B'] = levels.rate - levels.period.map(b_rates)
    levels.to_csv(OUT/'level_specific_series.csv', index=False)
    level_models = [fit(series(nat, long=[level])[1], f'{level} versus B') for level in ['C', 'D']]
    pd.DataFrame(level_models).to_csv(OUT/'level_specific_models.csv', index=False)

    june = [pd.Period('2025Q2'), pd.Period('2026Q2')]
    baseline, followup = [
        levels[(levels.period == p) & levels.kind.isin(['C', 'D', 'E'])].set_index('kind')
        for p in june
    ]
    old_weights = baseline.n / baseline.n.sum()
    new_weights = followup.n / followup.n.sum()
    components = pd.DataFrame({
        'weight_2025': old_weights,
        'weight_2026': new_weights,
        'within_level_pp': old_weights * (followup.rate - baseline.rate),
        'service_mix_pp': (new_weights - old_weights) * followup.rate,
    })
    components['total_pp'] = components.within_level_pp + components.service_mix_pp
    pooled_change = sum(new_weights * followup.rate) - sum(old_weights * baseline.rate)
    assert np.isclose(components.total_pp.sum(), pooled_change)
    components.to_csv(OUT/'level_mix_decomposition.csv')

    adult = known[known.age == '16 to 64']
    by_quintile = adult[(adult.period == june[0]) & (adult.kind == 'B')].set_index('seifa').n
    weights = by_quintile / by_quintile.sum()
    assert len(weights) == 5
    rows = []
    for p in june:
        for category, kinds in [('Standard', ['B']), ('Longer', ['C', 'D', 'E'])]:
            cells = adult[(adult.period == p) & adult.kind.isin(kinds)].groupby('seifa')[['n', 'bb']].sum()
            assert set(cells.index) == set(weights.index)
            national_n = nat[(nat.period == p) & nat.kind.isin(kinds)].n.sum()
            rows.append({'period': p, 'category': category, 'rate': (100 * cells.bb / cells.n * weights).sum(),
                         'assigned_share': cells.n.sum() / national_n})
    weights.rename('weight').to_csv(OUT/'adult_seifa_weights.csv')
    pd.DataFrame(rows).to_csv(OUT/'adult_seifa_standardized.csv', index=False)

    # Hypothetical removal from observed C/D/E only. No transition counts are observed.
    scenarios = []
    followup_rate_b = b_rates.loc[june[1]]
    for removed in [0, 100000, 200000, 300000]:
        for probability in [.50, .65, .80]:
            rate = 100 * (followup.bb.sum() - removed * probability) / (followup.n.sum() - removed)
            scenarios.append({'services_removed': removed, 'assumed_bulk_bill_probability': probability,
                              'remaining_coverage_pct': rate, 'gap_vs_B_pp': rate - followup_rate_b})
    pd.DataFrame(scenarios).to_csv(OUT/'mental_health_recoding_scenarios.csv', index=False)

revision_diagnostics()
revision_composition()

audit={'source_seifa_rows':len(seifa),'source_state_rows':len(state),'source_mmm_rows':len(mmm),'period_min':str(seifa.period.min()),'period_max':str(seifa.period.max()),'primary_model':models[0], 'primary_quarters':len(w),'main_total_BCDE_claims':int(nat[nat.kind.isin(['B','C','D','E'])].n.sum()),'selected_missing_numeric_cells':int(nat[nat.kind.isin(['B','C','D','E'])][['n','bb']].isna().sum().sum())}
# Audit that known SEIFA cells plus unassigned reproduce national level for both final periods.
checks=[]
for p in [pd.Period('2025Q2'),pd.Period('2026Q2')]:
 for k in ['B','C','D','E']:
  a=seifa[(seifa.period==p)&(seifa.kind==k)&(seifa.age=='16 to 64')]
  diff=float(a[a.seifa!='Australia'].n.sum()-a[a.seifa=='Australia'].n.sum());assert abs(diff)<.1
  checks.append({'period':str(p),'kind':k,'quintile_sum_difference':diff})
audit['quintile_sum_checks']=checks
(OUT/'audit.json').write_text(json.dumps(audit,indent=2),encoding='utf8')
print(json.dumps(audit,indent=2));print(contrasts[contrasts.dimension=='National'].to_string(index=False));print(pd.DataFrame(models).to_string(index=False))
