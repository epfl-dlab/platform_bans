from tempfile import NamedTemporaryFile
from matplotlib.image import imread
import matplotlib.pyplot as plt
import matplotlib.transforms as transforms
import scipy.stats as stats
import bootstrapped.bootstrap as bs
import bootstrapped.stats_functions as bs_stats
import bootstrapped.compare_functions as bs_compare
import numpy as np


def plot_intervention(ax, interventions, venue, intervention, interventions_helper, int_ls, int_c,
                      grace_period,
                      th=2, size=9, text=False):
    xsint = []

    trans = transforms.blended_transform_factory(
        ax.transData, ax.transAxes)
    if intervention == "all":
        for key in interventions[venue].keys():
            # print(key)
            ax.axvline(interventions[venue][key], alpha=0.3, color=int_c[key], ls=int_ls[key])

            delta = 0
            for x in xsint:
                diff = (abs((interventions[venue][key] - x).total_seconds() // (24 * 60 * 60)))
                if diff < th:
                    delta += 0.2
            if text:
                plt.text(interventions[venue][key], 1.04 + delta, interventions_helper[key],
                         transform=trans, ha='center', size=size)
            xsint.append(interventions[venue][key])

    else:
        ax.axvline(interventions[venue][intervention], alpha=0.3)
        if text:
            plt.text(interventions[venue][intervention], 1.02, interventions_helper[intervention],
                     transform=trans, ha='center', size=size)

    start, end = grace_period[venue]
    ax.axvline(start, color="black", lw=0.5, ls=":")
    ax.axvline(end, color="black", lw=0.5, ls=":")


def get_size(fig, dpi=100):
    with NamedTemporaryFile(suffix='.png') as f:
        fig.savefig(f.name, bbox_inches='tight', dpi=dpi)
        height, width, _channels = imread(f.name).shape
        return width / dpi, height / dpi


def set_size(fig, size, dpi=100, eps=1e-2, give_up=2, min_size_px=10):
    target_width, target_height = size
    set_width, set_height = target_width, target_height  # reasonable starting point
    deltas = []  # how far we have
    while True:
        fig.set_size_inches([set_width, set_height])
        actual_width, actual_height = get_size(fig, dpi=dpi)
        set_width *= target_width / actual_width
        set_height *= target_height / actual_height
        deltas.append(abs(actual_width - target_width) + abs(actual_height - target_height))
        if deltas[-1] < eps:
            return True
        if len(deltas) > give_up and sorted(deltas[-give_up:]) == deltas[-give_up:]:
            return False
        if set_width * dpi < min_size_px or set_height * dpi < min_size_px:
            return False


def match_plot_ccdf(df_gb, df_before_after, ax, colors, val="num_posts",
                    val_matched=["num_posts_x", "num_posts_y"]):
    append_dists = []

    for color, label, kind, val_m in zip(colors, ["Reddit", "Fringe"], ["before", "after"], val_matched):
        vals = df_gb[df_gb.kind == kind].sort_values(val)[val].values.astype(int)
        vals = vals[vals >= 0]

        append_dists.append(vals)
        y = np.cumsum(np.bincount(vals))
        y = (y / y[-1])
        y = 1 - y
        x = list(range(0, max(vals) + 1))

        ax.plot(x, y, color=color, ls="-", label="{}".format(label))

        mean = bs.bootstrap(vals, stat_func=bs_stats.mean, is_pivotal=False)
        median = bs.bootstrap(vals, stat_func=bs_stats.median, is_pivotal=False)
        print("mean all", kind, mean)
        ax.axvline(mean.value, color=color, ls="-", lw=2, alpha=0.2)

        if df_before_after is None:
            continue

        vals2 = df_before_after.sort_values(val_m)[val_m].values.astype(int)
        vals2 = vals2[vals2 >= 0]

        append_dists.append(vals2)
        y = np.cumsum(np.bincount(vals2))
        y = (y / y[-1])
        y = 1 - y
        x = list(range(0, max(vals2) + 1))
        ax.plot(x, y, color=color, ls=":", label="{} (Matched)".format(label))

        mean2 = bs.bootstrap(vals2, stat_func=bs_stats.mean, is_pivotal=False)
        median2 = bs.bootstrap(vals2, stat_func=bs_stats.median, is_pivotal=False)

        print("mean matched", kind, mean2)
        ax.axvline(mean2.value, color=color, ls=":", lw=2, alpha=0.5)


    if df_before_after is None:
        print("Reddit all vs. Fringe All")
        print(stats.ks_2samp(append_dists[0], append_dists[1], alternative="greater"))
    else:
        print("Reddit all vs. matched")
        print(stats.ks_2samp(append_dists[0], append_dists[1], alternative="greater"))
        print("Fringe all vs. matched")
        print(stats.ks_2samp(append_dists[2], append_dists[3], alternative="greater"))
        print("Reddit all vs. Fringe all")
        print(stats.ks_2samp(append_dists[0], append_dists[2]))
        print("Reddit matched vs. Fringe matched")
        print(stats.ks_2samp(append_dists[1], append_dists[3]))
