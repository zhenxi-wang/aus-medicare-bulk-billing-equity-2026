from hashlib import sha256
from itertools import combinations
from pathlib import Path
import sys

import numpy as np
from PIL import Image
import pymupdf

project, output = map(Path, sys.argv[1:])
original = project / 'code' / 'figures.py'
data = project / 'results' / 'costs_by_level.csv'
protected = [original, data, *(project / 'figures').glob('Figure2*')]
hashes = {path: sha256(path.read_bytes()).digest() for path in protected}

# Execute the original style and Figure 2 blocks only, without any of their exports.
text = original.read_text(encoding='utf-8')
setup, setup_end, _ = text.partition("gap=pd.read_csv")
_, fig2_start, remainder = text.partition("save(fig,'Figure1')")
fig2, fig2_end, _ = remainder.partition("save(fig,'Figure2')")
assert setup_end and fig2_start and fig2_end
namespace = {'__file__': str(original)}
exec(compile(setup + fig2, str(original), 'exec'), namespace)
fig, axes = namespace['fig'], namespace['aa']
source = namespace['cost']

def bar_geometry(ax):
    return [(bar.get_x(), bar.get_y(), bar.get_width(), bar.get_height(), bar.get_facecolor())
            for container in ax.containers for bar in container]

initial_geometry = [bar_geometry(ax) for ax in axes]
initial_xlim = [ax.get_xlim() for ax in axes]
initial_ylim = [ax.get_ylim() for ax in axes]
initial_categories = [[tick.get_text() for tick in ax.get_xticklabels()] for ax in axes]
initial_labels = [[label.get_text() for label in ax.texts[:8]] for ax in axes]
assert initial_ylim == [(0, 100), (0, 240), (0, 85)]

fig.set_layout_engine(None)
fig.set_size_inches(180 / 25.4, 88 / 25.4)
fig.set_dpi(180)
fig.subplots_adjust(left=.078, right=.989, bottom=.192, top=.827, wspace=.27)
headings = (
    'Bulk-billing coverage',
    'Mean contribution\nwhen patient billed',
    'Mean contribution across\noutpatient services',
)
ylabels = ('Bulk-billing coverage (%)', 'Mean patient contribution (A$)', 'Mean patient contribution (A$)')
periods = ('2025Q2', '2026Q2')
all_value_artists = []
for ax, code, heading, ylabel, metric, prior in zip(
        axes, 'ABC', headings, ylabels, ('rate', 'conditional_gap', 'burden'), initial_labels):
    location = ax.get_position().x0
    ax.set_title('', loc='left')
    fig.text(location - .028, .953, code, weight='bold', fontsize=10.2, ha='left', va='top')
    fig.text(location, .953, heading, weight='bold', fontsize=8.35, linespacing=1.16,
             ha='left', va='top')
    ax.set_ylabel(ylabel, fontsize=8.2, labelpad=3.5)
    ax.tick_params(axis='x', labelsize=6.05, length=2.5, pad=3.1)
    ax.tick_params(axis='y', labelsize=7.25, length=2.5, pad=2.6)
    ax.grid(axis='y', color='#DFE3E6', linewidth=.57)
    for inherited in tuple(ax.texts):
        inherited.remove()

    value_artists = []
    for period, container, offset in zip(periods, ax.containers, (-3.5, 3.5)):
        expected = source[source.period == period].set_index('kind').loc[list('BCDE'), metric]
        np.testing.assert_array_equal([bar.get_height() for bar in container], expected)
        for index, bar in enumerate(container):
            value = f'{bar.get_height():.1f}'
            # Keep first-column text clear of the y-axis and five-character text off its neighbour.
            shift = offset
            if period == '2025Q2':
                shift = -1.0 if index == 0 else (-4.55 if len(value) > 4 else offset)
            label = ax.annotate(value,
                                (bar.get_x() + bar.get_width()/2, bar.get_height()),
                                xytext=(shift, 3.4), textcoords='offset points',
                                ha='center', va='bottom', fontsize=7.05, color='#171C22', zorder=5)
            value_artists.append(label)
    assert [label.get_text() for label in value_artists] == prior
    all_value_artists.append(value_artists)

fig.legends[0].remove()
handles, _ = axes[0].get_legend_handles_labels()
fig.legend(handles, ('April–June 2025', 'April–June 2026'), loc='lower center',
           bbox_to_anchor=(.5, .035), frameon=False, ncol=2, fontsize=8.25,
           handlelength=1.6, columnspacing=2.25)

assert [bar_geometry(ax) for ax in axes] == initial_geometry
assert [ax.get_xlim() for ax in axes] == initial_xlim
assert [ax.get_ylim() for ax in axes] == initial_ylim
assert [[tick.get_text() for tick in ax.get_xticklabels()] for ax in axes] == initial_categories

fig.canvas.draw()
renderer = fig.canvas.get_renderer()
for artist in (*fig.texts, *fig.legends, *(a.yaxis.label for a in axes)):
    bbox = artist.get_window_extent(renderer)
    assert fig.bbox.contains(*bbox.p0) and fig.bbox.contains(*bbox.p1), (artist, bbox)
for ax, labels in zip(axes, all_value_artists):
    for artists in (labels, ax.get_xticklabels()):
        bboxes = [artist.get_window_extent(renderer) for artist in artists]
        for bbox in bboxes:
            assert fig.bbox.contains(*bbox.p0) and fig.bbox.contains(*bbox.p1), bbox
        for first, second in combinations(bboxes, 2):
            assert not first.overlaps(second), (first, second)

pdf_file = output / 'Figure2_MJA.pdf'
tiff_file = output / 'Figure2_MJA.tiff'
fig.savefig(pdf_file, facecolor='white')
fig.savefig(tiff_file, dpi=600, facecolor='white',
            pil_kwargs={'compression': 'tiff_lzw', 'dpi': (600, 600)})
with Image.open(tiff_file) as tiff:
    assert tiff.format == 'TIFF' and min(tiff.size) >= 2000 and tiff.info['dpi'] == (600., 600.)
    width, height = tiff.size

with pymupdf.open(pdf_file) as pdf:
    assert len(pdf) == 1 and not pdf[0].get_images()
    page = pdf[0]
    rendered_text = ' '.join(page.get_text().split())
    for label in (*headings, *ylabels, 'April–June 2025', 'April–June 2026', '64.4', '64.3'):
        assert ' '.join(label.split()) in rendered_text, (label, rendered_text)
    for label in ['64.4', '64.3']:
        blocks = page.search_for(label)
        assert len(blocks) == 1 and page.rect.contains(blocks[0])
    assert page.search_for('64.4')[0].x1 + 1 <= page.search_for('64.3')[0].x0
    page.get_pixmap(dpi=200, alpha=False).save(output / 'Figure2_MJA_preview.png')

assert hashes == {path: sha256(path.read_bytes()).digest() for path in protected}
print(f'Verified all 24 bar heights, positions, colours, labels and axis ranges, original hashes, vector PDF and {width}x{height} TIFF at 600 dpi.')
