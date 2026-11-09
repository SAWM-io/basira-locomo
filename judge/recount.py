"""Recount the LoCoMo results of SAWM & Basira Liquid Memory from the published graded answers.

No dependencies, no network calls, no key: the script reads the verdicts written by the judges,
question by question, and reproduces every figure in the README.

Usage:
  python3 -I recount.py                      # reads ../answers/*.jsonl
  python3 -I recount.py ../answers/recall-320_opus-5.5_judge-pass1.jsonl

Counting rules (identical to those of the protocol):
  - main score: questions in categories 1 to 4 (1,540 questions), as with the other providers;
  - category 5 (adversarial questions: recognizing that something was never said): measured separately, with
    the abstention judge; the two questions from conversation 26 reported in issue #43 of the LoCoMo repository
    ("excluded" field) are left out, i.e. 444 questions out of 446;
  - context: median, over the questions in categories 1 to 4, of the tokens given to the reader.
"""
from __future__ import annotations

import glob
import json
import math
import statistics
import sys
from pathlib import Path

CATEGORIES = {1: "multi-hop", 2: "temporal", 3: "open-domain", 4: "single-hop"}
JUDGES = {"j": "Mem0 J judge", "strict": "strict GPT-4o judge (LongMemEval)"}


def read(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def pct(k: int, n: int) -> str:
    return f"{100 * k / n:.2f}%"


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return 100 * (c - m), 100 * (c + m)


def mcnemar_exact(only_1: int, only_2: int) -> float:
    """Exact McNemar test (two-sided binomial) on the discordant pairs."""
    n, k = only_1 + only_2, min(only_1, only_2)
    if n == 0:
        return 1.0
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)


def p_txt(p: float) -> str:
    return "< 0.001" if p < 0.001 else f"= {p:.2f}"


def check(entries: list[dict], f: str) -> None:
    ids = [e["question_id"] for e in entries]
    if len(ids) != len(set(ids)):
        raise SystemExit(f"{f}: duplicate question_id.")


def count(entries: list[dict], judge: str, cats=(1, 2, 3, 4)):
    rows = [e for e in entries if e["category"] in cats and judge in e["judges"] and not e.get("excluded")]
    return sum(1 for e in rows if e["judges"][judge]["verdict"]), len(rows)


def report(f: Path) -> dict[str, dict[str, bool]]:
    entries = read(f)
    check(entries, f.name)
    print(f"\n{f.name}")
    models = sorted({v["model"] for e in entries for v in e["judges"].values()})
    print(f"  judges: {', '.join(models)}")
    for judge, name in JUDGES.items():
        k, n = count(entries, judge)
        lo, hi = wilson(k, n)
        print(f"  {name}: {k}/{n} = {pct(k, n)}  (Wilson 95%: {lo:.2f} - {hi:.2f})")
        per = []
        for c, label in CATEGORIES.items():
            kc, nc = count(entries, judge, (c,))
            per.append(f"{label} {pct(kc, nc)} ({nc})")
        print("    by category: " + "; ".join(per))
    k5, n5 = count(entries, "abstention", (5,))
    if n5:
        print(f"  Category 5 (adversarial questions), abstention judge: {k5}/{n5} = {pct(k5, n5)}")
    ctx = [e["context_tokens"] for e in entries if e["category"] in CATEGORIES]
    share = [e["conversation_fraction"] for e in entries if e["category"] in CATEGORIES]
    print(f"  median context: {statistics.median(ctx):,.0f} tokens"
          + f" ({100 * statistics.median(share):.0f}% of the conversation)")
    # Questions for which ALL official evidence turns (the dataset's evidence field) are among the returned memories.
    cov = [e["all_evidence_returned"] for e in entries
           if e["category"] in CATEGORIES and e.get("all_evidence_returned") is not None]
    if cov:
        print(f"  all evidence returned by the memory: {sum(cov)}/{len(cov)} = {pct(sum(cov), len(cov))}")
    return {j: {e["question_id"]: e["judges"][j]["verdict"] for e in entries
                if e["category"] in CATEGORIES and j in e["judges"]} for j in JUDGES}


def comparison(b: dict, c: dict, n_pass: int) -> None:
    for judge, name in JUDGES.items():
        ids = sorted(set(b[judge]) & set(c[judge]))
        kb = sum(b[judge][i] for i in ids)
        kc = sum(c[judge][i] for i in ids)
        s1 = sum(1 for i in ids if b[judge][i] and not c[judge][i])
        s2 = sum(1 for i in ids if c[judge][i] and not b[judge][i])
        gap = 100 * (kb - kc) / len(ids)
        print(f"  pass {n_pass}, {name}, {len(ids)} shared questions: memory {kb} ({pct(kb, len(ids))}), "
              f"full conversation {kc} ({pct(kc, len(ids))}), gap {gap:+.1f} points, "
              f"p {p_txt(mcnemar_exact(s1, s2))} (exact McNemar, {s1} / {s2} discordant)")


def main() -> None:
    args = sys.argv[1:]
    files = sorted(args or glob.glob(str(Path(__file__).resolve().parent.parent / "answers" / "*.jsonl")))
    if not files:
        raise SystemExit("No answer files.")
    verdicts = {}
    for f in files:
        verdicts[Path(f).name] = report(Path(f))
    for base, title in (("recall-320", "recall of up to 320 memories"), ("recall-160", "recall of up to 160 memories")):
        for n_pass in (1, 2):
            b = verdicts.get(f"{base}_opus-5.5_judge-pass{n_pass}.jsonl")
            c = verdicts.get(f"full-conversation-310_opus-5.5_judge-pass{n_pass}.jsonl")
            if b and c:
                if n_pass == 1:
                    print(f"\nComparison with the full conversation (same questions, {title}):")
                comparison(b, c, n_pass)


if __name__ == "__main__":
    main()
