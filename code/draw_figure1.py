from datetime import date
from hashlib import sha256
from pathlib import Path
import sys

import numpy as np
from matplotlib.lines import Line2D
from PIL import Image
import pymupdf

root, output = (Path(arg) for arg in sys.argv[1:])
original = root / 'code' / 'figures.py'
protected = [
    original, *(root / 'figures').glob('Figure1*'),
    *(root / 'results' / name for name in ('main_gap.csv', 'model_diagnostics.csv', 'model_coefficients.csv')),
]
before = {p: sha256(p.read_bytes()).digest() for p in protected}

# Load the existing figure construction up to its first export, in memory.
source, boundary, _ = original.read_text(encoding='utf-8').partition("save(fig,'Figure1')")
assert boundary
ns = {'__file__': str(original), '__name__': '__main__'}
exec(compile(source, str(original), 'exec'), ns)
fig = ns['fig']
a, b = ns['aa']
gap = ns['gap']
diag = ns['diag']
palette = {key: ns[key] for key in ('BLUE', 'TEAL', 'GRAY', 'LIGHT')}
navy = palette['BLUE']
grey = palette['GRAY']
original_limits = [tuple(ax.get_xlim()) + tuple(ax.get_ylim()) for ax in (a, b)]
standard, longer = a.lines[:2]
observed, reference, zero = b.lines[:3]
observed_lines = [(a, standard, 'Standard'), (a, longer, 'Longer'), (b, observed, 'gap')]
excluded = gap.index[gap.period.isin(['2023Q4', '2025Q4'])].to_numpy()
retained = gap.index[~gap.index.isin(excluded)].to_list()
assert excluded.tolist() == [9, 17]
for ax, line, column in observed_lines:
    np.testing.assert_array_equal(line.get_xdata(), gap.t)
    np.testing.assert_array_equal(line.get_ydata(), gap[column])
    line.set(linewidth=1.6, markersize=3.35, markevery=retained,
             markeredgewidth=.7, zorder=3, solid_capstyle='round')
    ax.plot(gap.t.iloc[excluded], gap[column].iloc[excluded], linestyle='none',
            marker='o', markersize=4.2, markerfacecolor='white',
            markeredgecolor=line.get_color(), markeredgewidth=1.05, zorder=5)
standard.set_label('Standard (Level B)')
longer.set_label('Longer-billed (Levels C/D/E)')

post = diag[diag.t >= 18]
coefficient = ns['pd'].read_csv(root / 'results' / 'model_coefficients.csv').set_index('term').loc['post']
np.testing.assert_array_equal(reference.get_xdata(), post.t)
np.testing.assert_array_equal(reference.get_ydata(), post.no_step_projection)
np.testing.assert_allclose(reference.get_ydata(), post.fitted - coefficient.estimate, rtol=0, atol=1e-13)
reference.set(label='Model-based reference (no 2025 step)', linewidth=1.4, zorder=3)
zero.set(zorder=1, linewidth=.85)

# Use a two-column print width and enough height for a 2000 px minimum at 600 dpi.
fig.set_layout_engine(None)
fig.set_size_inches(180/25.4, 88/25.4)
fig.subplots_adjust(left=.077, right=.989, bottom=.191, top=.885, wspace=.29)
for ax, heading, ylabel in [
    (a, 'Bulk-billing coverage', 'Bulk-billing coverage (%)'),
    (b, 'Longer-minus-standard coverage gap', 'Coverage gap (percentage points)'),
]:
    for artist in tuple(ax.texts):
        artist.remove()
    ax.get_legend().remove()
    ax.set_title(heading, loc='left', fontsize=9, pad=11, fontweight='bold')
    ax.set_ylabel(ylabel, fontsize=8.4, labelpad=5)
    ax.tick_params(axis='both', labelsize=8, pad=3, length=2.8)
    ax.set_axisbelow(True)
    ax.grid(axis='y', color='#DFE3E6', linewidth=.55)

