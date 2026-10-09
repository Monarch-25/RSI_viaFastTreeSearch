"""Validate one dataset item: schema, offsets, and PDF anchor resolvability.

Usage:
    python scripts/validate_item.py --item items.jsonl --line 12 --pdf-dir ./bench/pdfs
    python scripts/validate_item.py --item items.jsonl --all --pdf-dir ./bench/pdfs
"""
import argparse
import json
import sys

REQUIRED_TOP = {"item_id", "doc_id", "split", "pdf_uri", "injected_text",
                "spans", "is_distractor", "provenance", "injector", "verifier"}
REQUIRED_SPAN = {"char_start", "char_end", "surface", "rule_id",
                 "severity", "suggestion", "highlight_anchor"}


def check_item(it, pdf_dir=None):
    errors = []
    missing = REQUIRED_TOP - set(it)
    if missing:
        errors.append(f"missing top-level keys: {sorted(missing)}")
        return errors
    text = it.get("injected_text", "")
    if it["split"] not in {"discovery", "holdout", "canary"}:
        errors.append(f"bad split: {it['split']}")
    if it["provenance"] not in {"gold", "silver"}:
        errors.append(f"bad provenance: {it['provenance']} (must be gold|silver)")
    if it.get("is_distractor") and it.get("spans"):
        errors.append("distractor must have empty spans")
    for i, s in enumerate(it.get("spans", [])):
        m = REQUIRED_SPAN - set(s)
        if m:
            errors.append(f"span {i}: missing {sorted(m)}")
            continue
        a, b = s["char_start"], s["char_end"]
        if not (0 <= a < b <= len(text)):
            errors.append(f"span {i}: offsets [{a},{b}) out of bounds (len={len(text)})")
        elif text[a:b] != s["surface"]:
            errors.append(f"span {i}: surface mismatch: text has {text[a:b]!r}, label says {s['surface']!r}")
        if "@" not in s.get("rule_id", ""):
            errors.append(f"span {i}: rule_id must be pinned as rule@sg_ver")
        anch = s.get("highlight_anchor") or {}
        if not {"page", "x0", "y0", "x1", "y1"} <= set(anch):
            errors.append(f"span {i}: incomplete highlight_anchor")
    if pdf_dir and it.get("spans"):
        errors.extend(check_pdf_anchors(it, pdf_dir))
    return errors


def check_pdf_anchors(it, pdf_dir):
    try:
        import fitz
    except ImportError:
        return ["pymupdf not installed; cannot verify PDF anchors"]
    import os
    errors = []
    path = os.path.join(pdf_dir, os.path.basename(it["pdf_uri"]))
    if not os.path.exists(path):
        return [f"pdf not found: {path}"]
    try:
        doc = fitz.open(path)
    except Exception as e:  # noqa: BLE001
        return [f"cannot open pdf: {e}"]
    for i, s in enumerate(it["spans"]):
        page_no = s["highlight_anchor"]["page"] - 1
        if not (0 <= page_no < len(doc)):
            errors.append(f"span {i}: page {page_no + 1} out of range ({len(doc)} pages)")
            continue
        hits = doc[page_no].search_for(s["surface"])
        if not hits:
            errors.append(f"span {i}: surface {s['surface']!r} not found in PDF text layer (p{page_no + 1})")
        elif len(hits) > 1:
            errors.append(f"span {i}: surface occurs {len(hits)}x on p{page_no + 1} (ambiguous anchor)")
    doc.close()
    return errors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--item", required=True)
    ap.add_argument("--line", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--pdf-dir", default=None)
    args = ap.parse_args()

    with open(args.item) as f:
        lines = [ln for ln in f if ln.strip()]
    idxs = range(len(lines)) if args.all else [args.line or 0]
    failed = 0
    for n in idxs:
        it = json.loads(lines[n])
        errs = check_item(it, args.pdf_dir)
        status = "OK " if not errs else "FAIL"
        print(f"[{status}] line {n} item_id={it.get('item_id')}")
        for e in errs:
            print(f"       - {e}")
        failed += bool(errs)
    print(f"\n{len(list(idxs)) - failed}/{len(list(idxs))} valid")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
