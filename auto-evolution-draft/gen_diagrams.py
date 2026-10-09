"""Generate the explainer's architecture diagrams as standalone SVGs.

Each diagram answers exactly one question (see module docstrings below).
Palette matches research_draft.md: slate #3B4F66 / ink #1F3349, teal #2F6B57,
stone #7A6420. Minimum body text 18px; node titles 22-28px; figure titles 30px+.
Canvas widths 1600-2200px per the editorial spec.

Regenerate: python3 gen_diagrams.py
Verify:     python3 check_diagrams.py
"""
import os

OUT = "/Users/mozart/Documents/ml/research/agents/auto-evolution-draft/figs"

NAVY = "#1F3349"
SLATE = "#3B4F66"
SLATE_SOFT = "#E9EEF3"
SLATE_MID = "#6B7F96"
TEAL = "#2F6B57"
TEAL_SOFT = "#E7F0EB"
TEAL_MID = "#5A9179"
STONE = "#7A6420"
STONE_SOFT = "#F7F0DF"
STONE_MID = "#A98F3F"
WHITE = "#FFFFFF"
GRAY = "#F4F6F8"
LINE = "#E9E3D7"
INK2 = "#4A443C"
INK3 = "#7A7368"
INK4 = "#A39B8D"
TERRA = "#C05621"
TERRA_SOFT = "#FBEBDD"
GREEN_OK = "#2F6B57"

FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,'SF Mono',Menlo,Consolas,monospace"


def tw(s, size, factor=0.55):
    """Rough text width for the system sans stack."""
    return len(s) * size * factor


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class Scene:
    def __init__(self, w, h, title, q):
        self.w, self.h = w, h
        self.title = title
        self.q = q
        self.el = []
        self._box_n = 0

    # ---------- primitives ----------
    def raw(self, s):
        self.el.append(s)

    def text(self, x, y, s, size=18, color=NAVY, anchor="middle", weight=500,
             mono=False, in_box=None, role=None):
        fam = MONO if mono else FONT
        extra = ""
        if in_box is not None:
            extra += f' data-in="{in_box}"'
        if role:
            extra += f' data-role="{role}"'
        self.raw(
            f'<text x="{x:.0f}" y="{y:.0f}" text-anchor="{anchor}" '
            f'font-family="{fam}" font-size="{size}" font-weight="{weight}" '
            f'fill="{color}"{extra}>{esc(s)}</text>'
        )
        return tw(s, size, 0.60 if mono else 0.55)

    def rect(self, x, y, w, h, fill=WHITE, stroke=SLATE, rx=14, sw=2,
             dash=None, node=True, extra=""):
        n = ""
        if node:
            self._box_n += 1
            n = f' data-box="b{self._box_n}"'
            self._last_box = f"b{self._box_n}"
        else:
            self._last_box = None
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.raw(
            f'<rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" '
            f'rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}{n}{extra}/>'
        )
        return self._last_box

    def box(self, x, y, w, h, title, subs=(), fill=WHITE, edge=SLATE,
            tsize=24, ssize=18, badge=None, dash=None, sw=2, tcolor=NAVY,
            scolor=INK2, tmono=False):
        bid = self.rect(x, y, w, h, fill, edge, dash=dash, sw=sw)
        ty = y + (38 if len(subs) == 0 else 32)
        if badge:
            bcx, bcy = x + 26, y + 26
            self.raw(
                f'<circle cx="{bcx}" cy="{bcy}" r="16" fill="{edge}"/>'
                f'<text x="{bcx}" y="{bcy + 6}" text-anchor="middle" font-family="{FONT}" '
                f'font-size="17" font-weight="700" fill="#fff" data-in="{bid}">{badge}</text>'
            )
            self.text(x + w / 2 + 14, ty, title, tsize, tcolor, weight=600, in_box=bid, role="title")
        else:
            self.text(x + w / 2, ty, title, tsize, tcolor, weight=600, in_box=bid, role="title")
        sy = ty + ssize + 12
        for s in subs:
            self.text(x + w / 2, sy, s, ssize, scolor, in_box=bid)
            sy += ssize + 8
        return bid

    def label(self, x, y, s, size=18, color=INK2, anchor="middle", weight=500, mono=False):
        return self.text(x, y, s, size, color, anchor, weight, mono=mono)

    def arrow(self, x1, y1, x2, y2, color=SLATE_MID, dashed=False, label=None,
              lsize=18, lcolor=None, ldy=-10, elbow=None, head=True, lw=2.4):
        """Straight arrow; elbow = ('v', midy) or ('h', midx) inserts a bend."""
        d = f' stroke-dasharray="10 7"' if dashed else ""
        hd = ' marker-end="url(#a-{})"'.format(color.lstrip("#")) if head else ""
        if elbow:
            axis, m = elbow
            if axis == "v":
                path = f"M {x1:.0f} {y1:.0f} L {x1:.0f} {m:.0f} L {x2:.0f} {m:.0f} L {x2:.0f} {y2:.0f}"
            else:
                path = f"M {x1:.0f} {y1:.0f} L {m:.0f} {y1:.0f} L {m:.0f} {y2:.0f} L {x2:.0f} {y2:.0f}"
        else:
            path = f"M {x1:.0f} {y1:.0f} L {x2:.0f} {y2:.0f}"
        self.raw(
            f'<path d="{path}" fill="none" stroke="{color}" stroke-width="{lw}"{d}{hd}/>'
        )
        if label:
            if elbow:
                mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            else:
                mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            lc = lcolor or INK3
            self.label(mx, my + ldy, label, lsize, lc)

    def curve(self, x1, y1, x2, y2, cx, cy, color=TEAL, dashed=True, label=None,
              lsize=18, lcolor=None, head=True, lw=2.4):
        d = ' stroke-dasharray="10 7"' if dashed else ""
        hd = f' marker-end="url(#a-{color.lstrip("#")})"' if head else ""
        self.raw(
            f'<path d="M {x1:.0f} {y1:.0f} Q {cx:.0f} {cy:.0f} {x2:.0f} {y2:.0f}" '
            f'fill="none" stroke="{color}" stroke-width="{lw}"{d}{hd}/>'
        )
        if label:
            lx, ly = 0.25 * x1 + 0.5 * cx + 0.25 * x2, 0.25 * y1 + 0.5 * cy + 0.25 * y2
            self.label(lx, ly + (lsize + 4), label, lsize, lcolor or color)

    def defs(self):
        marks = []
        for c in {SLATE_MID, TEAL, STONE, NAVY, TERRA, TEAL_MID, STONE_MID}:
            marks.append(
                f'<marker id="a-{c.lstrip("#")}" viewBox="0 0 10 10" refX="9" refY="5" '
                f'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
                f'<path d="M0 0 L10 5 L0 10 z" fill="{c}"/></marker>'
            )
        return "<defs>" + "".join(marks) + "</defs>"

    def write(self, fname):
        title_id = "t-" + fname.replace(".svg", "")
        body = "\n".join(self.el)
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" '
            f'width="{self.w}" height="{self.h}" role="img" aria-labelledby="{title_id}">\n'
            f'<title id="{title_id}">{esc(self.title)}. {esc(self.q)}</title>\n'
            f'<rect width="{self.w}" height="{self.h}" fill="{WHITE}"/>\n'
            f"{self.defs()}\n"
            f'<text x="{self.w / 2:.0f}" y="52" text-anchor="middle" font-family="{FONT}" '
            f'font-size="32" font-weight="700" fill="{NAVY}">{esc(self.title)}</text>\n'
            f"{body}\n</svg>\n"
        )
        path = os.path.join(OUT, fname)
        with open(path, "w") as f:
            f.write(svg)
        print(f"wrote {fname} ({self.w}x{self.h})")


