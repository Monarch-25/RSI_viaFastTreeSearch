"""Generate a native .excalidraw HLD scene for the auto-evolution platform.

Palette matches research_draft.md v0.4 style standard:
  slate #3B4F66 / ink #1F3349, teal #2F6B57 / #E7F0EB, stone #7A6420 / #F7F0DF.
Validates itself by rendering PNG+SVG through `mcp-excalidraw-server render`.
"""
import json
import subprocess

NAVY = "#1F3349"
SLATE_EDGE = "#3B4F66"
TEAL_EDGE = "#2F6B57"
STONE_EDGE = "#7A6420"
F_SLATE = "#E9EEF3"
F_WHITE = "#F4F6F8"
F_TEAL = "#E7F0EB"
F_STONE = "#F7F0DF"

_ids = iter(f"el{i:03d}" for i in range(1000))


def rect(x, y, w, h, fill, edge, width=2):
    return {
        "id": next(_ids), "type": "rectangle", "x": x, "y": y,
        "width": w, "height": h, "angle": 0,
        "strokeColor": edge, "backgroundColor": fill,
        "fillStyle": "solid", "strokeWidth": width,
        "strokeStyle": "solid", "roughness": 0, "opacity": 100,
        "groupIds": [], "frameId": None, "roundness": {"type": 3},
        "boundElements": [], "link": None, "locked": False,
        "seed": 1, "version": 1, "versionNonce": 1,
        "updated": 1, "isDeleted": False,
    }


def text(x, y, content, size, color=NAVY, align="center"):
    lines = content.split("\n")
    longest = max(len(l) for l in lines)
    w = longest * size * 0.55 + 20
    lh = size * 1.3
    h = len(lines) * lh + 8
    if align == "center":
        x = x - w / 2
    return {
        "id": next(_ids), "type": "text", "x": round(x), "y": round(y),
        "width": round(w), "height": round(h), "angle": 0,
        "strokeColor": color, "backgroundColor": "transparent",
        "fillStyle": "solid", "strokeWidth": 1,
        "strokeStyle": "solid", "roughness": 0, "opacity": 100,
        "groupIds": [], "frameId": None, "roundness": None,
        "boundElements": [], "link": None, "locked": False,
        "seed": 1, "version": 1, "versionNonce": 1,
        "updated": 1, "isDeleted": False,
        "fontSize": size, "fontFamily": 2, "text": content,
        "textAlign": align, "verticalAlign": "top",
        "baseline": round(h - 8), "containerId": None,
        "originalText": content, "autoResize": True,
        "lineHeight": 1.3,
    }


def arrow(x0, y0, x1, y1, color=NAVY, dashed=False, width=2, head=True):
    return {
        "id": next(_ids), "type": "arrow", "x": x0, "y": y0,
        "width": abs(x1 - x0) or 1, "height": abs(y1 - y0) or 1,
        "angle": 0, "strokeColor": color, "backgroundColor": "transparent",
        "fillStyle": "solid", "strokeWidth": width,
        "strokeStyle": "dashed" if dashed else "solid",
        "roughness": 0, "opacity": 100,
        "groupIds": [], "frameId": None, "roundness": {"type": 2},
        "boundElements": [], "link": None, "locked": False,
        "seed": 1, "version": 1, "versionNonce": 1,
        "updated": 1, "isDeleted": False,
        "points": [[0, 0], [x1 - x0, y1 - y0]],
        "lastCommittedPoint": None,
        "startBinding": None, "endBinding": None,
        "startArrowhead": None, "endArrowhead": "arrow" if head else None,
        "elbowed": False,
    }


def labeled_box(cx, top, w, h, title, body_lines, fill, edge, width=2):
    els = [rect(round(cx - w / 2), top, w, h, fill, edge, width)]
    t = text(cx, top + 18, title, 22)
    els.append(t)
    y = top + 18 + t["height"] + 10
    for line in body_lines:
        tl = text(cx, y, line, 16)
        els.append(tl)
        y += tl["height"] + 2
    return els


els = []
# Title
els.append(text(860, 24, "Auto-Evolution Platform — HLD (proofreader pilot, bench_v7)", 30))
els.append(text(860, 78, "Context Lake  →  Control  →  Sandboxed Evolution  →  Human Plane", 18, color=SLATE_EDGE))

