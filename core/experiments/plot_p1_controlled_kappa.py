"""Renders the controlled-kappa figure the paper's own plan calls for
(EXPERIMENT_EXECUTION_PLAN.md P1: "Main-paper output: controlled-kappa
figure"). Two panels: E[G]/G* and E[Phi]/Phi*, each vs. kappa (log-log),
one line per method, with the analytical kappa/2 and kappa/4 reference
lines Theorem thm:kappa's lower bound is stated against.
"""
import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(__file__)
CSV_PATH = os.path.join(HERE, "results", "p1_controlled_kappa.csv")

METHOD_STYLE = {
    "merged_1k": dict(color="#c0392b", marker="o", label="Merged-1k"),
    "merged_2k": dict(color="#e67e22", marker="s", label="Merged-2k (comm.-matched)"),
    "splitgroup_2k": dict(color="#2980b9", marker="^", label="SplitGroup-2k"),
    "centralized": dict(color="#27ae60", marker="x", linestyle="--", label="Centralized (reference)"),
}

rows = list(csv.DictReader(open(CSV_PATH)))
for r in rows:
    r["kappa"] = int(r["kappa"])
    for k in ("eps", "G_star", "Phi_star", "mean_G", "se_G", "mean_Phi", "se_Phi", "ratio_G", "ratio_Phi"):
        r[k] = float(r[k])

methods = sorted(set(r["method"] for r in rows), key=lambda m: list(METHOD_STYLE).index(m))
kappas = sorted(set(r["kappa"] for r in rows))

fig, (ax_g, ax_phi) = plt.subplots(1, 2, figsize=(11, 4.5))

for ax, ratio_key, se_key, mean_key, star_key, ylabel, bound_num in [
    (ax_g, "ratio_G", "se_G", "mean_G", "G_star", r"$\mathbb{E}[G]/G^*$", 2),
    (ax_phi, "ratio_Phi", "se_Phi", "mean_Phi", "Phi_star", r"$\mathbb{E}[\Phi]/\Phi^*$", 4),
]:
    for m in methods:
        sub = sorted([r for r in rows if r["method"] == m], key=lambda r: r["kappa"])
        xs = [r["kappa"] for r in sub]
        ys = [r[ratio_key] for r in sub]
        err = [r[se_key] / r[star_key] for r in sub]
        ax.errorbar(xs, ys, yerr=err, capsize=2, **METHOD_STYLE[m])
    xs_line = np.array(kappas, dtype=float)
    ax.plot(xs_line, xs_line / bound_num, color="black", linestyle=":", linewidth=1,
            label=f"$\\kappa/{bound_num}$ (proven lower bound, this panel)")
    ax.set_xscale("log", base=2)
    ax.set_yscale("log")
    ax.set_xlabel(r"$\kappa$")
    ax.set_ylabel(ylabel)
    ax.grid(alpha=0.3, which="both")

ax_g.set_title("Warm-start balanced surrogate")
ax_phi.set_title("Warm-start fair objective")

handles_g, labels_g = ax_g.get_legend_handles_labels()
handles_phi, labels_phi = ax_phi.get_legend_handles_labels()
# Method lines repeat identically across both panels (same color/marker);
# only the two panel-specific bound lines need to both survive de-duping.
seen, handles, labels = set(), [], []
for h, l in zip(handles_g + handles_phi, labels_g + labels_phi):
    if l in seen and "bound" not in l:
        continue
    seen.add(l)
    handles.append(h)
    labels.append(l)
fig.legend(handles, labels, loc="upper left", bbox_to_anchor=(1.0, 0.95), frameon=False)
fig.suptitle(r"Controlled-$\kappa$ validation of Theorem (tight heterogeneity dependence)", y=1.03)
fig.tight_layout()

out_path = os.path.join(HERE, "results", "p1_controlled_kappa.png")
fig.savefig(out_path, dpi=150, bbox_inches="tight")
print(f"wrote {out_path}")
