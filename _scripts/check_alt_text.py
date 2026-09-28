#!/usr/bin/env python3
"""Check that every coursebook figure has useful LaTeX alt text."""

import re
import sys
from pathlib import Path


HACK_ALLOWLIST = {
    ("title.tex", 12),
    ("title.tex", 13),
    ("title.tex", 41),
}
DECORATIVE_ALLOWLIST = {("title.tex", 29)}

INCLUDEGRAPHICS = re.compile(r"\\includegraphics\*?(?![A-Za-z@])")
FIGURE_ENV = re.compile(r"\\(begin|end)\s*\{\s*figure\*?\s*\}")
CAPTION = re.compile(r"\\caption\*?(?![A-Za-z@])")
COMMENT_ENV = re.compile(
    r"\\begin\s*\{\s*comment\s*\}.*?\\end\s*\{\s*comment\s*\}",
    re.DOTALL,
)
LATEX_ESCAPE = re.compile(r"\\(?:[#$%&_{}]|[~^]|[A-Za-z@]+)")
GENERIC_ALT = {"diagram", "figure", "image"}


def _is_escaped(text, index):
    slashes = 0
    index -= 1
    while index >= 0 and text[index] == "\\":
        slashes += 1
        index -= 1
    return slashes % 2 == 1


def _mask_comments(text):
    """Replace TeX comments with spaces so source line numbers stay stable."""
    chars = list(text)
    index = 0
    while index < len(chars):
        if chars[index] == "%" and not _is_escaped(text, index):
            while index < len(chars) and chars[index] not in "\r\n":
                chars[index] = " "
                index += 1
        index += 1

    uncommented = "".join(chars)
    chars = list(uncommented)
    for match in COMMENT_ENV.finditer(uncommented):
        for index in range(match.start(), match.end()):
            if chars[index] not in "\r\n":
                chars[index] = " "
    return "".join(chars)


def _read_group(text, start, opening, closing):
    """Read one balanced TeX group and return (contents, end_index)."""
    if start >= len(text) or text[start] != opening:
        return None

    if opening == "{":
        depth = 1
        index = start + 1
        while index < len(text):
            if _is_escaped(text, index):
                index += 1
                continue
            if text[index] == "{":
                depth += 1
            elif text[index] == "}":
                depth -= 1
                if depth == 0:
                    return text[start + 1 : index], index + 1
            index += 1
        return None

    if opening == "[":
        bracket_depth = 1
        brace_depth = 0
        index = start + 1
        while index < len(text):
            if _is_escaped(text, index):
                index += 1
                continue
            char = text[index]
            if char == "{":
                brace_depth += 1
            elif char == "}" and brace_depth:
                brace_depth -= 1
            elif brace_depth == 0 and char == "[":
                bracket_depth += 1
            elif brace_depth == 0 and char == "]":
                bracket_depth -= 1
                if bracket_depth == 0:
                    return text[start + 1 : index], index + 1
            index += 1
    return None


def _skip_space(text, index):
    while index < len(text) and text[index].isspace():
        index += 1
    return index


def _split_top_level(value, delimiter, first_only=False):
    pieces = []
    start = 0
    brace_depth = 0
    bracket_depth = 0
    for index, char in enumerate(value):
        if _is_escaped(value, index):
            continue
        if char == "{":
            brace_depth += 1
        elif char == "}" and brace_depth:
            brace_depth -= 1
        elif brace_depth == 0 and char == "[":
            bracket_depth += 1
        elif brace_depth == 0 and char == "]" and bracket_depth:
            bracket_depth -= 1
        elif brace_depth == 0 and bracket_depth == 0 and char == delimiter:
            pieces.append(value[start:index])
            start = index + 1
            if first_only:
                break
    pieces.append(value[start:])
    return pieces


def _unwrap(value):
    value = value.strip()
    if value.startswith("{"):
        group = _read_group(value, 0, "{", "}")
        if group and group[1] == len(value):
            return group[0]
    return value


def _parse_options(options):
    parsed = {}
    for option in _split_top_level(options, ","):
        pair = _split_top_level(option, "=", first_only=True)
        if len(pair) == 2:
            parsed[pair[0].strip().lower()] = _unwrap(pair[1])
    return parsed


def _line_number(text, index):
    return text.count("\n", 0, index) + 1


def _figure_ranges(text):
    stack = []
    ranges = []
    for match in FIGURE_ENV.finditer(text):
        if _is_escaped(text, match.start()):
            continue
        if match.group(1) == "begin":
            stack.append(match.end())
        elif stack:
            ranges.append((stack.pop(), match.start()))
    return ranges