# Row 1: four planes
ROW1, H1 = 130, 300
planes = [
    (215, "A. Context Lake", ["snapshot (git SHA + image)", "LangSmith + Bedrock traces", "feedback CSV + docs + offsets", "style guide sg_v4.2"], F_SLATE, SLATE_EDGE),
    (645, "B. Control", ["orchestrator (Temporal)", "nudge queue (SQS)", "MAP-Elites archive", "cost ledger"], F_WHITE, SLATE_EDGE),
    (1080, "C. Evolution (sandbox)", ["adapter API run(doc)→spans", "router: 90% small / 10% frontier", "evaluator farm (smoke→proxy)", "VAULT read-only"], F_TEAL, TEAL_EDGE),
    (1510, "D. Human", ["WebUI: pathways + tree", "hillclimb + cost dashboard", "PM / Dev / promote gates"], F_STONE, STONE_EDGE),
]
for cx, title, body, fill, edge in planes:
    els += labeled_box(cx, ROW1, 370 if cx < 1400 else 360, H1, title, body, fill, edge)

mid1 = ROW1 + H1 // 2
for x0, x1 in [(400, 460), (830, 890), (1270, 1330)]:
    els.append(arrow(x0, mid1, x1, mid1))

# Row 2: module spine
ROW2, H2 = 490, 150
spine = [
    (215, "M1 Diagnose", ["normalize → join → dedup", "severity → issue cards"], F_WHITE, SLATE_EDGE),
    (645, "Gate: PM / Dev", ["defect vs preference", "feasible?"], F_STONE, STONE_EDGE),
    (1080, "M2 SearchCtx", ["pathways + seeds", "MCP connectors"], F_WHITE, SLATE_EDGE),
    (1510, "M3 Score / Re-evolve", ["proxy → full → holdout", "human-gated finalize"], F_WHITE, SLATE_EDGE),
]
for cx, title, body, fill, edge in spine:
    els += labeled_box(cx, ROW2, 370 if cx < 1400 else 360, H2, title, body, fill, edge, width=2)

mid2 = ROW2 + H2 // 2
for x0, x1 in [(400, 460), (830, 890), (1270, 1330)]:
    els.append(arrow(x0, mid2, x1, mid2))

# Vault (under D, aligned right)
els += labeled_box(1510, 700, 360, 170, "Benchmark Vault (RO)", ["discovery + holdout", "/score + /finalize", "agent cannot write"], F_SLATE, SLATE_EDGE, width=3)
# Elbow (dashed teal): out of C's right side, around the Human plane, into Vault's right edge
els.append(arrow(1270, 460, 1740, 460, color=TEAL_EDGE, dashed=True, head=False))
els.append(arrow(1740, 460, 1740, 805, color=TEAL_EDGE, dashed=True, head=False))
els.append(arrow(1740, 805, 1694, 805, color=TEAL_EDGE, dashed=True, head=True))
els.append(text(1792, 620, "score()", 15, color=TEAL_EDGE))
# Short dashed link: Vault top -> M3 bottom (finalize feeds promotion)
els.append(arrow(1450, 700, 1450, ROW2 + H2, color=STONE_EDGE, dashed=True, head=True))
els.append(text(1380, 662, "finalize", 15, color=STONE_EDGE))

# Footer
els.append(text(860, 900, "Every new evolution run and every promotion requires human approval.", 16, color=SLATE_EDGE))

scene = {
    "type": "excalidraw",
    "version": 2,
    "source": "auto-evolution-draft/gen_excalidraw.py",
    "elements": els,
    "appState": {"theme": "light", "viewBackgroundColor": "#ffffff", "gridSize": None},
    "files": {},
}

OUT = "/Users/mozart/Documents/ml/research/agents/auto-evolution-draft/auto-evolution-hld.excalidraw"
with open(OUT, "w") as f:
    json.dump(scene, f, indent=1)
print(f"wrote {OUT} with {len(els)} elements")

for fmt, path in [("png", OUT.replace(".excalidraw", ".png")),
                  ("svg", OUT.replace(".excalidraw", ".svg"))]:
    r = subprocess.run(
        ["npx", "-y", "mcp-excalidraw-server", "render", OUT,
         "--out", path, "--format", fmt, "--scale", "2"],
        capture_output=True, text=True, timeout=180,
        cwd="/Users/mozart/Documents/ml/research/agents",
    )
    print(fmt, "rc=", r.returncode)
    if r.returncode != 0:
        print(r.stderr[-2000:])
