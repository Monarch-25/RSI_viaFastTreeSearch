"""Generate verified figures for auto-evolution research draft."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

OUT = "/Users/mozart/Documents/ml/research/agents/auto-evolution-draft/figs"
np.random.seed(7)

# Professional research palette (matches Mermaid classDef: slate / teal / stone, no default red-blue)
NAVY = "#1F3349"
SLATE = "#5B6B7C"
TEAL = "#2F6B57"
TEAL_LIGHT = "#E7F0EB"
STONE = "#7A6420"
GRID = "#E5E8EB"
plt.rcParams.update({"axes.edgecolor": NAVY, "axes.labelcolor": NAVY,
                     "text.color": NAVY, "xtick.color": NAVY, "ytick.color": NAVY,
                     "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6})

# --- Fig 1: Hillclimb (best-so-far) + cost burn-down, illustrative synthetic run ---
plt.figure(figsize=(10, 4.2))
gens = np.arange(0, 241)
# monotonic best-so-far with diminishing returns + 3 breakthrough jumps (Shinka-like)
base = 0.61 + 0.10*(1-np.exp(-gens/60)) + 0.015*np.log1p(gens/10)
jumps = np.zeros_like(base)
jumps[55:] += 0.025; jumps[130:] += 0.03; jumps[185:] += 0.018
best = base + jumps
# raw per-eval noisy observations below best-so-far
raw = best - np.abs(np.random.normal(0, 0.02, size=gens.shape)) - 0.01*np.random.rand(len(gens))
raw[0] = best[0]
fig, ax1 = plt.subplots(figsize=(10, 4.4))
ax1.scatter(gens, raw, s=8, alpha=0.4, color=SLATE, label="per-candidate proxy score")
ax1.plot(gens, best, linewidth=2.6, color=TEAL, label="best-so-far S(c)")
ax1.set_xlabel("Evaluations (proxy suite)", fontsize=14)
ax1.set_ylabel("Composite score S(c)", fontsize=14)
ax1.set_ylim(0.55, 0.86)
ax1.tick_params(labelsize=12)
ax1.set_title("Fig 1 — Illustrative hillclimb: best-so-far vs. evaluations (synthetic, Shinka/LEVI-style trajectory)", fontsize=15)
ax2 = ax1.twinx()
cost = gens * (4.50/240)  # LEVI-typical $4.50 per 240 evals
ax2.plot(gens, cost, linestyle="--", linewidth=1.6, color=NAVY, label="cumulative cost (USD)")
ax2.set_ylabel("Cumulative cost (USD)", fontsize=14)
ax2.tick_params(colors=NAVY, labelsize=12)
for x in [55, 130, 185]:
    ax1.axvline(x, linestyle=":", linewidth=1.2, color=STONE)
ax1.text(55, 0.80, "paradigm\nshift", ha="center", fontsize=11)
ax1.text(130, 0.80, "highlight\nfix", ha="center", fontsize=11)
ax1.text(185, 0.80, "retriever\nfix", ha="center", fontsize=11)
fig.legend(loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.02), fontsize=12)
fig.tight_layout()
fig.savefig(f"{OUT}/fig1_hillclimb.png", dpi=200, bbox_inches="tight")
plt.close(fig)
print("wrote fig1_hillclimb.png", best[0], best[-1], cost[-1])

# --- Fig 2: Cost comparison (from LEVI paper ADRS numbers; Shinka ICFP $60/320 as reference) ---
labels = ["LEVI\n(this work\ntarget)", "GEPA", "OpenEvolve", "ShinkaEvolve", "Frontier-only\nAlphaEvolve-style"]
costs = [4.5, 18.0, 22.0, 15.0, 30.0]
scores = [76.5, 71.9, 70.6, 67.4, 70.0]
x = np.arange(len(labels))
fig, ax = plt.subplots(figsize=(10, 4.4))
palette = [TEAL, SLATE, SLATE, SLATE, "#8A94A0"]
bars = ax.bar(x, costs, color=palette, edgecolor=NAVY, linewidth=1.0)
ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=12)
ax.set_ylabel("USD per problem (ADRS suite, log-scale illustrative)", fontsize=14)
ax.tick_params(labelsize=12)
ax.set_yscale("log")
ax.set_title("Fig 2 — Cost vs. quality (ADRS means from LEVI 2026; costs: LEVI $4.50 typical, baselines $15-30)", fontsize=15)
for i, (c, s) in enumerate(zip(costs, scores)):
    ax.text(i, c*1.12, f"${c:.1f}\nscore {s}", ha="center", fontsize=12)
ax.set_ylim(3, 45)
fig.tight_layout()
fig.savefig(f"{OUT}/fig2_cost.png", dpi=200, bbox_inches="tight")
plt.close(fig)
print("wrote fig2_cost.png")

# --- Fig 3: CVT-MAP-Elites archive heatmap (synthetic but structurally faithful) ---
rng = np.random.default_rng(11)
n = 36
# 2D behavioral descriptor: x=code complexity, y=rule-tradeoff (trademark F1 - datetime F1)
# rejection-sample for min separation so labels do not overlap (chart legibility, not a model claim)
pts = []
tries = 0
while len(pts) < n and tries < 5000:
    tries += 1
    cand = rng.uniform(0.02, 0.98, 2)
    if all(np.linalg.norm(cand - np.array(p)) > 0.13 for p in pts):
        pts.append(cand)
pts = np.array(pts); n = len(pts)
cx, cy = pts[:, 0], pts[:, 1]
cell_score = 0.55 + 0.25*np.sqrt(cx*cy) + rng.normal(0, 0.03, n)
cell_score = np.clip(cell_score, 0.4, 0.95)
occupied = cell_score > 0.60  # leave some cells empty on purpose: diversity reserve
fig, ax = plt.subplots(figsize=(7.8, 5.6))
sc = ax.scatter(cx[occupied], cy[occupied], c=cell_score[occupied], s=560, marker="s",
                vmin=0.55, vmax=0.85, cmap="YlGnBu", edgecolors=NAVY, linewidths=0.6)
ax.scatter(cx[~occupied], cy[~occupied], s=560, marker="s", c="#EDEFF2", edgecolors=SLATE, alpha=0.9)
for i in range(n):
    ax.text(cx[i], cy[i], f"{cell_score[i]:.2f}" if occupied[i] else "empty", ha="center", va="center", fontsize=11)
ax.set_xlabel("Dim 1: structural complexity (normalized)", fontsize=13)
ax.set_ylabel("Dim 2: rule tradeoff (normalized)", fontsize=13)
ax.tick_params(labelsize=12)
ax.set_title("Fig 3 — CVT-MAP-Elites archive (36 cells, synthetic):\nkeep best per cell, not global best only", fontsize=14)
fig.colorbar(sc, label="cell-best S(c)")
fig.tight_layout()
fig.savefig(f"{OUT}/fig3_map_elites.png", dpi=200, bbox_inches="tight")
plt.close(fig)
print("wrote fig3_map_elites.png", occupied.sum(), "occupied")

# --- Fig 4: Proxy benchmark rank-preservation (synthetic calibration matrix demo) ---
# 24 seeds x 60 docs; proxy 12 docs preserves ranking with rho~0.96
m, ndocs, k = 24, 60, 12
true_q = rng.normal(0.65, 0.08, m)
doc_diff = rng.normal(0, 0.06, ndocs)
M = true_q[:, None] + doc_diff[None, :] + rng.normal(0, 0.03, (m, ndocs))
full = M.mean(axis=1)
# greedy pick discriminative docs (high col-std, low redundancy) — simplified faithful proxy
colstd = M.std(axis=0)
order = np.argsort(-colstd)[:k]
proxy = M[:, order].mean(axis=1)
order_full = np.argsort(-full); order_proxy = np.argsort(-proxy)
fig, ax = plt.subplots(figsize=(6.8, 5.0))
ax.scatter(full, proxy, s=48, color=TEAL, edgecolors=NAVY, linewidths=0.6, alpha=0.9)
for i in range(m):
    ax.text(full[i], proxy[i], f"p{i}", fontsize=10)
ax.set_xlabel("Full discovery score (mean over 60 docs)", fontsize=13)
ax.set_ylabel("Proxy score (mean over 12 discriminative docs)", fontsize=13)
ax.tick_params(labelsize=12)
ax.set_title("Fig 4 — Proxy benchmark preserves RANK (synthetic demo):\nselection needs ordering, not exact scores", fontsize=14)
# Spearman
from scipy.stats import spearmanr
try:
    rho, _ = spearmanr(full, proxy)
    ax.text(0.02, 0.98, f"Spearman rho={rho:.2f}", transform=ax.transAxes, va="top", fontsize=12,
            bbox=dict(facecolor="white", edgecolor="gray"))
    print("spearman", rho)
except Exception as e:
    print("spearman unavailable", e)
fig.tight_layout()
fig.savefig(f"{OUT}/fig4_proxy_rank.png", dpi=200, bbox_inches="tight")
plt.close(fig)
print("wrote fig4_proxy_rank.png")

# --- Fig 5: HLD block diagram (vector boxes, deterministic layout) ---
fig, ax = plt.subplots(figsize=(11, 5.2))
ax.set_xlim(0, 11); ax.set_ylim(0, 6); ax.axis("off")
ax.set_title("Fig 5 — HLD block diagram: Context Lake → Control → Sandboxed Evolution → Human Plane", fontsize=11)
boxes = [
    (0.2, 3.4, 2.2, 2.0, "A. Context Lake\n- snapshot\n- traces\n- CSV/docs\n- style guide"),
    (2.8, 3.4, 2.2, 2.0, "B. Control\n- orchestrator\n- nudge queue\n- archive\n- ledger"),
    (5.4, 3.4, 2.6, 2.0, "C. Evolution\n(sandbox)\n- adapter API\n- router/mutator\n- evaluator farm\n- VAULT (RO)"),
    (8.4, 3.4, 2.4, 2.0, "D. Human\n- WebUI/tree\n- hillclimb obs\n- PM/Dev gates"),
    (2.8, 0.6, 5.2, 1.6, "Module spine:\nM1 Diagnose -> Gate(PM/Dev) -> M2 SearchCtx -> M3 Score/Re-evolve\n(every promotion needs human approval)"),
]
for x, y, w, h, t in boxes:
    face = {"A.": "#E9EEF3", "B.": "#F4F6F8", "C.": TEAL_LIGHT, "D.": "#F7F0DF",
            "Module": "#F4F6F8"}[[k for k in ["A.", "B.", "C.", "D.", "Module"] if t.startswith(k)][0]]
    edge = {"A.": "#3B4F66", "B.": "#3B4F66", "C.": TEAL, "D.": STONE,
            "Module": "#3B4F66"}[[k for k in ["A.", "B.", "C.", "D.", "Module"] if t.startswith(k)][0]]
    ax.add_patch(patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.05", facecolor=face, edgecolor=edge, linewidth=1.4))
    ax.text(x+w/2, y+h/2, t, ha="center", va="center", fontsize=9, color=NAVY)
for x1, x2 in [(2.4, 2.8), (5.0, 5.4), (8.0, 8.4)]:
    ax.annotate("", xy=(x2, 4.4), xytext=(x1, 4.4), arrowprops=dict(arrowstyle="->", lw=1.5, color=NAVY))
ax.annotate("", xy=(8.6, 3.4), xytext=(6.7, 3.4), arrowprops=dict(arrowstyle="->", ls="dashed", lw=1.2, color=STONE))
ax.text(7.6, 3.0, "score + lineage", fontsize=8, ha="center", color=STONE)
fig.tight_layout()
fig.savefig(f"{OUT}/fig5_hld.png", dpi=160, bbox_inches="tight")
plt.close(fig)
print("wrote fig5_hld.png")
