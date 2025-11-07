script = r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
doc_audit.py — One-file document quality auditor for DOCX/PDF/TXT.
Generates an issues report and a 0–100 score based on grammar, style, readability and consistency checks.

USAGE:
    python doc_audit.py /path/to/document.docx --lang en-US --out /path/to/report_prefix

OUTPUTS:
    - <prefix>_report.json   (machine-readable findings & scores)
    - <prefix>_report.md     (human-readable summary)
    - prints a compact summary to stdout

OPTIONAL DEPENDENCIES (install what you need):
    pip install python-docx pdfminer.six PyPDF2 language-tool-python textstat

NOTES:
    - If language_tool_python is installed, a local LanguageTool server will be started automatically.
      For best performance, ensure Java is installed.
    - If both pdfminer and PyPDF2 are available, pdfminer is preferred for text extraction.
"""

import argparse
import json
import math
import os
import re
import statistics
import sys
import unicodedata
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, Tuple

# Optional imports
try:
    import docx  # python-docx
except Exception:
    docx = None

try:
    from pdfminer.high_level import extract_text as pdfminer_extract_text
except Exception:
    pdfminer_extract_text = None

try:
    import PyPDF2
except Exception:
    PyPDF2 = None

try:
    import language_tool_python  # grammar/spelling/style (rules-based)
except Exception:
    language_tool_python = None

try:
    import textstat  # readability
except Exception:
    textstat = None


# -----------------------------
# Data structures
# -----------------------------

@dataclass
class Issue:
    check: str
    message: str
    location: Optional[str] = None  # e.g., "Line 42" or a short snippet

@dataclass
class CheckResult:
    name: str
    score: float
    max_score: float
    issues: List[Issue]
    metrics: Dict[str, Any]

@dataclass
class AuditReport:
    file_path: str
    language: str
    total_score: float
    check_results: List[CheckResult]
    summary: Dict[str, Any]


# -----------------------------
# Helpers
# -----------------------------

def read_text_from_file(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    if ext in [".txt", ".md"]:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    if ext == ".docx":
        if docx is None:
            raise RuntimeError("python-docx is required to read .docx files. Install with: pip install python-docx")
        return _read_docx(file_path)
    if ext == ".pdf":
        return _read_pdf(file_path)
    # Attempt to read as text fallback
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def _read_docx(file_path: str) -> str:
    d = docx.Document(file_path)
    parts = []
    for p in d.paragraphs:
        parts.append(p.text)
    # Include simple table cell extraction
    for t in d.tables:
        for row in t.rows:
            cells = [c.text for c in row.cells]
            if any(cells):
                parts.append(" | ".join(cells))
    return "\n".join(parts)

def _read_pdf(file_path: str) -> str:
    # Prefer pdfminer if available (better text extraction)
    if pdfminer_extract_text is not None:
        try:
            return pdfminer_extract_text(file_path) or ""
        except Exception:
            pass
    # Fallback to PyPDF2
    if PyPDF2 is None:
        raise RuntimeError(
            "Reading PDFs requires either pdfminer.six or PyPDF2. Install with: pip install pdfminer.six or pip install PyPDF2"
        )
    text = []
    with open(file_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for i, page in enumerate(reader.pages):
            try:
                text.append(page.extract_text() or "")
            except Exception:
                continue
    return "\n".join(text)


def normalize_text(text: str) -> str:
    # Normalize unicode, standardize line breaks, collapse trailing spaces
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+\n", "\n", text)  # strip trailing spaces before newline
    return text


def split_sentences(text: str) -> List[str]:
    # Simple sentence splitter (avoid heavy deps). Not perfect but serviceable.
    # Split on ., !, ? while respecting common abbreviations.
    # We also split on line breaks when they look like paragraph ends.
    text = re.sub(r"\s+", " ", text)
    # Protect a few common abbreviations
    protected = {"e.g.", "i.e.", "Mr.", "Mrs.", "Dr.", "Prof.", "vs.", "No.", "U.S."}
    tokens = text.split(" ")
    rebuilt = []
    i = 0
    while i < len(tokens):
        w = tokens[i]
        if any(w.endswith(p) for p in protected):
            # keep token as-is
            rebuilt.append(w)
        else:
            rebuilt.append(w)
        i += 1
    s = " ".join(rebuilt)
    # Now split
    candidates = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", s)
    # Filter empties
    return [c.strip() for c in candidates if c and not c.isspace()]


def word_tokens(text: str) -> List[str]:
    return re.findall(r"[A-Za-z][A-Za-z'-]*", text)


def percent_values(text: str) -> List[str]:
    return re.findall(r"\b\d+(?:\.\d+)?\s*%|\b\d+(?:\.\d+)?\s+percent\b", text, flags=re.IGNORECASE)


def line_iter(text: str) -> List[str]:
    return text.split("\n")


# -----------------------------
# Checks
# -----------------------------

def check_language_tool(text: str, lang: str, max_points: float = 35.0) -> CheckResult:
    issues: List[Issue] = []
    metrics: Dict[str, Any] = {"matches": 0}

    if language_tool_python is None:
        # Graceful skip
        return CheckResult(
            name="Grammar & style (LanguageTool)",
            score=max_points * 0.6,  # partial credit if not available
            max_score=max_points,
            issues=[Issue("Grammar & style (LanguageTool)", "language_tool_python not installed; skipping deep grammar/style. Install with: pip install language-tool-python")],
            metrics={"available": False}
        )
    try:
        tool = language_tool_python.LanguageTool(public_api=False, language=lang)
        matches = tool.check(text)
        metrics["matches"] = len(matches)
        words = max(1, len(word_tokens(text)))
        matches_per_1k = 1000 * len(matches) / words

        # Scoring: start at max_points, subtract up to max_points based on density
        # Subtract 1 point per 2 matches/1k words (tunable), capped.
        penalty = min(max_points, (matches_per_1k / 2.0) * 1.0)
        score = max_points - penalty

        # Record a few sample issues
        for m in matches[:100]:
            snippet = text[max(0, m.offset - 20): m.offset + 40].replace("\n", " ")
            msg = f"{m.ruleId}: {m.message} → suggestion(s): {', '.join(m.replacements[:3])}"
            issues.append(Issue("Grammar & style (LanguageTool)", msg, location=f"...{snippet}..."))
        return CheckResult(
            name="Grammar & style (LanguageTool)",
            score=round(score, 2),
            max_score=max_points,
            issues=issues,
            metrics={
                "available": True,
                "total_matches": len(matches),
                "matches_per_1000_words": round(matches_per_1k, 2)
            }
        )
    except Exception as e:
        return CheckResult(
            name="Grammar & style (LanguageTool)",
            score=max_points * 0.6,
            max_score=max_points,
            issues=[Issue("Grammar & style (LanguageTool)", f"LanguageTool error: {e}")],
            metrics={"available": False}
        )


def check_readability(text: str, max_points: float = 10.0) -> CheckResult:
    issues: List[Issue] = []
    metrics: Dict[str, Any] = {}
    sents = split_sentences(text)
    words = word_tokens(text)
    avg_len = statistics.mean([len(word_tokens(s)) for s in sents]) if sents else 0
    long_sents = [s for s in sents if len(word_tokens(s)) > 30]
    metrics["avg_sentence_length_words"] = round(avg_len, 2)
    metrics["long_sentences_over_30_words"] = len(long_sents)

    # Readability via textstat if present
    if textstat is not None:
        try:
            fre = textstat.flesch_reading_ease(text)
            grade = textstat.text_standard(text, float_output=True)
            metrics["flesch_reading_ease"] = round(fre, 2)
            metrics["grade_level"] = round(grade, 2)
        except Exception:
            pass

    # Scoring: penalize lots of very long sentences
    penalty = min(max_points, 0.5 * len(long_sents))  # 0.5 point per long sentence
    score = max_points - penalty

    if len(long_sents) > 0:
        examples = long_sents[:3]
        for ex in examples:
            issues.append(Issue("Readability", "Very long sentence (>30 words). Consider splitting.", location=ex[:120] + ("..." if len(ex) > 120 else "")))

    return CheckResult(
        name="Readability",
        score=round(score, 2),
        max_score=max_points,
        issues=issues,
        metrics=metrics
    )


def check_punctuation_style(text: str, max_points: float = 10.0) -> CheckResult:
    issues: List[Issue] = []
    metrics: Dict[str, Any] = {}
    words = max(1, len(word_tokens(text)))
    semicolons = text.count(";")
    ellipses = text.count("...")
    double_punct = len(re.findall(r"[!?]{2,}", text))
    em_dashes = text.count("—")
    spaced_em_dashes = len(re.findall(r"\s—\s", text))

    metrics.update({
        "semicolons": semicolons,
        "semicolons_per_1000_words": round(1000 * semicolons / words, 2),
        "ellipses": ellipses,
        "double_punctuations": double_punct,
        "em_dashes": em_dashes,
        "em_dashes_with_spaces": spaced_em_dashes
    })

    # Heuristic penalties
    penalty = 0.0
    if semicolons > 0 and (1000 * semicolons / words) > 3.0:
        penalty += 2.5; issues.append(Issue("Punctuation/Style", "Potential overuse of semicolons. Consider periods or conjunctions."))
    if ellipses > 2:
        penalty += 1.5; issues.append(Issue("Punctuation/Style", "Ellipses ('...') appear frequently; use sparingly in formal prose."))
    if double_punct > 0:
        penalty += 1.0; issues.append(Issue("Punctuation/Style", "Repeated punctuation like '!!' or '??' found; avoid in formal writing."))
    if spaced_em_dashes > 0:
        penalty += 0.5; issues.append(Issue("Punctuation/Style", "Use unspaced em dashes (—) or a consistent style (— with no spaces)."))

    score = max_points - min(max_points, penalty)
    return CheckResult(
        name="Punctuation & Style",
        score=round(score, 2),
        max_score=max_points,
        issues=issues,
        metrics=metrics
    )


def check_whitespace_formatting(text: str, max_points: float = 5.0) -> CheckResult:
    issues: List[Issue] = []
    metrics: Dict[str, Any] = {}
    trailing = len(re.findall(r"[ \t]+$", text, flags=re.MULTILINE))
    doubles = len(re.findall(r" {2,}", text))
    tabs = text.count("\t")
    metrics.update({
        "trailing_whitespace_lines": trailing,
        "double_spaces": doubles,
        "tab_characters": tabs
    })
    penalty = 0.1 * trailing + 0.05 * doubles + 0.1 * tabs
    score = max_points - min(max_points, penalty)
    if trailing > 0:
        issues.append(Issue("Whitespace", f"{trailing} line(s) have trailing spaces."))
    if doubles > 0:
        issues.append(Issue("Whitespace", f"{doubles} double-space occurrence(s) detected. Consider single spacing."))
    if tabs > 0:
        issues.append(Issue("Whitespace", f"{tabs} tab character(s) found. Use spaces for alignment."))

    return CheckResult(
        name="Whitespace & Basic Formatting",
        score=round(score, 2),
        max_score=max_points,
        issues=issues,
        metrics=metrics
    )


def check_percentage_consistency(text: str, max_points: float = 5.0) -> CheckResult:
    issues: List[Issue] = []
    metrics: Dict[str, Any] = {}
    vals = percent_values(text)
    pct = len([v for v in vals if "%" in v])
    wordpct = len([v for v in vals if re.search(r"\bpercent\b", v, flags=re.IGNORECASE)])
    metrics.update({
        "percent_symbol": pct,
        "percent_word": wordpct,
        "total_percent_mentions": len(vals)
    })
    penalty = 0.0
    if pct > 0 and wordpct > 0:
        penalty = 2.0
        issues.append(Issue("Numbers/Percentages", "Both '%' and 'percent' are used. Consider choosing one style for consistency."))

    # Decimal style consistency (7% vs 7.0%)
    decimals = re.findall(r"\b\d+\.\d+\s*%", text)
    integers = re.findall(r"\b\d+\s*%", text)
    if decimals and integers:
        penalty += 0.5
        issues.append(Issue("Numbers/Percentages", "Mix of whole-number and decimal percentages. Consider a consistent format."))

    score = max_points - min(max_points, penalty)
    return CheckResult(
        name="Numbers & Percentages Consistency",
        score=round(score, 2),
        max_score=max_points,
        issues=issues,
        metrics=metrics
    )


def check_headings_capitalization(text: str, max_points: float = 5.0) -> CheckResult:
    issues: List[Issue] = []
    metrics: Dict[str, Any] = {}
    lines = [ln.strip() for ln in line_iter(text)]
    probable_headings = [ln for ln in lines if (ln and (ln.endswith(":") or (len(ln) < 60 and ln.isupper())))]
    metrics["probable_headings"] = len(probable_headings)

    bad = 0
    for h in probable_headings:
        # Simple title-case check (ignore minor words)
        if h.endswith(":"):
            core = h[:-1].strip()
        else:
            core = h.strip()
        if core and core[0].islower():
            bad += 1
            issues.append(Issue("Headings/Capitalization", f"Heading may not be capitalized: '{h}'"))
    penalty = min(max_points, bad * 0.5)
    score = max_points - penalty
    return CheckResult(
        name="Headings & Capitalization",
        score=round(score, 2),
        max_score=max_points,
        issues=issues,
        metrics=metrics
    )


def check_passive_voice(text: str, max_points: float = 5.0) -> CheckResult:
    # Heuristic: forms of "be" + past participle (-ed), not perfect but indicative.
    issues: List[Issue] = []
    metrics: Dict[str, Any] = {}
    be_forms = r"\b(?:am|is|are|was|were|be|been|being)\b"
    # A very rough past participle detector
    participle = r"\b\w+(?:ed|en)\b"
    matches = re.findall(be_forms + r"\s+" + participle, text, flags=re.IGNORECASE)
    metrics["passive_like_phrases"] = len(matches)

    penalty = min(max_points, len(matches) * 0.05)  # small penalty
    score = max_points - penalty
    if matches[:5]:
        for m in matches[:5]:
            issues.append(Issue("Passive Voice (heuristic)", f"Possible passive construction: '{m}'"))
    return CheckResult(
        name="Passive Voice (Heuristic)",
        score=round(score, 2),
        max_score=max_points,
        issues=issues,
        metrics=metrics
    )


def check_parallel_bullets(text: str, max_points: float = 10.0) -> CheckResult:
    """
    Check bullet/numbered lists for parallel starts (all gerunds, all imperatives, or all noun phrases).
    Heuristic: categorize each item start into {GERUND(-ing), IMPERATIVE(verb-ish), NOUN/OTHER}.
    """
    issues: List[Issue] = []
    metrics: Dict[str, Any] = {}

    lines = line_iter(text)
    bullet_blocks: List[List[str]] = []
    block: List[str] = []
    bullet_re = re.compile(r"^\s*(?:[-*•]|(\d+)[.)])\s+")

    def flush_block():
        nonlocal block
        if len(block) >= 3:
            bullet_blocks.append(block)
        block = []

    for ln in lines:
        if bullet_re.match(ln):
            block.append(ln.strip())
        else:
            flush_block()
    flush_block()

    def classify_start(token: str) -> str:
        t = token.lower()
        if t.endswith("ing"):
            return "GERUND"
        # Imperative-ish: verb base forms are hard; crude heuristic: common verbs
        common_base_verbs = {"use","add","ensure","consider","avoid","include","provide","attend","highlight","outline","emphasize","leverage","budget","remember","keep"}
        if t in common_base_verbs:
            return "IMPERATIVE"
        # If starts with a determiner, likely noun phrase
        determiners = {"a","an","the","this","that","these","those"}
        if t in determiners:
            return "NOUNPHRASE"
        # Uppercase initial noun-ish: just call OTHER/NOUN
        return "OTHER"

    inconsistent_blocks = 0
    for blk in bullet_blocks:
        starts = []
        for item in blk:
            first = word_tokens(item[:60])
            token = first[0] if first else ""
            starts.append(classify_start(token))
        # measure diversity
        categories = set(starts)
        if len(categories) > 1:
            inconsistent_blocks += 1
            issues.append(Issue("Parallelism", f"Bullet list with mixed starts ({', '.join(sorted(categories))}). Consider making items parallel.", location=" | ".join(blk[:3]) + (" ..." if len(blk)>3 else "")))

    metrics["bullet_blocks_3plus"] = len(bullet_blocks)
    metrics["inconsistent_blocks"] = inconsistent_blocks

    penalty = min(max_points, inconsistent_blocks * 2.0)  # 2 points per inconsistent block
    score = max_points - penalty
    return CheckResult(
        name="Parallel Structure in Lists",
        score=round(score, 2),
        max_score=max_points,
        issues=issues,
        metrics=metrics
    )


def check_links_formatting(text: str, max_points: float = 5.0) -> CheckResult:
    issues: List[Issue] = []
    metrics: Dict[str, Any] = {}
    raw_urls = re.findall(r"https?://\S+", text)
    markdown_links = re.findall(r"\[[^\]]+\]\(\s*https?://[^\)]+\)", text)
    metrics["raw_urls"] = len(raw_urls)
    metrics["markdown_or_hyperlinks"] = len(markdown_links)

    penalty = 0.0
    if raw_urls and not markdown_links:
        penalty = 2.0
        issues.append(Issue("Links/Formatting", "Raw URLs detected. Consider hyperlinking text instead of showing bare links."))

    score = max_points - min(max_points, penalty)
    return CheckResult(
        name="Links & Citation Formatting",
        score=round(score, 2),
        max_score=max_points,
        issues=issues,
        metrics=metrics
    )


def check_acronym_definitions(text: str, max_points: float = 10.0) -> CheckResult:
    """
    Find ALL-CAPS abbreviations (2–6 letters) and see if they are defined (e.g., 'International Documentary Association (IDA)')
    """
    issues: List[Issue] = []
    metrics: Dict[str, Any] = {}
    acronyms = set(re.findall(r"\b([A-Z]{2,6})\b", text))
    # Ignore common English words in caps (simple stoplist)
    stop = {"USA","US","U.S","PDF","DOCX","CEO","CFO","FYI","ETA"}
    acronyms = {a for a in acronyms if a not in stop}

    undefined: List[str] = []
    for ac in sorted(acronyms):
        # Consider defined if "(" + ac + ")" appears anywhere
        if not re.search(r"\([ ]*" + re.escape(ac) + r"[ ]*\)", text):
            undefined.append(ac)

    metrics["acronyms_found"] = len(acronyms)
    metrics["acronyms_undefined"] = len(undefined)

    penalty = min(max_points, 1.0 * len(undefined[:5]))  # up to 5 points
    score = max_points - penalty

    for ac in undefined[:5]:
        issues.append(Issue("Acronyms", f"Acronym '{ac}' appears without a nearby definition (e.g., 'Name (AC)')."))

    return CheckResult(
        name="Acronym Definitions",
        score=round(score, 2),
        max_score=max_points,
        issues=issues,
        metrics=metrics
    )


# -----------------------------
# Scoring aggregation
# -----------------------------

def aggregate_report(file_path: str, text: str, lang: str) -> AuditReport:
    checks: List[CheckResult] = []
    checks.append(check_language_tool(text, lang, max_points=35.0))
    checks.append(check_readability(text, max_points=10.0))
    checks.append(check_punctuation_style(text, max_points=10.0))
    checks.append(check_whitespace_formatting(text, max_points=5.0))
    checks.append(check_percentage_consistency(text, max_points=5.0))
    checks.append(check_headings_capitalization(text, max_points=5.0))
    checks.append(check_passive_voice(text, max_points=5.0))
    checks.append(check_parallel_bullets(text, max_points=10.0))
    checks.append(check_links_formatting(text, max_points=5.0))
    checks.append(check_acronym_definitions(text, max_points=10.0))

    total = sum(c.score for c in checks)
    max_total = sum(c.max_score for c in checks)
    # Normalize to 100 (should already be 100, but keep robust)
    total_score = round(100 * total / max_total, 2) if max_total else 0.0

    summary = {
        "file": file_path,
        "language": lang,
        "score": total_score,
        "max": 100.0,
        "checks": {c.name: {"score": c.score, "max": c.max_score} for c in checks}
    }
    return AuditReport(
        file_path=file_path,
        language=lang,
        total_score=total_score,
        check_results=checks,
        summary=summary
    )


def report_to_json(audit: AuditReport) -> Dict[str, Any]:
    return {
        "file_path": audit.file_path,
        "language": audit.language,
        "total_score": audit.total_score,
        "checks": [
            {
                "name": c.name,
                "score": c.score,
                "max_score": c.max_score,
                "metrics": c.metrics,
                "issues": [asdict(i) for i in c.issues]
            } for c in audit.check_results
        ]
    }


def report_to_markdown(audit: AuditReport) -> str:
    lines = []
    lines.append(f"# Document Audit Report")
    lines.append(f"**File:** `{audit.file_path}`  ")
    lines.append(f"**Language:** {audit.language}  ")
    lines.append(f"**Total Score:** **{audit.total_score}/100**")
    lines.append("")
    for c in audit.check_results:
        lines.append(f"## {c.name} — {c.score:.2f}/{c.max_score:.0f}")
        if c.metrics:
            lines.append("**Metrics**:")
            for k, v in c.metrics.items():
                lines.append(f"- {k}: {v}")
        if c.issues:
            lines.append("**Issues (samples):**")
            for i, iss in enumerate(c.issues[:10], 1):
                loc = f" ({iss.location})" if iss.location else ""
                lines.append(f"{i}. {iss.message}{loc}")
        lines.append("")
    return "\n".join(lines)


# -----------------------------
# Main
# -----------------------------

def main():
    parser = argparse.ArgumentParser(description="Audit writing quality of DOCX/PDF/TXT and score out of 100.")
    parser.add_argument("file", help="Path to input document (.docx/.pdf/.txt/.md)")
    parser.add_argument("--lang", default="en-US", help="Language code for grammar checks (default: en-US)")
    parser.add_argument("--out", default=None, help="Output path prefix (default: same folder/name)")
    args = parser.parse_args()

    file_path = args.file
    if not os.path.exists(file_path):
        print(f"ERROR: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    try:
        raw = read_text_from_file(file_path)
        text = normalize_text(raw)
    except Exception as e:
        print(f"ERROR reading file: {e}", file=sys.stderr)
        sys.exit(2)

    audit = aggregate_report(file_path, text, args.lang)

    if args.out is None:
        base, _ = os.path.splitext(file_path)
        out_prefix = base
    else:
        out_prefix = args.out

    json_path = out_prefix + "_report.json"
    md_path = out_prefix + "_report.md"

    with open(json_path, "w", encoding="utf-8") as jf:
        json.dump(report_to_json(audit), jf, ensure_ascii=False, indent=2)

    with open(md_path, "w", encoding="utf-8") as mf:
        mf.write(report_to_markdown(audit))

    # Console summary
    print(f"Score: {audit.total_score}/100 — {os.path.basename(file_path)}")
    for c in audit.check_results:
        print(f"  - {c.name}: {c.score:.2f}/{c.max_score:.0f}")
    print(f"\nSaved: {json_path}\nSaved: {md_path}")


if __name__ == "__main__":
    main()
'''
with open('/mnt/data/doc_audit.py', 'w', encoding='utf-8') as f:
    f.write(script)

with open('/mnt/data/doc_audit_requirements.txt', 'w', encoding='utf-8') as f:
    f.write(reqs)

print("Files created: /mnt/data/doc_audit.py and /mnt/data/doc_audit_requirements.txt")