# ══════════════════════════════════════════════════════════════════════════════
# 1. Proofreader pipeline — Q: which parts of this pipeline may change?
# ══════════════════════════════════════════════════════════════════════════════
def pipe_proofreader():
    s = Scene(960, 1700, "The proofreader pipeline — seven editable dimensions",
              "Which parts of this pipeline may change?")
    s.label(480, 96, "PDF / DOCX in  →  annotated document out  ·  run(doc_bytes) → spans[]",
            19, INK3)

    # Vertical pipeline: 8 stages, full width
    stages = [
        ("source document", ["text + char offsets + page map"], GRAY, SLATE, None),
        ("chunk", ["splitter · overlap · window"], WHITE, SLATE, "𝒮chunk"),
        ("style-guide retrieval", ["top-k · reranker · gazetteer"], WHITE, SLATE, "𝒮retr"),
        ("Bedrock call (per rule)", ["prompt template · model · schema"], TEAL_SOFT, TEAL, "𝒮prompt · 𝒮route"),
        ("span proposal", ["predicted spans + confidence"], WHITE, SLATE, "𝒮logic"),
        ("τ threshold", ["per-rule surfacing threshold"], WHITE, SLATE, "𝒮τ"),
        ("highlight anchor", ["fuzzy match → PDF coords"], WHITE, SLATE, "𝒮hl"),
        ("suggestion + document", ["fix text · annotated output"], GRAY, SLATE, None),
    ]
    payloads = ["text+offsets", "chunks", "rule chunks", "spans",
                "spans", "surfaced", "anchored"]
    ys = [150 + i * 184 for i in range(8)]
    for y, (t, sub, f, e, chip) in zip(ys, stages):
        s.box(40, y, 880, 100, t, sub, fill=f, edge=e)
        if chip:
            s.label(480, y + 128, chip, 18, TEAL, weight=600)
    for i in range(7):
        s.arrow(480, ys[i] + 148, 480, ys[i] + 184, color=SLATE_MID, label=None)
        s.label(480, ys[i] + 170, payloads[i], 18, INK3)

    # Frozen band
    s.rect(40, 1570, 880, 80, fill=STONE_SOFT, stroke=STONE, dash="12 8", sw=2.5, node=False)
    s.label(480, 1606, "never evolves: scorer · vault · adapter contract run(doc) → spans[]",
            19, "#5A4A14", weight=600)
    s.write("pipe_proofreader.svg")


