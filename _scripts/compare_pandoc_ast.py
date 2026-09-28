#!/usr/bin/env python3
"""Report structural element-count changes between Pandoc JSON ASTs."""

import argparse
import json
import re
from pathlib import Path


ELEMENTS = {
    "headers": {"Header"},
    "paragraphs": {"Para", "Plain"},
    "code blocks": {"CodeBlock"},
    "math": {"Math"},
    "tables": {"Table"},
    "images": {"Image"},
    "citations": {"Cite"},
    "links": {"Link"},
}


def _counts(path):
    document = json.loads(Path(path).read_text(encoding="utf-8"))
    counts = {name: 0 for name in ELEMENTS}
    kinds = {}
    stack = [document]
    while stack:
        value = stack.pop()
        if isinstance(value, dict):
            kind = value.get("t")
            if kind is not None:
                kinds[kind] = kinds.get(kind, 0) + 1
            for name, matches in ELEMENTS.items():
                if kind in matches:
                    counts[name] += 1
            stack.extend(value.values())
        elif isinstance(value, list):
            stack.extend(value)
    return counts, kinds


def _citation_report(wiki_dir):
    pages = [
        path
        for path in Path(wiki_dir).glob("*.md")
        if path.name not in {"Home.md", "_Sidebar.md"}
    ]
    texts = [path.read_text(encoding="utf-8") for path in pages]
    links = sum(text.count("#ref-") for text in texts)
    raw = sum(len(re.findall(r"\[@[^\]]+\]", text)) for text in texts)
    if links == 0 or raw:
        raise ValueError("wiki citations did not render as links (links={}, raw={})".format(links, raw))
    return links, raw


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("baseline_json", type=Path)
    parser.add_argument("current_json", type=Path)
    parser.add_argument("--baseline-label", default="Pandoc 2.7")
    parser.add_argument("--current-label", default="Pandoc 3.10.2")
    parser.add_argument("--wiki-dir", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--report-file", type=Path)
    args = parser.parse_args()

    baseline, _ = _counts(args.baseline_json)
    current, _ = _counts(args.current_json)
    lines = [
        "# Pandoc structural comparison",
        "",
        "Source: `main.tex` JSON AST; counts are reported for review, not required to match.",
        "",
        "| Element | {} | {} | Change |".format(args.baseline_label, args.current_label),
        "| --- | ---: | ---: | ---: |",
    ]
    for name in ELEMENTS:
        old = baseline[name]
        new = current[name]
        lines.append("| {} | {} | {} | {:+d} |".format(name, old, new, new - old))

    citation_links, raw_citations = _citation_report(args.wiki_dir)
    lines.extend(
        [
            "",
            "Wiki citations: {} rendered reference links; {} raw citation tokens.".format(
                citation_links, raw_citations
            ),
        ]
    )

    generator = (args.repo_root / "_scripts" / "gen_wiki.py").read_text(encoding="utf-8")
    if "sed_regex" in generator or re.search(r"check_call\(\[\s*['\"]sed", generator):
        raise ValueError("obsolete wiki glyph cleanup is still present")
    lines.append("Wiki glyph cleanup: obsolete sed step removed.")
    report = "\n".join(lines) + "\n"
    print(report, end="")
    if args.report_file:
        args.report_file.parent.mkdir(parents=True, exist_ok=True)
        args.report_file.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
