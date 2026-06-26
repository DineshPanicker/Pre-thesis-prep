#!/usr/bin/env python3
"""Plot a cyclictest histogram.

Reads the --histfile output produced by `cyclictest --histfile=...`.
Format (cyclictest writes this): one line per latency bucket, where each line
contains the latency-in-microseconds followed by one count column per CPU
that cyclictest measured.  Lines starting with '#' are headers; lines starting
with a non-digit are summary stats (Min/Max/Avg) that we skip here.

Usage:  python3 plot_histogram.py cyclictest-loaded-1h.hist [output.png]
"""

import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker


def parse_histfile(path):
    """Read a cyclictest .hist file.

    Returns:
        latencies: 1D numpy array of latency values in microseconds.
        counts:    2D numpy array, shape (n_latencies, n_cpus). Each row is
                   the per-CPU sample count at that latency bucket.

    The file format is whitespace-separated text:

        # cyclictest header lines start with '#'
        0      12     8      11     ...
        1      45     38     42     ...
        ...
        # Min Latencies: 00001 00001 00001 ...
        # Avg Latencies: 00007 00006 00007 ...
        # Max Latencies: 00143 00128 00139 ...

    We only keep the data rows (lines whose first token is a digit).
    """
    latencies = []
    counts = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            # Skip blanks and comment/summary lines
            if not line or not line[0].isdigit():
                continue
            parts = line.split()
            if len(parts) < 2:
                # Defensive: shouldn't happen, but a single column means no
                # per-CPU data, which is useless for us.
                continue
            try:
                latencies.append(int(parts[0]))
                # Everything after the first column is per-CPU counts.
                counts.append([int(x) for x in parts[1:]])
            except ValueError:
                # Skip any line that doesn't parse as ints — defensive.
                continue
    return np.array(latencies), np.array(counts)


def percentile_from_histogram(latencies, counts_summed, pct):
    """Compute the latency at the given percentile of all samples.

    A histogram gives us total_count samples binned by latency. To find the
    Nth percentile, we compute the cumulative count and find the smallest
    latency whose cumulative count exceeds (pct/100) * total_count.

    This is exact for the bin granularity of cyclictest (1 µs by default).
    """
    total = counts_summed.sum()
    if total == 0:
        return None
    target = total * pct / 100.0
    cumulative = np.cumsum(counts_summed)
    idx = np.searchsorted(cumulative, target)
    if idx >= len(latencies):
        return latencies[-1]
    return latencies[idx]


def main():
    if len(sys.argv) < 2:
        sys.exit("Usage: plot_histogram.py <cyclictest.hist> [output.png]")

    histpath = Path(sys.argv[1])
    if len(sys.argv) > 2:
        outpath = Path(sys.argv[2])
    else:
        # Default: same name, .png extension. Side-by-side with the .hist file.
        outpath = histpath.with_suffix('.png')

    latencies, counts = parse_histfile(histpath)
    if len(latencies) == 0:
        sys.exit("No data rows in histogram file. Was --histfile= used?")

    # Sum across CPUs to get one count per latency bucket. We could plot
    # per-CPU traces instead, but for a 1-hour run on 12 cores the cumulative
    # view is more readable and tells the same story.
    counts_summed = counts.sum(axis=1)
    total_samples = counts_summed.sum()
    n_cpus = counts.shape[1]

    # Compute the summary statistics that actually matter for RT systems.
    # The MAX is what determines hard-real-time worst case. The p99.9 is
    # what determines firm-real-time behaviour. The median is roughly
    # what the system spends most of its time doing.
    p50   = percentile_from_histogram(latencies, counts_summed, 50)
    p99   = percentile_from_histogram(latencies, counts_summed, 99)
    p999  = percentile_from_histogram(latencies, counts_summed, 99.9)
    p9999 = percentile_from_histogram(latencies, counts_summed, 99.99)
    max_seen = latencies[counts_summed > 0].max()
    min_seen = latencies[counts_summed > 0].min()

    # Build the figure. 10x6 inches at 120 dpi gives a sharp PNG at typical
    # screen resolutions, and it prints cleanly on A4 with margins.
    fig, ax = plt.subplots(figsize=(10, 6))

    # Bar chart of count vs latency. width=1.0 so adjacent bars touch (no
    # gaps), which is the conventional histogram look.
    ax.bar(latencies, counts_summed, width=1.0,
           color='#1a4480', alpha=0.85, edgecolor='none')

    # Log scale on Y is essential here. Most samples cluster near the median;
    # the interesting tail has counts that are 4-6 orders of magnitude smaller.
    # Linear scale would render the entire tail invisible as a flat line at
    # zero, hiding the most diagnostic part of the data.
    ax.set_yscale('log')

    ax.set_xlabel('Wakeup latency (µs)')
    ax.set_ylabel('Sample count (log scale)')
    ax.set_title(
        f'cyclictest 1h under stress-ng load — PREEMPT_RT 6.12 / i7-9750H\n'
        f'{total_samples:,} samples across {n_cpus} CPUs'
    )

    # Draw vertical lines at each percentile and label them. These are the
    # numbers an RT engineer reads first.
    for value, label in [(p50, 'p50'),
                         (p99, 'p99'),
                         (p999, 'p99.9'),
                         (p9999, 'p99.99'),
                         (max_seen, 'max')]:
        if value is None:
            continue
        ax.axvline(value, color='#c0392b', linestyle='--',
                   linewidth=0.8, alpha=0.7)
        # Place the label vertically so it doesn't overlap the next one
        # when percentiles are close together.
        ax.text(value, ax.get_ylim()[1] * 0.5,
                f' {label}={value}µs',
                rotation=90, verticalalignment='center',
                fontsize=9, color='#c0392b')

    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_locator(mticker.MaxNLocator(20))

    fig.tight_layout()
    fig.savefig(outpath, dpi=120)
    print(f"Saved {outpath}")
    print(f"Stats: min={min_seen}  p50={p50}  p99={p99}  "
          f"p99.9={p999}  p99.99={p9999}  max={max_seen}  "
          f"total={total_samples:,}  cpus={n_cpus}")


if __name__ == '__main__':
    main()
