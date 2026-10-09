---
name: proofreader-dataset-builder
description: Builds a high-quality synthetic benchmark dataset for a document proofreading task via controlled error injection. Use when asked to create proofreading eval data, inject style-guide violations into documents, verify span labels, render PDFs with highlight anchors, or freeze a bench version. Triggers on: build dataset, synthetic benchmark, inject errors, proofreader eval data, span labels, bench freeze.
---

# Proofreader Dataset Builder

Generates a **synthetic benchmark dataset** for document proofreading: clean documents → controlled injection of exactly-specified style-guide violations → independent verification → PDF rendering with highlight anchors → distractor/minimal-pair construction → QC-gated freeze. Grounded in frontier dataset-synthesis practice: typed error injection with one-error-per-item control (SynCED-EnDe, Chopra et al. 2025), two-step generate-then-judge with a *different* model family (CoPrUS, Steindl et al. 2025), cross-family verifier gain over self-verification (Agentic Learning AI Lab, 37-model study), and explicit label-provenance tiers.

## 0. Read first (inputs you must locate)

| Input | Where | What to extract |
|---|---|---|
| Rule taxonomy + preferences | `RULE_TAXONOMY_MD` (markdown in the main codebase — ask the user for its path if unset) | Every `rule_id`, its definition, severity, deterministic-vs-semantic flag, 1–2 exemplar violations per rule |
| Clean corpus | `CLEAN_CORPUS_DIR` (human-written, style-guide-compliant `.txt`/`.md`; ask if unset) | Base passages. Must be deduplicated and post-cutoff if possible to limit pretraining overlap |
| Output dir | `OUT_DIR` (default `./bench/`) | All artifacts below land here, versioned by `BENCH_VER` |

**Model separation (non-negotiable):** `INJECTOR_MODEL` and `VERIFIER_MODEL` must come from **different model families/vendors**. Self-verification and same-family verification systematically accept the injector's own mistakes (higher false-positive rate correlates with solution-distribution similarity). If only one family is available, the verifier must be a deterministic oracle plus mandatory human audit at 3× the normal sampling rate.

## 1. Setup

```bash
pip install -r requirements.txt   # pymupdf, reportlab, jsonschema, numpy
export INJECTOR_MODEL="..." VERIFIER_MODEL="..."   # different families
export RULE_TAXONOMY_MD="path/to/style-taxonomy.md" CLEAN_CORPUS_DIR="path/to/clean/" OUT_DIR="./bench/"
python scripts/validate_item.py --help   # schema + offset + PDF-anchor checker
```

## 2. Output schema (one JSON object per line in `items.jsonl`)

```json
{
  "item_id": "trad_0147",
  "doc_id": "doc_marketing_022",
  "split": "discovery | holdout | canary",
  "pdf_uri": "pdfs/doc_marketing_022.pdf",
  "passage_id": "p03",
  "clean_text": "Acme announced...",
  "injected_text": "Acme(TM) announced...",
  "spans": [{
    "char_start": 0, "char_end": 8,
    "surface": "Acme(TM)",
    "rule_id": "trademark.registered@sg_v4.2",
    "severity": 1,
    "suggestion": "Acme®",
    "suggestion_alternatives": ["Acme (registered trademark)"],
    "wrong_suggestions": ["Acme™"],
    "highlight_anchor": {"page": 1, "x0": 72.0, "y0": 700.0, "x1": 130.5, "y1": 712.0},
    "error_class": "FN_target | FP_distractor | minimal_pair_mate"
  }],
  "is_distractor": false,
  "minimal_pair_id": "trad_0147_mate",
  "obviousness": 3, "localization_complexity": 1, "contextual_dependency": 2,
  "injector": {"model": "...", "prompt_hash": "...", "seed": 7},
  "verifier": {"model_or_oracle": "...", "rounds": 3, "verdict": "accept", "scores": [5, 4, 5]},
  "provenance": "silver | gold",
  "qc": {"anchor_resolved": true, "dedup_nearest_cosine": 0.61}
}
```

Rules: `char_start/char_end` index into `injected_text`; every span carries exactly one `rule_id@style_guide_version`; distractors have empty `spans` and `is_distractor: true`; every row carries `provenance` (`gold` = human-audited, `silver` = 3-round model-verified, never anything weaker on holdout).

## 3. Pipeline (execute in order, no skipping)

### Stage 1 — Freeze the taxonomy
Parse `RULE_TAXONOMY_MD` into `taxonomy.json`: `[{rule_id, family, definition, severity, deterministic: bool, oracle: regex|gazetteer|null, exemplars: [...] }]`. Flag every rule as **oracle-first** (datetime format, trademark list, units, capitalization) or **model-judged** (semantics, tone, clarity). Oracles are code, not prompts — write them now, unit-test them now. Ambiguous rules go to `adjudication_log.md` with a single recorded decision each; the agent must not re-litigate them per item.

### Stage 2 — Prepare the clean corpus
Deduplicate (SHA-256 + embedding near-dup removal, cosine > 0.92), filter to compliant passages (run oracles over them; any hit = quarantine, not silent keep), and tag triggers per passage: `has_ner, has_num, has_date, has_trademark_candidate, domain`. Keep passage length 60–200 words; record `source, date, hash` per passage for the freshness/overlap audit.

### Stage 3 — Coverage-driven sampling
Build the matrix `rule × domain × density{single,multi} × {target, distractor, minimal_pair}`. Sample without replacement until every cell hits quota (default: ≥8 discovery + ≥4 holdout items per rule). Assign splits **by document** — never split passages of one doc across discovery/holdout. Reserve 2–5% of holdout as canaries (unique nonsense marks, e.g. `Zxqpl®`, recorded in a sealed file).