for ax, panel, limits in zip((a, b), 'AB', original_limits):
    ax.set_xlim(limits[:2])
    ax.set_ylim(limits[2:])
    ax.text(-.13, 1.067, panel, transform=ax.transAxes, fontsize=11.5, weight='bold',
            va='baseline', ha='left')

def date_position(year, quarter_center):
    start = date(year, 10, 1)
    end = date(year+1, 1, 1)
    return quarter_center - .5 + (date(year, 11, 1) - start) / (end - start)

# Retain quarter shading and distinguish the 1 November date from the excluded dot.
for ax in (a, b):
    ax.patches[0].remove()
    ax.axvspan(16.5, 19.5, facecolor=palette['LIGHT'], edgecolor='none', zorder=0)
    ax.axvline(date_position(2025, 17), color=grey, lw=.72, ls=(0, (3, 3)), zorder=1.5)
a.lines[2].remove()
a.axvline(date_position(2023, 9), color='#BCC3C9', lw=.62, ls=(0, (2, 3)), zorder=1.5)
a.annotate('Nov 2023\nMBS changes', (date_position(2023, 9), 60), xytext=(-3.5, 0),
           textcoords='offset points', ha='right', va='bottom', fontsize=7.0, color='#525B64')
a.annotate('Nov 2025 reforms', (date_position(2025, 17), 60), xytext=(-3.5, 0),
           textcoords='offset points', ha='right', va='bottom', fontsize=7.0, color='#525B64')

excluded_key = Line2D([], [], color=navy, marker='o', markerfacecolor='white',
                      markeredgewidth=1.05, markersize=4.2, linestyle='none',
                      label='Excluded from regression')
a.legend(handles=[standard, longer, excluded_key], frameon=False, loc='upper right',
         fontsize=7.75, handlelength=2.05, borderaxespad=.57, labelspacing=.55)
b.legend(handles=[reference], frameon=False, loc='upper left', fontsize=7.75,
         handlelength=2.5, borderaxespad=.48)
def pp(number):
    return f'{number:.2f}'.replace('-', '−')

annotation = (f'Adjusted post-2025 contrast: {pp(coefficient.estimate)} pp\n'
              f'Model-based 95% CI: {pp(coefficient.lower)} to {pp(coefficient.upper)}')
b.text(.048, .032, annotation, transform=b.transAxes, color=navy, fontsize=7.35,
       ha='left', va='bottom', linespacing=1.32)

fig.savefig(output / 'Figure1_MJA.pdf', facecolor='white')
fig.savefig(output / 'Figure1_MJA.tiff', dpi=600, facecolor='white',
            pil_kwargs={'compression': 'tiff_lzw', 'dpi': (600, 600)})
with Image.open(output / 'Figure1_MJA.tiff') as img:
    assert img.format == 'TIFF' and min(img.size) >= 2000
    assert img.info['dpi'] == (600.0, 600.0)
    size = img.size

with pymupdf.open(output / 'Figure1_MJA.pdf') as pdf:
    assert len(pdf) == 1 and not pdf[0].get_images()
    page = pdf[0]
    pdf_text = page.get_text()
    expected_labels = ['Bulk-billing coverage (%)', 'Standard (Level B)', 'Longer-billed (Levels C/D/E)',
                       'Longer-minus-standard coverage gap', 'Coverage gap (percentage points)',
                       'Model-based reference (no 2025 step)', 'Adjusted post-2025 contrast: −2.04 pp',
                       'Model-based 95% CI: −2.40 to −1.68', 'Nov 2025 reforms', 'Excluded from regression']
    assert all(label in pdf_text for label in expected_labels), repr(pdf_text)
    for label in expected_labels:
        for rect in page.search_for(label):
            assert page.rect.contains(rect), (label, rect, page.rect)
    page.get_pixmap(dpi=200, alpha=False).save(output / 'Figure1_MJA_preview.png')

assert before == {p: sha256(p.read_bytes()).digest() for p in protected}
print(f'Verified one vector page, {size[0]} × {size[1]} px TIFF at 600 dpi, all plotted values, original axis limits and source-file hashes.')