def _caption_for(text, position, ranges):
    for start, end in ranges:
        if start <= position < end:
            match = CAPTION.search(text, start, end)
            if not match or _is_escaped(text, match.start()):
                return None
            index = _skip_space(text, match.end())
            if index < end and text[index] == "[":
                optional = _read_group(text, index, "[", "]")
                if not optional:
                    return None
                index = _skip_space(text, optional[1])
            group = _read_group(text, index, "{", "}")
            return group[0] if group else None
    return None


def _normalise(value):
    return re.sub(r"\s+", " ", value).strip().casefold()


def scan_source(relative_path, source):
    """Return figures, decorative images, macro definitions, and errors."""
    relative_path = Path(relative_path).as_posix()
    text = _mask_comments(source)
    ranges = _figure_ranges(text)
    figures = []
    decorative = []
    macro_definitions = []
    errors = []

    for match in INCLUDEGRAPHICS.finditer(text):
        if _is_escaped(text, match.start()):
            continue
        line = _line_number(text, match.start())
        identity = (relative_path, line)
        if identity in HACK_ALLOWLIST:
            macro_definitions.append(line)
            continue

        index = _skip_space(text, match.end())
        options = None
        if index < len(text) and text[index] == "[":
            group = _read_group(text, index, "[", "]")
            if not group:
                errors.append("{}:{}: unterminated includegraphics options".format(relative_path, line))
                continue
            options, index = group
            index = _skip_space(text, index)

        filename_group = _read_group(text, index, "{", "}")
        if not filename_group:
            errors.append("{}:{}: missing includegraphics filename".format(relative_path, line))
            continue
        filename = filename_group[0].strip()

        if identity in DECORATIVE_ALLOWLIST:
            decorative.append({"path": relative_path, "line": line, "file": filename})
            continue

        option_map = _parse_options(options or "")
        alt = option_map.get("alt")
        if alt is None or not alt.strip():
            errors.append("{}:{}: includegraphics needs non-empty alt text".format(relative_path, line))
            continue

        warnings = []
        caption = _caption_for(text, match.start(), ranges)
        if caption is not None and _normalise(alt) == _normalise(caption):
            warnings.append("alt text repeats the figure caption")
        generic = re.sub(r"[^\w]+", " ", alt.casefold(), flags=re.UNICODE).strip()
        if generic in GENERIC_ALT:
            warnings.append("alt text is a generic label")
        if LATEX_ESCAPE.search(alt):
            warnings.append("alt text contains a LaTeX escape or command")

        figures.append({
            "path": relative_path,
            "line": line,
            "file": filename,
            "alt": alt.strip(),
            "warnings": warnings,
        })

    return {
        "figures": figures,
        "decorative": decorative,
        "macro_definitions": macro_definitions,
        "errors": errors,
    }


def scan_repository(root):
    root = Path(root)
    report = {"figures": [], "decorative": [], "macro_definitions": [], "errors": []}
    paths = sorted(path for path in root.rglob("*.tex") if ".git" not in path.parts)
    for path in paths:
        relative_path = path.relative_to(root).as_posix()
        source = path.read_text(encoding="utf-8")
        result = scan_source(relative_path, source)
        for key in report:
            report[key].extend(result[key])

    observed_macros = {("title.tex", line) for line in report["macro_definitions"]}
    for path, line in sorted(HACK_ALLOWLIST - observed_macros):
        report["errors"].append(
            "{}:{}: expected includegraphics macro definition was not found".format(path, line)
        )
    observed_decorative = {(item["path"], item["line"]) for item in report["decorative"]}
    for path, line in sorted(DECORATIVE_ALLOWLIST - observed_decorative):
        report["errors"].append(
            "{}:{}: expected decorative image was not found".format(path, line)
        )
    return report


def main():
    root = Path(__file__).resolve().parents[1]
    report = scan_repository(root)

    print("Content figures ({}):".format(len(report["figures"])))
    for figure in report["figures"]:
        print("  {}:{} -> {} | alt={}".format(
            figure["path"], figure["line"], figure["file"], figure["alt"]
        ))

    print("Decorative images excluded: {}".format(len(report["decorative"])))
    for image in report["decorative"]:
        print("  {}:{} -> {}".format(image["path"], image["line"], image["file"]))

    print("Ignored includegraphics macro definitions: {}".format(
        ", ".join("title.tex:{}".format(line) for line in sorted(report["macro_definitions"]))
    ))

    for figure in report["figures"]:
        for warning in figure["warnings"]:
            print("WARNING: {}:{}: {}".format(figure["path"], figure["line"], warning))
    for error in report["errors"]:
        print("ERROR: " + error, file=sys.stderr)

    return 1 if report["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
