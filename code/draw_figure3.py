from csv import DictReader
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
from itertools import combinations
from pathlib import Path
import sys

import numpy as np
from PIL import Image
import pymupdf

project, output = map(Path, sys.argv[1:])
original = project / 'code' / 'figures.py'
data = project / 'results' / 'contrasts.csv'
protected = [original, data, *(project / 'figures').glob('Figure3*')]
hashes = {path: sha256(path.read_bytes()).digest() for path in protected}

# Reuse the published plotting code without executing its output commands.
raw = original.read_text(encoding='utf-8')
setup, setup_end, _ = raw.partition("gap=pd.read_csv")
_, fig3_start, remainder = raw.partition("save(fig,'Figure2')")
fig3, fig3_end, _ = remainder.partition("save(fig,'Figure3')")
assert setup_end and fig3_start and fig3_end
namespace = {'__file__': str(original)}
exec(compile(setup + fig3, str(original), 'exec'), namespace)
fig, axes = namespace['fig'], namespace['aa']

with data.open(encoding='utf-8', newline='') as csv:
    by_key = {(row['dimension'], row['subgroup'], row['period']): Decimal(row['gap'])
              for row in DictReader(csv) if row['subgroup'] != 'Unknown'}

def line_geometry(ax):
    return [(tuple(line.get_xdata()), tuple(line.get_ydata()), line.get_color(), line.get_linestyle())
            for line in ax.lines]

def point_geometry(ax):
    return [(collection.get_offsets().copy(), collection.get_facecolors().copy())
            for collection in ax.collections]

before_lines = [line_geometry(ax) for ax in axes]
before_points = [point_geometry(ax) for ax in axes]
before_limits = [(ax.get_xlim(), ax.get_ylim()) for ax in axes]
assert all(x == (-9, 9) for x, _ in before_limits)

fig.set_layout_engine(None)
fig.set_size_inches(180 / 25.4, 88 / 25.4)
fig.set_dpi(180)
for ax, left in zip(axes, (.203, .680)):
    ax.set_position((left, .227, .305, .612))

xlabel = 'Longer-minus-standard coverage gap (pp)'
headings = ('Area disadvantage (ages 16–64 years)', 'Rurality (all ages)')
all_labels = []
for ax, dimension, title, letter in zip(axes, ('SEIFA', 'MMM all ages'), headings, 'AB'):
    start = ax.get_position().x0
    fig.text(start - .030, .952, letter, fontsize=10.6, weight='bold', va='top')
    fig.text(start, .952, title, fontsize=9.0, weight='bold', va='top')
    ax.set_title('', loc='left')
    for artist in tuple(ax.texts):
        artist.remove()

    ax.set_xlabel(xlabel, fontsize=7.65, labelpad=5)
    ax.tick_params(axis='x', labelsize=7.55, length=2.8, pad=3)
    ax.tick_params(axis='y', labelsize=7.15, length=0, pad=5)
    ax.grid(axis='x', color='#DFE3E6', linewidth=.55)
    for line in ax.lines[:-1]:
        line.set_linewidth(.92)
    zero = ax.lines[-1]
    assert list(zero.get_xdata()) == [0, 0] and zero.get_linestyle() == '--'
    zero.set_linewidth(.75)
    for points, size in zip(ax.collections, (21, 24)):
        points.set_sizes([size])

    subgroups = sorted({group for dim, group, _ in by_key if dim == dimension})
    if dimension == 'SEIFA':
        ax.set_yticklabels(['Q1 (most disadvantaged)', 'Q2', 'Q3', 'Q4', 'Q5 (least disadvantaged)'])
    plotted_label_artists = []
    decimals = []
    for y, group in enumerate(subgroups):
        past = by_key[dimension, group, '2025Q2']
        current = by_key[dimension, group, '2026Q2']
        endpoints = [ax.collections[index].get_offsets()[y] for index in range(2)]
        np.testing.assert_allclose(endpoints, [[float(past), y], [float(current), y]], atol=2e-15, rtol=0)
        shown = f'{current.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP):.2f}'.replace('-', '−')
        if group == '3. Large Rural Towns':
            assert shown == '−0.04'
        decimals.append(shown)
        x = endpoints[1][0]
        near_zero = abs(x) < 1
        plotted_label_artists.append(ax.annotate(
            shown, (x, y), xytext=(-3.4 if near_zero else 0, -4.3),
            textcoords='offset points', ha='right' if near_zero else 'center', va='top',
            fontsize=7.15, color=namespace['BLUE'], zorder=6))
    print(f'{letter}: {", ".join(decimals)}')
    all_labels.extend(plotted_label_artists)

axes[0].get_legend().remove()
handles, _ = axes[0].get_legend_handles_labels()
fig.legend(handles, ('April–June 2025', 'April–June 2026'), loc='lower center',
           bbox_to_anchor=(.5, .028), ncol=2, frameon=False, fontsize=8.2,
           handletextpad=.45, columnspacing=2.4)
assert [(ax.get_xlim(), ax.get_ylim()) for ax in axes] == before_limits
for ax, lines, points in zip(axes, before_lines, before_points):
    assert line_geometry(ax) == lines
    for (original_values, original_colours), (new_values, new_colours) in zip(points, point_geometry(ax)):
        np.testing.assert_array_equal(new_values, original_values)
        np.testing.assert_array_equal(new_colours, original_colours)

fig.canvas.draw()
renderer = fig.canvas.get_renderer()
labels = [*fig.texts, *fig.legends, *all_labels]
for ax in axes:
    labels.extend([ax.xaxis.label, *ax.get_yticklabels()])
bounds = [artist.get_window_extent(renderer) for artist in labels]
for artist, bbox in zip(labels, bounds):
    assert fig.bbox.contains(*bbox.p0) and fig.bbox.contains(*bbox.p1), (artist, bbox)
for first, second in combinations(bounds, 2):
    assert not first.overlaps(second), (first, second)

pdf_file = output / 'Figure3_MJA.pdf'
tiff_file = output / 'Figure3_MJA.tiff'
fig.savefig(pdf_file, facecolor='white')
fig.savefig(tiff_file, dpi=600, facecolor='white',
            pil_kwargs={'compression': 'tiff_lzw', 'dpi': (600, 600)})
with Image.open(tiff_file) as tiff:
    assert tiff.format == 'TIFF' and min(tiff.size) >= 2000 and tiff.info['dpi'] == (600., 600.)
    width, height = tiff.size
with pymupdf.open(pdf_file) as pdf:
    assert len(pdf) == 1 and not pdf[0].get_images()
    page = pdf[0]
    for label in (*headings, xlabel, 'Q1 (most disadvantaged)', 'Q5 (least disadvantaged)',
                  'April–June 2025', 'April–June 2026', *(artist.get_text() for artist in all_labels)):
        matches = page.search_for(label)
        assert matches and all(page.rect.contains(match) for match in matches), (label, matches)
    assert len(page.search_for(xlabel)) == 2
    page.get_pixmap(dpi=200, alpha=False).save(output / 'Figure3_MJA_preview.png')

assert hashes == {path: sha256(path.read_bytes()).digest() for path in protected}
print(f'Verified 24 original point coordinates, 12 connector segments, both symmetric axes, '
      f'12 verified annotations, input hashes, vector PDF and {width}x{height} TIFF at 600 dpi.')