# ══════════════════════════════════════════════════════════════════════════════
# 2. Diagnosis flow — Q: what happens to a failure?
# ══════════════════════════════════════════════════════════════════════════════
def flow_diagnose():
    s = Scene(960, 1390, "What happens to a failure?",
              "Feedback rows and traces become ranked, evidence-backed issue cards — or a constraint.")
    # Inputs 2x2
    ins = ["feedback CSV rows", "documents + offsets",
           "LangSmith + Bedrock traces", "snapshot + style guide"]
    ixs = [40, 490]
    for i, t in enumerate(ins):
        s.box(ixs[i % 2], 130 + (i // 2) * 92, 430, 72, t, (), fill=GRAY, edge=SLATE, tsize=22)
    # bottom-row inputs feed straight down; top-row inputs route around the sides
    for cx in (255, 705):
        s.arrow(cx, 294, cx, 330, color=SLATE_MID, lw=2)
    for x1, x2 in ((40, 20), (920, 940)):
        s.raw(f'<path d="M {x1} 166 L {x2} 166 L {x2} 390 L {x1} 390" fill="none" '
              f'stroke="{SLATE_MID}" stroke-width="2" marker-end="url(#a-{SLATE_MID.lstrip("#")})"/>')
    s.label(480, 314, "evidence", 18, INK3)

    # Lake
    s.box(40, 330, 880, 120, "Context Lake", ["append-only", "checksummed pulls"], fill=SLATE_SOFT, edge=SLATE)
    s.arrow(480, 450, 480, 500, color=SLATE_MID, lw=2, label=None)
    s.label(480, 478, "lake snapshot", 18, INK3)

    # Steps: 2 rows x 3, snaking right then right-to-left
    steps1 = [
        ("normalize", ["NFKC · offsets", "highlight/detect split"]),
        ("join traces", ["miss-rate · prompt", "hash · tokens"]),
        ("dedup", ["exact → MinHash", "→ emb 0.88 → LLM"]),
    ]
    steps2 = [
        ("issue card", ["evidence · class", "pathway hint"]),
        ("severity", ["σ(w·features) ·", "business weight"]),
        ("cluster", ["HDBSCAN ·", "failure taxonomy"]),
    ]
    sxs = [40, 345, 650]
    for x, (t, sub) in zip(sxs, steps1):
        s.box(x, 500, 270, 120, t, sub, fill=WHITE, edge=SLATE, tsize=23)
    for x, (t, sub) in zip(sxs, steps2):
        s.box(x, 650, 270, 120, t, sub, fill=WHITE, edge=SLATE, tsize=23)
    s.arrow(310, 560, 345, 560, color=SLATE_MID, lw=2.2)
    s.arrow(615, 560, 650, 560, color=SLATE_MID, lw=2.2)
    s.arrow(785, 620, 785, 650, color=SLATE_MID, lw=2.2)
    s.arrow(650, 710, 615, 710, color=SLATE_MID, lw=2.2)
    s.arrow(345, 710, 310, 710, color=SLATE_MID, lw=2.2)

    # Gates row
    s.arrow(175, 770, 245, 830, color=SLATE_MID, lw=2.2, label=None)
    s.label(210, 802, "issue_card", 18, INK3)
    s.box(40, 830, 400, 140, "G1 · PM triage", ["defect / preference /", "needs evidence + rationale"],
          fill=STONE_SOFT, edge=STONE, tsize=23)
    s.box(520, 830, 400, 140, "G2 · Dev feasibility", ["feasible / infeasible", "{reason, effort, risk}"],
          fill=STONE_SOFT, edge=STONE, tsize=23)
    s.arrow(440, 900, 520, 900, color=STONE, label=None)
    s.label(480, 890, "defects", 18, STONE)

    # Outputs row: do-not-optimize + pathways
    s.box(40, 1030, 430, 90, "do-not-optimize", ["never chase · Regress guard"],
          fill=TERRA_SOFT, edge=TERRA, tsize=22)
    s.arrow(245, 970, 245, 1030, color=TERRA, dashed=True, lw=2.2, label=None)
    s.label(140, 1005, "PREFERENCE_IGNORE", 18, TERRA, weight=600)
    s.box(490, 1030, 410, 120, "search pathways", ["PATH-A highlight · B retrieval", "C prompt · D routing/threshold"],
          fill=TEAL_SOFT, edge=TEAL, tsize=22)
    s.arrow(725, 970, 725, 1030, color=TEAL, label=None)
    s.label(725, 1005, "approved + feasible", 18, TEAL)

    # Backlog + infeasible curve around pathways
    s.box(40, 1200, 880, 90, "backlog", ["infeasible + reason"],
          fill=GRAY, edge=SLATE_MID, tsize=22, dash="8 6")
    s.raw(f'<path d="M 915 970 Q 975 1085 915 1200" fill="none" stroke="{SLATE_MID}" '
          f'stroke-width="2.2" stroke-dasharray="10 7" marker-end="url(#a-{SLATE_MID.lstrip("#")})"/>')

    s.label(480, 1340, "every vote carries its reason · preferences re-enter as constraints, not tasks",
            19, INK3)
    s.write("flow_diagnose.svg")


# ══════════════════════════════════════════════════════════════════════════════
# 3. Evaluation cost ladder — Q: when is money spent, when is a candidate killed?
# ══════════════════════════════════════════════════════════════════════════════
def ladder_eval():
    s = Scene(960, 1300, "The evaluation ladder",
              "Cheap signals first — a candidate only reaches expensive stages after surviving the cheap ones.")
    s.label(480, 120, "CHEAP  →  EXPENSIVE", 18, INK4, weight=700)

    rows = [
        ("novelty gate", ["docs: — · cost: free · labels: none",
                          "skip duplicates · kill: cos > 0.95 or boring vote",
                          "feeds search: ✗ pre-eval only"], TEAL_SOFT),
        ("smoke", ["docs: 5 fixed · cost: free · labels: discovery",
                   "fail-fast gate · kill: fail / timeout / canary hit",
                   "feeds search: ✓ gates only"], SLATE_SOFT),
        ("judge", ["docs: ≤10 pairs · cost: ledger · labels: none (reads files)",
                   "cheap ranking · kill: —",
                   "feeds search: ✓ BT rank"], TEAL_SOFT),
        ("proxy", ["docs: ~12–20 · cost: ~$0.10 avg · labels: discovery",
                   "search ranking · kill: stagnation / budget stop",
                   "feeds search: ✓ 80% of evals"], SLATE_SOFT),
        ("full discovery", ["docs: ~60–100 · cost: per finalist · labels: discovery",
                            "finalist selection · kill: —",
                            "feeds search: ✓ finalist rank"], SLATE_SOFT),
        ("holdout", ["docs: ~30 · cost: ×1 per run · labels: sealed · never",
                     "promotion claim · kill: —",
                     "feeds search: ✗ final claim only"], STONE_SOFT),
    ]
    y = 160
    for name, subs, fill in rows:
        bid = s.rect(40, y, 880, 150, fill=fill, stroke=LINE, sw=1.5, rx=12, node=True)
        s.text(460, y + 36, name, 23, NAVY, weight=700, in_box=bid, role="title")
        sy = y + 66
        for sub in subs:
            s.text(460, sy, sub, 18, INK2, in_box=bid)
            sy += 28
        y += 165

    s.rect(40, y + 10, 880, 110, fill=GRAY, stroke=LINE, sw=1.5, rx=12, node=False)
    s.label(480, y + 52, "≤250-eval budget → ≈80% proxy · ≈15% full discovery · holdout ×1",
            19, INK2)
    s.label(480, y + 86, "holdout is a gated ceremony, not a budget line · judge cost per ledger",
            18, INK3)
    s.write("ladder_eval.svg")


# ══════════════════════════════════════════════════════════════════════════════
# 4. Candidate lineage — Q: where did this candidate come from?
# ══════════════════════════════════════════════════════════════════════════════
def tree_lineage():
    s = Scene(960, 1000, "Candidate lineage",
              "Which ancestors does the best candidate carry, and what did each edit cost?")

    def node(x, y, w, cid, score, path, cost, star=False, queued=False):
        fill = TEAL_SOFT if star else (GRAY if queued else WHITE)
        edge = TEAL if star else (SLATE_MID if queued else SLATE)
        title = f"{cid}{' ★' if star else ''}"
        subs = []
        if queued:
            subs = ["queued · inherits parent", path, cost]
        else:
            subs = [f"S(c) = {score}", path, cost]
        s.box(x, y, w, 140, title, subs, fill=fill, edge=edge, tsize=23, sw=3 if star else 2)

    # Vertical tree: seed → two children → three grandchildren
    node(300, 130, 360, "seed_v0", "0.61", "production baseline", "start")
    node(60, 330, 400, "cand_004", "0.65", "PATH-B · retrieval + gazetteer", "small refine · $0.11")
    node(500, 330, 400, "cand_011", None, "PATH-D · threshold edit", "queued for eval", queued=True)
    node(40, 530, 290, "cand_019", "0.64", "PATH-A · highlighter", "small refine · $0.09")
    node(335, 530, 290, "cand_027", "0.71", "PATH-C · prompt decompose", "paradigm shift · $0.34")
    node(630, 530, 290, "cand_041", "0.73", "PATH-B + reranker", "small refine · $0.12")

    # Edges
    s.arrow(480, 270, 260, 330, color=SLATE_MID, lw=2.2)
    s.arrow(480, 270, 700, 330, color=SLATE_MID, lw=2.2)
    s.arrow(200, 470, 190, 530, color=SLATE_MID, lw=2.2)
    s.arrow(320, 470, 480, 530, color=SLATE_MID, lw=2.2)
    s.arrow(700, 470, 770, 530, color=SLATE_MID, lw=2.2)

    # Best-candidate callout
    s.rect(40, 730, 880, 150, fill=TEAL_SOFT, stroke=TEAL, rx=14, sw=2.5, node=False)
    s.label(480, 770, "best of the run", 18, TEAL, weight=700)
    s.label(480, 806, "full discovery 0.73", 22, NAVY, weight=600)
    s.label(480, 840, "holdout 0.718  (gap ≤ ε)", 19, INK2)
    s.label(480, 872, "run: $18.40 · 240 evals", 18, INK3)
    s.arrow(770, 670, 770, 730, color=TEAL, lw=2.4)

    s.label(480, 930, "stop: STAGNATION_30 ∧ budget_75% · every node keeps its diff and score vector",
            19, INK3)
    s.label(480, 962, "scores and costs shown are illustrative; the chain shape is what the archive stores",
            18, INK4)
    s.write("tree_lineage.svg")


# ══════════════════════════════════════════════════════════════════════════════
# 5. Vault boundary — Q: what can the agent never do?
# ══════════════════════════════════════════════════════════════════════════════
def vault_boundary():
    s = Scene(960, 1250, "The Benchmark Vault is a boundary, not a database",
              "The search may ask the vault for scores; it may never write, peek, or finalize on its own.")

    # Outside actors in a row
    s.label(480, 100, "OUTSIDE — the search", 19, INK4, weight=700)
    actors = [
        ("coding agent (Copilot)", ["authors ONE candidate patch", "from a sampled parent"], 40),
        ("mutation model", ["small refine · frontier shift"], 335),
        ("evaluator farm", ["builds image · runs docs", "in the sandbox"], 630),
    ]
    for t, sub, x in actors:
        s.box(x, 130, 290, 120, t, sub, fill=GRAY, edge=SLATE, tsize=22)
    s.arrow(480, 250, 480, 300, color=TEAL, dashed=True, label=None)
    s.label(390, 278, "POST /score", 18, TEAL)
    s.arrow(620, 300, 680, 252, color=TEAL, dashed=True, label=None)
    s.label(775, 272, "score vector", 18, TEAL)

    # Boundary
    s.rect(40, 300, 880, 680, fill="#FBFAF7", stroke=STONE, sw=4, dash="18 10", rx=22, node=False)
    s.label(480, 342, "BENCHMARK VAULT — separate account · read-only mount",
            20, STONE, weight=700)
    s.label(480, 370, "the agent cannot write · finalize is human-gated", 18, STONE)

    inner = [
        ("discovery set", ["~60 labeled docs"], 60, 380),
        ("holdout set", ["~30 docs · sealed"], 480, 380),
        ("frozen labels", ["SHA-256 · bench_v7"], 60, 524),
        ("frozen scorer", ["IoU ≥ 0.5 · S(c) weights"], 480, 524),
        ("canaries", ["nonsense marks · sealed"], 60, 668),
        ("bench_ver pin", ["docs + labels + scorer"], 480, 668),
    ]
    for t, sub, x, y in inner:
        s.box(x, y, 420, 124, t, sub, fill=SLATE_SOFT, edge=SLATE, tsize=22)

    # Finalize through a gate
    s.box(60, 832, 840, 110, "POST /finalize", ["human-gated · once per run", "promotion request only — a human stands on this line"],
          fill=STONE_SOFT, edge=STONE, tsize=22)

    # Forbidden
    s.rect(40, 1020, 880, 190, fill=TERRA_SOFT, stroke=TERRA, sw=2, rx=16, node=False)
    s.label(480, 1062, "FORBIDDEN — guardrail diff-scanner rejects the candidate, not just the request",
            19, TERRA, weight=700)
    s.label(260, 1105, "✗ write benchmark files", 20, "#8A3B12", weight=600)
    s.label(700, 1105, "✗ read holdout labels", 20, "#8A3B12", weight=600)
    s.label(260, 1145, "✗ modify the scorer", 20, "#8A3B12", weight=600)
    s.label(700, 1145, "✗ finalize without a human", 20, "#8A3B12", weight=600)
    s.label(480, 1188, "canary hits block promotion when the candidate flags marks it never saw in discovery",
            18, INK3)
    s.write("vault_boundary.svg")


# ══════════════════════════════════════════════════════════════════════════════
# 6. Human gates — Q: who can say no, and what happens when they do?
# ══════════════════════════════════════════════════════════════════════════════
def flow_gates():
    s = Scene(960, 1680, "Four gates, every one a real decision",
              "The machine proposes at every stage; at four points a person can stop it.")
    gates = [
        ("G1 · PM triage", "issue cards",
         ["APPROVE_DEFECT", "PREFERENCE_IGNORE", "NEED_EVIDENCE", "+ rationale"]),
        ("G2 · Dev feasibility", "approved defects + code",
         ["FEASIBLE", "INFEASIBLE {reason, effort, risk}"]),
        ("G3 · Owner: run?", "pathways + budget",
         ["approve run · scope", "$ / eval caps", "→ run_id authorized"]),
        ("G4 · Owner + PM: ship?", "finalists + full + holdout",
         ["APPROVE → deploy tag", "ROLLBACK → parent", "reason → archive"]),
    ]
    ys = [150, 420, 690, 960]
    for y, (t, inp, outs) in zip(ys, gates):
        bid = s.rect(40, y, 880, 210, fill=STONE_SOFT, stroke=STONE, sw=2.5)
        s.text(480, y + 42, t, 23, NAVY, weight=700, in_box=bid, role="title")
        s.text(480, y + 74, f"in: {inp}", 18, INK3, in_box=bid)
        yy = y + 110
        for o in outs:
            s.text(480, yy, o, 18, "#5A4A14", weight=600, in_box=bid)
            yy += 30
    links = ["approved defects", "feasible set", "run authorized"]
    for i in range(3):
        s.arrow(480, ys[i] + 200, 480, ys[i + 1], color=STONE, label=None)
        s.label(480, ys[i] + 235, links[i], 18, STONE)

    # Negative path
    s.rect(40, 1230, 880, 140, fill=TERRA_SOFT, stroke=TERRA, sw=2, rx=14, node=False)
    s.label(480, 1270, "PREFERENCE_IGNORE  →  do-not-optimize constraints  (from G1)", 21, TERRA, weight=700)
    s.label(480, 1308, "injected into mutation prompts  ·  enforced as Regress guards", 19, "#8A3B12")
    s.label(480, 1342, "the loop is told what NOT to chase — the second-most valuable output of triage", 18, INK3)

    # Discipline
    s.rect(40, 1410, 880, 140, fill=GRAY, stroke=LINE, sw=1.5, rx=14, node=False)
    s.label(480, 1450, "every vote is timestamped, immutable, and carries its reason", 20, NAVY, weight=600)
    s.label(480, 1488, "only G4 is synchronous — G1–G3 run on queues so the search never waits", 19, INK2)
    s.label(480, 1522, "a rollback reason re-enters the archive as a constraint on future mutations", 18, INK3)

    s.label(480, 1600, "G3 fires for every evolution run — there is no unattended budget", 19, STONE, weight=600)
    s.label(480, 1634, "G4 fires once per run, after the single permitted holdout evaluation", 19, STONE, weight=600)
    s.write("flow_gates.svg")


# ══════════════════════════════════════════════════════════════════════════════
# 7. Evolution loop (HERO) — Q: how does one evolution run work?
# ══════════════════════════════════════════════════════════════════════════════
def loop_evolution():
    s = Scene(960, 2810, "One evolution run",
              "Sample a parent, mutate it, judge it cheaply, archive what is novel — repeat until it stops paying.")
    bx, bw, bh = 40, 420, 110

    def stage(y, title, subs, fill=WHITE, edge=SLATE):
        s.box(bx, y, bw, bh, title, subs, fill=fill, edge=edge, tsize=23)

    # Main column
    stage(150, "parent archive", ["MAP-Elites champions · every candidate"], fill=SLATE_SOFT)
    stage(314, "parent selection", ["softmax(S / T) · novelty bonus ν"], fill=WHITE)
    stage(478, "route mutation", ["UCB over models · stagnation check"], fill=WHITE)
    stage(642, "cheap refinement", ["small model · ONE targeted edit", "∇text = failing trace + verifier msg"], fill=TEAL_SOFT, edge=TEAL)
    stage(806, "paradigm shift", ["frontier model · k diverse cells", "fires on stagnation or interval"], fill=TEAL_SOFT, edge=TEAL)
    stage(970, "candidate", ["diff + image build · self-check attached"], fill=WHITE)
    stage(1134, "novelty gate", ["cos(d_new, d_arch) > 0.95 → LLM vote", "duplicate → free reject, resample parent"], fill=WHITE)
    stage(1298, "smoke", ["5 fixed docs · free", "fail / timeout / canary → rejected"], fill=SLATE_SOFT)
    stage(1462, "judge", ["pairwise vs ≤10 incumbents · full files", "wins → regularized Bradley–Terry refit"], fill=TEAL_SOFT, edge=TEAL)
    stage(1626, "proxy score", ["vault POST /score · ~12–20 docs"], fill=SLATE_SOFT)
    stage(1790, "archive insert", ["per-cell best · UCB + ledger + UI"], fill=WHITE)

    ys = [150, 314, 478, 642, 806, 970, 1134, 1298, 1462, 1626, 1790]
    for i in range(10):
        if i == 3:
            continue  # route→paradigm bypass drawn separately below
        s.arrow(250, ys[i] + 110, 250, ys[i + 1], color=SLATE_MID, label=None)
    s.label(250, 622, "90%", 19, TEAL)
    # paradigm bypass around the cheap-refinement box (right corridor, no crossings)
    s.raw(f'<path d="M 460 533 L 890 533 L 890 900 L 460 900" fill="none" stroke="{TEAL}" '
          f'stroke-width="2.4" marker-end="url(#a-{TEAL.lstrip("#")})"/>')
    s.label(675, 533, "10% · on stagnation", 19, TEAL)

    # Costs column (right of stages)
    costs = ["free", "free", "ledger", "free", "free", "free",
             "free", "free", "ledger-measured", "~$0.10 avg", "free"]
    for y, c in zip(ys, costs):
        s.label(480, y + 59, c, 18, INK4, anchor="start", mono=True)

    # duplicate rejects inside the novelty gate (see its second line); the trunk below is the continue loop
    # continue loop-back (outer right trunk)
    s.raw(f'<path d="M 460 1845 L 905 1845 L 905 369 L 460 369" fill="none" stroke="{TEAL}" '
          f'stroke-width="2.4" stroke-dasharray="10 7" marker-end="url(#a-{TEAL.lstrip("#")})"/>')
    s.label(600, 1250, "continue — the loop", 19, TEAL)

    # Stagnation exit stacked below
    s.arrow(250, 1900, 250, 1954, color=STONE, label=None)
    s.label(250, 1930, "stagnation", 18, STONE)
    s.box(40, 1954, 420, 150, "stagnation or budget", ["ΔS < ε for 30 evals", "∨ $25 · 250 evals · 12h"],
          fill=STONE_SOFT, edge=STONE, tsize=23)
    s.box(40, 2158, 420, 110, "full discovery", ["top candidate per cell"], fill=SLATE_SOFT, edge=SLATE, tsize=23)
    s.arrow(250, 2104, 250, 2158, color=SLATE_MID, label=None)
    s.box(40, 2322, 420, 110, "holdout", ["/finalize · ×1 · labels sealed"], fill=SLATE_SOFT, edge=SLATE, tsize=23)
    s.arrow(250, 2268, 250, 2322, color=SLATE_MID, label=None)
    s.box(40, 2486, 420, 110, "human decision", ["approve → deploy  |  rollback"], fill=STONE_SOFT, edge=STONE, tsize=23)
    s.arrow(250, 2432, 250, 2486, color=STONE, label=None)

    # Guardrail strip
    s.rect(40, 2650, 880, 120, fill=TERRA_SOFT, stroke=TERRA, sw=2, rx=14, node=False)
    s.label(480, 2692, "every candidate passes guardrails before judging:", 19, "#8A3B12", weight=600)
    s.label(480, 2724, "diff-scanner: vault / bench / scorer edits → reject · suppression check", 18, "#8A3B12")
    s.label(480, 2752, "canary hits · sandbox egress", 18, "#8A3B12")
    s.write("loop_evolution.svg")


# ══════════════════════════════════════════════════════════════════════════════
# 8. Full platform — Q: what does the whole platform look like?
# ══════════════════════════════════════════════════════════════════════════════
def hld_platform():
    s = Scene(960, 3150, "The platform — ten components, one outer loop",
              "Real-world signal in at the top, the evolution loop in the middle, deployment closing the loop.")

    # Sources 2x2
    s.label(480, 108, "PROOFREADER RUNS", 18, INK4, weight=700)
    src = ["documents", "runtime traces", "human corrections", "style guide sg_v4.2"]
    for i, t in enumerate(src):
        s.box(40 + (i % 2) * 450, 130 + (i // 2) * 92, 430, 72, t, (), fill=GRAY, edge=SLATE, tsize=20)
    for cx in (255, 705):
        s.arrow(cx, 294, cx, 330, color=SLATE_MID, lw=2)

    # Lake
    s.box(40, 330, 880, 150, "Context Lake ②", ["snapshots · traces", "docs + offsets", "feedback · nudges", "append-only"],
          fill=SLATE_SOFT, edge=SLATE, tsize=21)

    # Diagnose
    s.box(40, 520, 880, 130, "Diagnose M1", ["normalize → join", "→ dedup → cluster", "→ severity"],
          fill=WHITE, edge=SLATE, tsize=21)
    s.arrow(480, 480, 480, 520, color=SLATE_MID, label=None)

    # Issue cards
    s.box(40, 690, 880, 110, "issue cards", ["ISS-xxx + evidence"], fill=GRAY, edge=SLATE, tsize=21)
    s.arrow(480, 650, 480, 690, color=SLATE_MID, label=None)

    # Human triage
    s.box(40, 840, 880, 140, "Human triage ⑩", ["PM: defect / pref?", "Dev: feasible?", "G1 · G2"],
          fill=STONE_SOFT, edge=STONE, tsize=21)
    s.arrow(480, 800, 480, 840, color=SLATE_MID, label=None)
    # preference out + pathways below
    s.box(620, 1010, 300, 80, "do-not-optimize", [], fill=TERRA_SOFT, edge=TERRA, tsize=20)
    s.arrow(700, 980, 760, 1010, color=TERRA, dashed=True, label=None)
    s.label(835, 1002, "preference", 18, TERRA)
    s.box(40, 1010, 540, 140, "Pathways view ⑧", ["M2: pathways · seeds", "G3: user approval", "code + trace search"],
          fill=WHITE, edge=SLATE, tsize=21)
    s.arrow(300, 980, 300, 1010, color=SLATE_MID, label=None)

    # Orchestrator above loop
    s.box(40, 1190, 880, 90, "Orchestrator ⑦", ["Temporal + SQS · nudge queue · budget · stop rules"],
          fill=GRAY, edge=SLATE, tsize=20)
    s.arrow(480, 1150, 480, 1190, color=SLATE_MID, label=None)

    # EVOLUTION LOOP (visual center)
    s.rect(40, 1320, 880, 740, fill=TEAL_SOFT, stroke=TEAL, sw=3.5, rx=22, node=False)
    s.label(480, 1362, "EVOLUTION LOOP", 22, TEAL, weight=700)
    inner = [
        ("parent selection", ["softmax · novelty"], 1390),
        ("Mutation Router ⑥", ["90% small / 10% frontier"], 1516),
        ("App Adapter ①", ["run(doc) → spans[]", "sandbox · Bedrock proxy"], 1642),
        ("Evaluator Farm ④", ["smoke → judge → proxy"], 1768),
        ("Lineage Archive ⑤", ["MAP-Elites + ledger"], 1894),
    ]
    for t, subs, y in inner:
        s.box(60, y, 840, 96, t, subs, fill=WHITE, edge=TEAL, tsize=21)
    s.raw(f'<path d="M 905 1980 Q 915 1700 905 1420" fill="none" stroke="{TEAL}" '
          f'stroke-width="2.2" stroke-dasharray="8 6" marker-end="url(#a-{TEAL.lstrip("#")})"/>')
    s.arrow(480, 1280, 480, 1320, color=TEAL, lw=2.4, label=None)

    # Vault below loop
    s.box(40, 2100, 880, 120, "Benchmark Vault ③", ["/score · gated /finalize", "bench_ver pinned"],
          fill=SLATE_SOFT, edge=STONE, tsize=21, sw=3)
    s.arrow(480, 2060, 480, 2100, color=TEAL, dashed=True, label=None)
    s.label(540, 2082, "score", 18, TEAL)

    # WebUI bottom
    s.box(40, 2260, 880, 100, "WebUI ⑨", ["discovery tree · hillclimb", "$ burn · worker status"],
          fill=GRAY, edge=SLATE, tsize=21)
    s.arrow(480, 2220, 480, 2260, color=SLATE_MID, dashed=True, label=None)

    # Band: post-loop, top to bottom
    by = [2400, 2535, 2670, 2805, 2940]
    band = [
        ("top per-cell", ["finalists"], WHITE, SLATE),
        ("full discovery", ["~60–100 docs · finalists"], SLATE_SOFT, SLATE),
        ("holdout", ["×1 · /finalize · sealed"], SLATE_SOFT, SLATE),
        ("promotion gate ⑩", ["G4: owner + PM"], STONE_SOFT, STONE),
        ("deploy", ["versioned tag · rollback"], TEAL_SOFT, TEAL),
    ]
    for y, (t, subs, fill, edge) in zip(by, band):
        s.box(40, y, 880, 95, t, subs, fill=fill, edge=edge, tsize=21)
    s.arrow(480, 2360, 480, 2400, color=SLATE_MID, label=None)
    for i in range(4):
        s.arrow(480, by[i] + 95, 480, by[i + 1], color=SLATE_MID, label=None)

    # Closing notes
    s.label(480, 3080, "deployed runs feed new traces + feedback back into the lake — the outer loop (§13)", 18, TEAL)
    s.label(480, 3112, "①–⑩: ten components · slate=data · white=process · teal=evolution · stone=gate", 18, INK4)
    s.write("hld_platform.svg")


def main():
    os.makedirs(OUT, exist_ok=True)
    pipe_proofreader()
    flow_diagnose()
    ladder_eval()
    tree_lineage()
    vault_boundary()
    flow_gates()
    loop_evolution()
    hld_platform()


if __name__ == "__main__":
    main()
