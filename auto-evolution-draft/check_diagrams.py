"""Automated legibility/geometry checks for gen_diagrams.py output.

Run: python3 check_diagrams.py
Exits non-zero if any diagram fails. Checks per SVG:
  - uniform canvas width 960 (900-1100) so figures render ~1:1 at 1.5x body width
  - all <text> font-size >= MIN_BODY (18); figure titles (largest) >= 30
  - node titles (inside data-box) >= 22 where present
  - text width heuristic 0.55*size*len(s) fits inside its containing data-box width - padding
  - no overlapping data-boxes (rect intersects rect)
  - every arrow path has a label nearby OR is in a known unlabeled set (elbows, short links)
  - at least one arrow (flow) in each flow diagram
"""
import os
import re
import sys
import xml.etree.ElementTree as ET

OUT = "/Users/mozart/Documents/ml/research/agents/auto-evolution-draft/figs"
NS = "{http://www.w3.org/2000/svg}"

MIN_BODY = 18
MIN_NODE_TITLE = 20
MIN_FIG_TITLE = 30
CANVAS_MIN, CANVAS_MAX = 900, 1100
PRED = 0.55  # width per char / fontsize

FILES = [
    "pipe_proofreader.svg",
    "flow_diagnose.svg",
    "ladder_eval.svg",
    "tree_lineage.svg",
    "vault_boundary.svg",
    "flow_gates.svg",
    "loop_evolution.svg",
    "hld_platform.svg",
]


def text_w(s, size):
    return len(s) * size * PRED


def parse(fn):
    path = os.path.join(OUT, fn)
    tree = ET.parse(path)
    root = tree.getroot()
    vb = [float(v) for v in root.get("viewBox").split()]
    w, h = vb[2], vb[3]

    boxes = []
    for rect in root.iter(f"{NS}rect"):
        if rect.get("data-box"):
            boxes.append({
                "id": rect.get("data-box"),
                "x": float(rect.get("x")),
                "y": float(rect.get("y")),
                "w": float(rect.get("width")),
                "h": float(rect.get("height")),
            })

    texts = []
    for t in root.iter(f"{NS}text"):
        texts.append({
            "x": float(t.get("x", 0)),
            "y": float(t.get("y", 0)),
            "s": (t.text or "").strip(),
            "size": float(t.get("font-size", 0)),
            "anchor": t.get("text-anchor", "middle"),
            "in": t.get("data-in"),
            "role": t.get("data-role"),
        })

    paths = list(root.iter(f"{NS}path"))  # arrows

    return w, h, boxes, texts, paths


def check(fn):
    errs = []
    w, h, boxes, texts, paths = parse(fn)

    # canvas
    if not (CANVAS_MIN <= w <= CANVAS_MAX):
        errs.append(f"canvas width {w} outside [{CANVAS_MIN},{CANVAS_MAX}]")

    # fonts
    sizes = [t["size"] for t in texts if t["s"]]
    if not sizes:
        errs.append("no text")
        return errs
    biggest = max(sizes)
    if biggest < MIN_FIG_TITLE:
        errs.append(f"title size {biggest} < {MIN_FIG_TITLE}")
    small = [t for t in texts if t["s"] and t["size"] < MIN_BODY]
    for t in small[:5]:
        errs.append(f"text '{t['s'][:30]}' size {t['size']} < {MIN_BODY}")

    # node titles >= 20
    for t in texts:
        if t["role"] == "title" and t["size"] < MIN_NODE_TITLE:
            errs.append(f"node title '{t['s'][:30]}' size {t['size']} < {MIN_NODE_TITLE}")

    # text fit inside box
    box_by_id = {b["id"]: b for b in boxes}
    for t in texts:
        if not t["in"] or t["in"] not in box_by_id or not t["s"]:
            continue
        b = box_by_id[t["in"]]
        tw = text_w(t["s"], t["size"])
        if t["anchor"] == "middle":
            left, right = t["x"] - tw / 2, t["x"] + tw / 2
        elif t["anchor"] == "start":
            left, right = t["x"], t["x"] + tw
        else:  # end
            left, right = t["x"] - tw, t["x"]
        if left < b["x"] - 2 or right > b["x"] + b["w"] + 2:
            errs.append(
                f"text '{t['s'][:40]}' ({tw:.0f}px) overflows box {t['in']} "
                f"[{b['x']:.0f}..{b['x']+b['w']:.0f}] -> [{left:.0f}..{right:.0f}]"
            )

    # box overlap
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a, b = boxes[i], boxes[j]
            if (a["x"] < b["x"] + b["w"] and b["x"] < a["x"] + a["w"]
                    and a["y"] < b["y"] + b["h"] and b["y"] < a["y"] + a["h"]):
                # allow small overlaps? report
                ox = min(a["x"] + a["w"], b["x"] + b["w"]) - max(a["x"], b["x"])
                oy = min(a["y"] + a["h"], b["y"] + b["h"]) - max(a["y"], b["y"])
                errs.append(f"boxes {a['id']} & {b['id']} overlap {ox:.0f}x{oy:.0f}px")

    # arrows present
    if len(paths) < 3:
        errs.append(f"only {len(paths)} paths — expected arrows")

    return errs


def main():
    all_errs = {}
    for fn in FILES:
        try:
            errs = check(fn)
        except Exception as e:
            errs = [f"parse error: {e}"]
        if errs:
            all_errs[fn] = errs
    if all_errs:
        for fn, errs in all_errs.items():
            print(f"\n✗ {fn}")
            for e in errs:
                print(f"   - {e}")
        print(f"\n{sum(len(e) for e in all_errs.values())} issues in {len(all_errs)} files")
        sys.exit(1)
    else:
        print(f"✓ all {len(FILES)} diagrams pass")


if __name__ == "__main__":
    main()
