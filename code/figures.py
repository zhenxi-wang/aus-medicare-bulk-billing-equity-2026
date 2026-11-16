"""Publication figures: exact administrative summaries and quarter-level models."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
from PIL import Image

ROOT=Path(__file__).resolve().parents[1];R=ROOT/'results';F=ROOT/'figures'
F.mkdir(exist_ok=True)
BLUE='#123D6A';TEAL='#238A8D';OLD='#A7BED2';GRAY='#929AA1';LIGHT='#E8EDF1';ORANGE='#BA7850'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.titlesize':12,'axes.titleweight':'bold','axes.labelsize':11,'axes.spines.top':False,'axes.spines.right':False,'axes.edgecolor':'#4C5358','axes.linewidth':.8,'xtick.color':'#42484D','ytick.color':'#42484D','pdf.fonttype':42,'ps.fonttype':42,'savefig.facecolor':'white'})
def clean(a,grid=True):
 if grid:a.grid(axis='y',color='#DFE3E6',lw=.65);a.set_axisbelow(True)
 a.tick_params(length=3,width=.7)
def title(a,letter,text):
 a.set_title(text,loc='left',pad=15);a.text(-.14,1.045,letter,transform=a.transAxes,fontsize=16,fontweight='bold',va='bottom')
def save(f,name):
 f.savefig(F/(name+'.png'),dpi=600,bbox_inches='tight',pad_inches=.12)
 f.savefig(F/(name+'.pdf'),bbox_inches='tight',pad_inches=.12)
 f.savefig(F/(name+'.svg'),bbox_inches='tight',pad_inches=.12)
 f.savefig(F/(name+'_preview.png'),dpi=120,bbox_inches='tight',pad_inches=.12)
 with Image.open(F/(name+'.png')) as im:im.save(F/(name+'.tiff'),compression='tiff_lzw',dpi=(600,600))
 plt.close(f)

gap=pd.read_csv(R/'main_gap.csv'); x=np.arange(len(gap));diag=pd.read_csv(R/'model_diagnostics.csv')
fig,aa=plt.subplots(1,2,figsize=(11.8,4.5),gridspec_kw={'width_ratios':[1.13,1]},layout='constrained')
a=aa[0]
for col,color,label in [('Standard',BLUE,'Standard (B)'),('Longer',TEAL,'Longer (C/D/E)')]:a.plot(x,gap[col],color=color,lw=2.4,label=label,marker='o',ms=3)
a.axvspan(17-.45,19.4,color=LIGHT,zorder=0);a.axvline(17-1/6,color=GRAY,ls='--',lw=1)
a.set_ylim(59,86);a.set_ylabel('Bulk-billed services (%)');a.set_xticks([0,4,8,12,16,19],['2021 Q3','2022 Q3','2023 Q3','2024 Q3','2025 Q3','2026 Q2'],rotation=30,ha='right');a.legend(frameon=False,loc='upper right',fontsize=9)
a.text(17.1,60,'Expansion',fontsize=8,color='#626A72',rotation=90);title(a,'A','Bulk-billing coverage');clean(a)
a=aa[1];a.plot(x,gap.gap,color=BLUE,lw=2.2,marker='o',ms=3.5)
post=diag[diag.t>=18];a.plot(post.t,post.no_step_projection,color=GRAY,lw=1.7,ls='--',label='Model with 2025 step set to zero')
a.axhline(0,color=GRAY,lw=1,ls=':');a.axvspan(16.55,19.4,color=LIGHT,zorder=0);a.set_ylim(-4.5,.5)
a.set_xticks([0,4,8,12,16,19],['2021 Q3','2022 Q3','2023 Q3','2024 Q3','2025 Q3','2026 Q2'],rotation=30,ha='right')
a.set_ylabel('Longer minus standard coverage (pp)');a.text(9.7,-4.05,'Adjusted change: −2.04 pp\n95% CI −2.40 to −1.68',fontsize=10,color=BLUE);a.legend(frameon=False,loc='upper left',fontsize=8.5)
title(a,'B','Coverage gap by billing category');clean(a)
save(fig,'Figure1')

cost=pd.read_csv(R/'costs_by_level.csv');cost=cost[cost.age=='16 to 64'];ks=['B','C','D','E'];labs=['B\nStandard','C\nLong','D\nProlonged','E\nExtended']
fig,aa=plt.subplots(1,3,figsize=(12.4,4.7),layout='constrained')
for a,metric,heading,ylab,lim in zip(aa,['rate','conditional_gap','burden'],['Bulk billing by level','Cost when patient billed','Cost across all outpatient services'],['Bulk-billed services (%)','Average contribution (A$)','Average contribution (A$)'],[100,240,85]):
 for j,(p,color) in enumerate([('2025Q2',OLD),('2026Q2',BLUE)]):
  v=cost[cost.period==p].set_index('kind').loc[ks,metric];pos=np.arange(4)+(j-.5)*.35
  a.bar(pos,v,.33,color=color,label='Apr–Jun '+p[:4],zorder=3)
  for xx,vv in zip(pos,v):a.text(xx,vv+lim*.018,f'{vv:.1f}',ha='center',va='bottom',fontsize=8.4,rotation=0)
 a.set_xticks(np.arange(4),labs);a.set_ylim(0,lim);a.set_ylabel(ylab);clean(a)
 title(a,'ABC'[list(aa).index(a)],heading)
handles,labels=aa[0].get_legend_handles_labels()
fig.legend(handles,labels,frameon=False,fontsize=10,loc='lower center',ncol=2,bbox_to_anchor=(.5,-.065))
save(fig,'Figure2')

c=pd.read_csv(R/'contrasts.csv');fig,aa=plt.subplots(1,2,figsize=(12.2,5),layout='constrained',gridspec_kw={'width_ratios':[1,1.18]})
for a,dim,labels,heading in [(aa[0],'SEIFA',['Q1 Most disadvantaged','Q2','Q3','Q4','Q5 Least disadvantaged'],'Area disadvantage, ages 16–64'),(aa[1],'MMM all ages',['Metropolitan','Regional centres','Large rural towns','Medium rural towns','Small rural towns','Remote','Very remote'],'Rurality, all ages')]:
 v=c[(c.dimension==dim)&(c.subgroup!='Unknown')].pivot(index='subgroup',columns='period',values='gap').sort_index();y=np.arange(len(v))
 for yi,(_,r) in zip(y,v.iterrows()):a.plot([r['2025Q2'],r['2026Q2']],[yi,yi],color='#BCC6CE',lw=1.5)
 a.scatter(v['2025Q2'],y,color=OLD,s=49,zorder=3,label='Apr–Jun 2025');a.scatter(v['2026Q2'],y,color=BLUE,s=58,zorder=4,label='Apr–Jun 2026')
 for yi,vv in zip(y,v['2026Q2']):a.annotate(f'{0 if abs(vv)<.05 else vv:.1f}',(vv,yi),xytext=(-8,-14),textcoords='offset points',ha='center',color=BLUE,fontsize=9)
 a.set_yticks(y,labels);a.invert_yaxis();a.set_ylim(len(v)-.25,-.5);a.axvline(0,color=GRAY,lw=1,ls='--');a.set_xlim(-9,9);a.xaxis.set_major_locator(MultipleLocator(3));a.grid(axis='x',color='#DFE3E6',lw=.65);a.set_axisbelow(True);a.set_xlabel('Longer minus standard coverage (pp)');a.spines['left'].set_visible(False);a.tick_params(axis='y',length=0,pad=8)
 title(a,'A' if dim=='SEIFA' else 'B',heading)
aa[0].legend(frameon=False,fontsize=9,loc='lower right')
save(fig,'Figure3')

mix=pd.read_csv(R/'billing_mix.csv');n=mix[mix.payer=='n'].copy();t=np.arange(len(n))
fig,aa=plt.subplots(1,2,figsize=(11.7,4.5),layout='constrained')
a=aa[0]
for k,color,label in [('longer',TEAL,'Longer C/D/E'),('mental_health',ORANGE,'Dedicated GP mental health'),('combined_long_mh',BLUE,'Longer + GP mental health')]:
 v=n[k]/n.loc[n.period=='2025Q2',k].iloc[0]*100;a.plot(t,v,color=color,lw=2,label=label)
a.axvspan(16.55,19.4,color=LIGHT,zorder=0);a.axhline(100,lw=.7,color=GRAY,ls=':');a.set_ylabel('Service count index (2025 Q2 = 100)');a.set_xticks([0,4,8,12,16,19],['2021 Q3','2022 Q3','2023 Q3','2024 Q3','2025 Q3','2026 Q2'],rotation=30,ha='right');a.legend(frameon=False,fontsize=8.7);clean(a);title(a,'A','Interpret growth alongside recoding')
a=aa[1]
for payer,color,label in [('bb',TEAL,'Bulk billed'),('pb',BLUE,'Patient billed')]:
 v=mix[mix.payer==payer];a.plot(t,v.long_share,color=color,lw=2,label=label)
a.axvspan(16.55,19.4,color=LIGHT,zorder=0);a.set_ylabel('Longer share of B/C/D/E services (%)');a.set_xticks([0,4,8,12,16,19],['2021 Q3','2022 Q3','2023 Q3','2024 Q3','2025 Q3','2026 Q2'],rotation=30,ha='right');a.legend(frameon=False,fontsize=9,loc='upper left');clean(a);title(a,'B','Billing mix differs by payment status')
save(fig,'FigureS1')

m=pd.read_csv(R/'sensitivity_models.csv');fig,a=plt.subplots(figsize=(10.8,4.8));fig.subplots_adjust(left=.40,right=.81,bottom=.18,top=.9)
y=np.arange(len(m));a.axvline(0,color=GRAY,ls='--',lw=1)
for i,r in m.iterrows():
 color=BLUE if i==0 else TEAL;a.errorbar(r.estimate,i,xerr=[[r.estimate-r.lower],[r.upper-r.estimate]],fmt='o',ms=7,color=color,lw=2,capsize=0)
 a.text(1.03,i,f'{r.estimate:.2f} ({r.lower:.2f} to {r.upper:.2f})',transform=a.get_yaxis_transform(),va='center',fontsize=9,color='#42484D',clip_on=False)
labs=['Primary: HAC lag 4','HAC lag 1','HAC lag 2','Without 2023 slope change','January 2024 onward','C/D only (exclude E)','C/D/E + GP mental health¹','Fixed C/D/E mix, recent window']
a.set_yticks(y,labs);a.invert_yaxis();a.set_xlabel('Adjusted post-2025 change in coverage gap (pp)');a.set_xlim(-4.7,.2);a.grid(axis='x',color='#DFE3E6',lw=.7);a.set_axisbelow(True);a.spines['left'].set_visible(False);a.tick_params(axis='y',length=0,pad=10)
a.text(1.03,-.9,'Estimate (95% CI)',transform=a.get_yaxis_transform(),fontweight='bold',fontsize=10,clip_on=False)
fig.text(.04,.025,'¹ Expanded service basket; a different estimand. All intervals reflect quarter-level model uncertainty.',fontsize=9,color='#626A72')
save(fig,'FigureS2')
quarter_ticks = [0, 4, 8, 12, 16, 19]
quarter_labels = ['2021 Q3', '2022 Q3', '2023 Q3', '2024 Q3', '2025 Q3', '2026 Q2']
projection = pd.read_csv(R/'pretrend_projections.csv')
pre = projection[projection.t <= 16]
post = projection[projection.t >= 18]
fig, a = plt.subplots(figsize=(10.8, 4.6), layout='constrained')
for omitted in [9, 17]:
    a.axvspan(omitted-.35, omitted+.35, color=LIGHT, zorder=0)
a.plot(gap.t, gap.gap, color=BLUE, lw=1.8, marker='o', ms=4, label='Observed gap')
excluded = gap[gap.t.isin([9, 17])]
a.scatter(excluded.t, excluded.gap, facecolor='white', edgecolor=BLUE, zorder=4, s=42, label='Excluded implementation quarter')
a.plot(pre.t, pre['mean'], color=TEAL, lw=2, label='Historical fit')
extension = pd.concat([pre.tail(1), post])
a.plot(extension.t, extension['mean'], color=TEAL, lw=2, ls='--', label='Historical projection')
a.fill_between(post.t, post.obs_ci_lower, post.obs_ci_upper, color=TEAL, alpha=.18, label='95% prediction interval')
a.vlines(post.t, post.observed, post['mean'], color=ORANGE, lw=1.7, zorder=2)
for row in post.itertuples():
    a.annotate(f'{row.observed_minus_projection:.2f} pp', (row.t, row.observed),
               xytext=(-8, -12), textcoords='offset points', ha='right', color=BLUE, fontsize=9)
a.axhline(0, color=GRAY, lw=.8, ls=':')
a.set_xticks(quarter_ticks, quarter_labels)
a.set_xlim(-.4, 19.7)
a.set_ylim(bottom=min(-4.3, gap.gap.min()-.45))
a.set_ylabel('Longer minus standard coverage (pp)')
a.legend(frameon=False, loc='upper left', ncol=2, fontsize=9)
clean(a)
save(fig, 'FigureS3')

fig, panels = plt.subplots(2, 2, figsize=(11.5, 6.15), layout='constrained')
colors = np.where(diag.t >= 18, ORANGE, BLUE)
a = panels[0, 0]
bounds = [min(diag.gap.min(), diag.fitted.min())-.1, max(diag.gap.max(), diag.fitted.max())+.1]
a.plot(bounds, bounds, color=GRAY, lw=1, ls='--')
a.scatter(diag.fitted, diag.gap, c=colors, s=30, zorder=3)
a.set(xlabel='Fitted gap (pp)', ylabel='Observed gap (pp)', xlim=bounds, ylim=bounds)
a.set_title('A   Observed versus fitted', loc='left')
clean(a)
a = panels[0, 1]
a.axhline(0, color=GRAY, lw=1, ls='--')
a.scatter(diag.t, diag.residual, c=colors, s=31, zorder=3)
a.set(ylabel='Residual (pp)', ylim=(-.75, .75))
a.set_xticks(quarter_ticks, quarter_labels, fontsize=8)
a.set_title('B   Residuals by processing quarter', loc='left')
clean(a)
a = panels[1, 0]
acf = pd.read_csv(R/'calendar_residual_acf.csv')
a.axhline(0, color=GRAY, lw=1, ls='--')
a.vlines(acf.lag, 0, acf.acf, color=TEAL, lw=2)
a.scatter(acf.lag, acf.acf, color=TEAL, s=39, zorder=3)
a.set_xticks(acf.lag, [f'{lag}\n({pairs} pairs)' for lag, pairs in zip(acf.lag, acf.pairs)])
a.set(xlabel='Calendar-quarter lag', ylabel='Residual autocorrelation', ylim=(-.5, .12), xlim=(.5, 4.5))
a.set_title('C   Calendar-lag autocorrelation', loc='left')
clean(a)
a = panels[1, 1]
a.scatter(diag.t-.14, diag.leverage, color=colors, s=29, label='Leverage')
a.scatter(diag.t+.14, diag.cooks_distance, edgecolor=colors, facecolor='white', marker='D', s=26, label='Cook’s distance')
a.set_xticks(quarter_ticks, quarter_labels, fontsize=8)
a.set_ylim(bottom=-.015)
a.legend(frameon=False, loc='best', fontsize=8.3)
a.set_title('D   Influence by processing quarter', loc='left')
clean(a)
save(fig, 'FigureS4')

scenario = pd.read_csv(R/'mental_health_recoding_scenarios.csv')
fig, a = plt.subplots(figsize=(10.5, 4.4), layout='constrained')
for (probability, values), color in zip(scenario.groupby('assumed_bulk_bill_probability'), [BLUE, TEAL, ORANGE]):
    a.plot(values.services_removed, values.remaining_coverage_pct, color=color, lw=2,
           marker='o', ms=5, label=f'{probability:.0%} bulk billed among removed services')
level_b = gap.loc[gap.period == '2026Q2', 'Standard'].iloc[0]
a.axhline(level_b, color=GRAY, lw=1.4, ls='--', label=f'Observed Level B coverage ({level_b:.2f}%)')
observed_cde = scenario.loc[scenario.services_removed == 0, 'remaining_coverage_pct'].iloc[0]
a.annotate(f'Observed C/D/E: {observed_cde:.2f}%', (0, observed_cde), xytext=(5, -19),
           textcoords='offset points', fontsize=9.5)
ticks = [0, 100000, 200000, 300000]
a.set_xticks(ticks, [f'{v:,}' for v in ticks])
a.set(xlabel='Hypothetical services removed from Levels C/D/E',
      ylabel='Remaining C/D/E coverage (%)', ylim=(72.3, 77.65))
a.legend(frameon=False, loc='upper left', bbox_to_anchor=(.006, .885), fontsize=9)
clean(a)
save(fig, 'FigureS5')
print('Created 3 main and 5 supplementary figures in PNG, TIFF, PDF and SVG.')