### Stage 4 — Inject (INJECTOR_MODEL, low temperature, diff contract)
One controlled error per target item. The injector returns a unified diff plus claimed spans — never a free-written document (free writing produces stereotyped, too-clean errors that flatter detectors). Use the prompt in §4. Multi-error items: apply sequentially, re-verifying after each edit so errors don't collide or cancel. Randomize topic/domain framing per call (zero-shot topic variation beats fixed prompts on diversity); ground with 1–2 exemplars from the taxonomy so output stays on-task.

### Stage 5 — Verify (oracle first, then VERIFIER_MODEL, 3 rounds, reject on doubt)
1. Oracle pass: deterministic rules checked by code. Fail = reject.
2. Model pass, 3 independent rounds with the rubric in §4: accept iff all rounds score ≥4/5 on *correct-span, only-these-spans, rule-match*. Any round ≤3 = reject (not repair — rejection sampling, not self-correction loops).
3. Budget 20–40% rejection; if rejections fall below 10%, your verifier is too lenient — tighten, don't celebrate.
4. Distractors verified in reverse: model + oracle must confirm the passage is genuinely CLEAN under all rules.

### Stage 6 — Render PDFs + resolve anchors
Render each doc to PDF (reportlab or HTML→PDF; embed the full text layer, no scanned images). Extract per-span coordinates with pymupdf word search on the exact surface; an anchor resolves only if the surface matches the text layer verbatim at one location. Unresolvable anchors → item rejected (this is ground-truth `highlight_fail` prevention, not a warning to ignore).

### Stage 7 — Minimal pairs + distractors
For ≥30% of targets, emit the clean mate (same passage, no injection, empty spans, linked by `minimal_pair_id`). Distractor quota: ≥25% of the split must be clean-but-tricky (near-miss phrasing, quoted code containing datetimes, unregistered marks used correctly). A benchmark without distractors measures recall only.

### Stage 8 — QC gates + freeze
Compute and record in `bench_report.md`: per-rule counts, verifier round agreement, embedding diversity (mean pairwise cosine, target <0.75), human spot-audit κ (sample 10–15% stratified + 100% of canaries and adjudications; ship-gate κ ≥ 0.75 on spans+rules), anchor resolvability (gate ≥99%), train/holdout doc overlap = 0, rejection rate. Then freeze: `BENCH_VER` tag, SHA-256 of `items.jsonl`, sealed canary file. Holdout labels never enter any prompt, log, or commit message after this point.

## 4. Prompts (copy, fill `{slots}`, log `prompt_hash` per call)

**Injector** (temperature 0.2–0.4):
```
You are a dataset generator for document proofreading evaluation.
RULE: {rule_id} — {rule_definition}. CORRECT EXAMPLE: {exemplar_ok}. VIOLATED EXAMPLE: {exemplar_bad}.
Given the CLEAN PASSAGE below, rewrite it to introduce EXACTLY ONE violation of this rule and no other
style-guide violation. Preserve all other content, facts, names, and numbers. Return: (1) the full rewritten
passage, (2) a unified diff vs the original, (3) the exact violating surface string(s) and character offsets
in your rewritten passage. Do not explain.
CLEAN PASSAGE: {passage}
```

**Verifier** (temperature 0, 3 independent rounds, different family from injector):
```
You are a strict annotator. RULE: {rule_id} — {rule_definition}.
PASSAGE: {injected_text}. CLAIMED SPANS: {spans with offsets}.
Answer: (a) does each claimed span violate exactly this rule? (b) does ANY other span in the passage
violate ANY rule in {taxonomy_summary}? Score 1-5: 5 = claimed spans exactly right and nothing else wrong;
3 = right rule but span boundary off or an extra/missed violation; 1 = wrong rule or clean passage.
Return only: score + one-line reason.
```
Accept iff all three rounds ≥4. For distractors, same prompt over the clean passage; accept iff all rounds confirm no violation (score 5 = clean).

## 5. Oracles before models (write code, not prompts, for these)

`datetime_format` (regex per allowed/prohibited pattern + section-scope check), `trademark.registered` (gazetteer: approved-mark list + first-mention detector + ®/™/(TM) normalizer), `units_spacing`, `capitalization_headings`. Each oracle ships with 20+ unit tests including adversarial cases (datetimes inside code quotes, marks in URLs, hyphenated compounds). Model judgment is allowed ONLY for rules with no decidable oracle — and those items get 100% human audit on holdout.

## 6. Diversity, leakage, freshness controls

- Topic/domain randomization per injection call; embedding dedup (reject items with nearest-neighbor cosine > 0.88 to any accepted item).
- Hash every base passage against known pretraining-era corpora where feasible; prefer recent sources; record publish dates.
- Prompt-leakage check: injected text must not contain taxonomy wording verbatim.
- Split hygiene: no doc, passage, or near-dup across discovery/holdout; canary file sealed with restricted read access.

## 7. Definition of done

`items.jsonl` + `pdfs/` + `taxonomy.json` + `adjudication_log.md` + `bench_report.md` (all gates green) + `validate_item.py` clean on 100% of rows + frozen `BENCH_VER` tag. Report to the user: per-rule counts, rejection rate, audit κ, anchor rate, and any taxonomy ambiguities needing THEIR decision (the agent decides nothing ambiguous alone).

## 8. Anti-patterns (do not do these)

Single-model generate-and-verify; free-writing documents instead of diff-contract edits; accepting verifier round scores ≤3; splitting one document across discovery/holdout; rendering PDFs without verifying the text layer; shipping without distractors or minimal pairs; stamping anything weaker than 3-round verification as holdout; re-prompting a rejected item until it passes (re-sample instead).
