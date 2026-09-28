#!/usr/bin/env python3
"""Check Pandoc EPUB and wiki outputs against the source figure alt text."""

import argparse
from collections import Counter
import json
import os
import posixpath
import re
import subprocess
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree as ET

import yaml

from alt_text import _render_tex_escapes
from check_alt_text import _mask_comments, scan_repository, scan_source


OPF_NS = "http://www.idpf.org/2007/opf"
DC_NS = "http://purl.org/dc/elements/1.1/"
XHTML_NS = "http://www.w3.org/1999/xhtml"
SVG_NS = "http://www.w3.org/2000/svg"
DECORATIVE_COVER = {
    "role": "presentation",
    "aria-hidden": "true",
    "focusable": "false",
}


def _normalise(text):
    return re.sub(r"\s+", " ", text).strip()


def _expected_figures(root):
    report = scan_repository(root)
    if report["errors"]:
        raise ValueError("source alt-text scan failed: {}".format("; ".join(report["errors"])))

    order = yaml.safe_load((root / "order.yaml").read_text(encoding="utf-8"))
    input_command = re.compile(r"\\(?:input|include)\s*\{\s*([^{}]+?)\s*\}")
    figures = []

    def visit(source_path, active):
        source_path = source_path.resolve()
        if source_path in active:
            raise ValueError("cyclic TeX input: {}".format(source_path))
        if not source_path.is_file():
            raise ValueError("ordered chapter is missing: {}".format(source_path))
        active = active | {source_path}
        source = source_path.read_text(encoding="utf-8")
        relative = source_path.relative_to(root).as_posix()
        result = scan_source(relative, source)
        if result["errors"]:
            raise ValueError("source alt-text scan failed: {}".format("; ".join(result["errors"])))
        local_figures = iter(result["figures"])
        pending = next(local_figures, None)
        masked = _mask_comments(source)
        for include in input_command.finditer(masked):
            include_line = masked.count("\n", 0, include.start()) + 1
            while pending is not None and pending["line"] < include_line:
                figures.append(pending)
                pending = next(local_figures, None)

            name = include.group(1).strip()
            include_path = root / name
            if not include_path.suffix:
                include_path = include_path.with_suffix(".tex")
            if not include_path.is_file():
                include_path = source_path.parent / name
                if not include_path.suffix:
                    include_path = include_path.with_suffix(".tex")
            if include_path.is_file():
                visit(include_path, active)

        if pending is not None:
            figures.append(pending)
        figures.extend(local_figures)

    for chapter in order:
        visit(root / (chapter + ".tex"), set())

    ordered_ids = {(figure["path"], figure["line"]) for figure in figures}
    unlisted = [
        "{}:{}".format(figure["path"], figure["line"])
        for figure in report["figures"]
        if (figure["path"], figure["line"]) not in ordered_ids
    ]
    if len(figures) != len(report["figures"]):
        raise ValueError(
            "ordered chapters contain {} of {} source figures; unlisted: {}".format(
                len(figures), len(report["figures"]), ", ".join(unlisted)
            )
        )
    return figures


def _check_alts(actual, expected, output_name):
    if len(actual) != len(expected):
        raise ValueError(
            "{} has {} content images; source has {} figures".format(
                output_name, len(actual), len(expected)
            )
        )
    source_values = Counter()
    for source in expected:
        wanted = _normalise(_render_tex_escapes(source["alt"]))
        suffix = Path(source["file"]).suffix.lower()
        if suffix == ".eps":
            suffix = ".png"
        source_values[(wanted, suffix)] += 1

    output_values = Counter()
    for alt, image_path in actual:
        if not alt or not alt.strip():
            raise ValueError("{} has an image with empty alt text".format(output_name))
        output_values[(_normalise(alt), Path(image_path).suffix.lower())] += 1

    if output_values != source_values:
        missing = source_values - output_values
        unexpected = output_values - source_values
        raise ValueError(
            "{} image alt/source mismatch; missing {}, unexpected {}".format(
                output_name, dict(missing), dict(unexpected)
            )
        )


def _property_values(metadata, name):
    return {
        (element.text or "").strip()
        for element in metadata.findall(".//{{{}}}meta".format(OPF_NS))
        if element.get("property") == name
    }


def validate_epub(epub_path, expected):
    with zipfile.ZipFile(epub_path, "r") as archive:
        names = set(archive.namelist())
        opf_name = next((name for name in names if name.endswith(".opf")), None)
        if opf_name is None:
            raise ValueError("EPUB package document is missing")
        opf = ET.fromstring(archive.read(opf_name))
        metadata = opf.find("{{{}}}metadata".format(OPF_NS))
        if metadata is None:
            raise ValueError("EPUB metadata element is missing")

        metadata_expectations = {
            "schema:accessMode": {"textual", "visual"},
            "schema:accessModeSufficient": {"textual,visual"},
            "schema:accessibilityFeature": {
                "alternativeText",
                "readingOrder",
                "structuralNavigation",
                "tableOfContents",
            },
            "schema:accessibilityHazard": {"none"},
        }
        for name, values in metadata_expectations.items():
            actual_values = _property_values(metadata, name)
            if actual_values != values:
                raise ValueError(
                    "EPUB {} metadata is {}; expected {}".format(name, actual_values, values)
                )

        language = metadata.find("{{{}}}language".format(DC_NS))
        edition_date = metadata.find("{{{}}}date".format(DC_NS))
        if language is None or language.text != "en-US":
            raise ValueError("EPUB language metadata must be en-US")
        if edition_date is None or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", edition_date.text or ""):
            raise ValueError("EPUB date metadata must be an ISO calendar date")

        manifest = {
            item.get("id"): item.get("href")
            for item in opf.findall(".//{{{}}}manifest/{{{}}}item".format(OPF_NS, OPF_NS))
        }
        spine = opf.find("{{{}}}spine".format(OPF_NS))
        if spine is None:
            raise ValueError("EPUB spine is missing")
        content_images = []
        opf_dir = posixpath.dirname(opf_name)
        for itemref in spine.findall("{{{}}}itemref".format(OPF_NS)):
            href = manifest.get(itemref.get("idref"))
            if not href:
                raise ValueError("EPUB spine references an unknown manifest item")
            document_name = posixpath.normpath(posixpath.join(opf_dir, href))
            if document_name.endswith("/cover.xhtml"):
                continue
            document = ET.fromstring(archive.read(document_name))
            for image in document.iter():
                if image.tag.rsplit("}", 1)[-1] != "img":
                    continue
                alt = image.get("alt")
                if alt is None or not alt.strip():
                    raise ValueError("EPUB {} has an img without alt".format(document_name))
                content_images.append((alt, image.get("src", "")))

        _check_alts(content_images, expected, "EPUB")

        if "EPUB/text/cover.xhtml" not in names:
            raise ValueError("EPUB cover.xhtml is missing")
        cover = ET.fromstring(archive.read("EPUB/text/cover.xhtml"))
        cover_images = [node for node in cover.iter() if node.tag == "{{{}}}image".format(SVG_NS)]
        if len(cover_images) != 1 or any(
            cover_images[0].get(name) != value for name, value in DECORATIVE_COVER.items()
        ):
            raise ValueError("EPUB cover image is not explicitly marked decorative")

    print("EPUB: {} source-matched content images; accessibility metadata and decorative cover verified".format(len(expected)))


class _ImageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = []

    def handle_starttag(self, tag, attrs):
        if tag.casefold() == "img":
            self.images.append(dict(attrs))


def _wiki_images(page, pandoc):
    result = subprocess.run(
        [pandoc, "--from=gfm+raw_html+autolink_bare_uris", "--to=json", str(page)],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        raise ValueError("Pandoc could not parse {}: {}".format(page, result.stderr.strip()))
    document = json.loads(result.stdout)
    images = []
    stack = [document]
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            if node.get("t") == "Image":
                images.append(node["c"])
            stack.extend(reversed(list(node.values())))
        elif isinstance(node, list):
            stack.extend(reversed(node))
    return [("".join(_inline_text(value) for value in image[1]), image[2][0]) for image in images]


def _inline_text(value):
    if isinstance(value, dict):
        kind = value.get("t")
        if kind == "Str":
            return value.get("c", "")
        if kind in {"Space", "SoftBreak", "LineBreak"}:
            return " "
        return _inline_text(value.get("c"))
    if isinstance(value, list):
        return "".join(_inline_text(child) for child in value)
    return ""


def validate_wiki(wiki_dir, root, expected, pandoc):
    actual = []
    order = yaml.safe_load((root / "order.yaml").read_text(encoding="utf-8"))
    for chapter in order:
        page = wiki_dir / (Path(chapter).name.title() + ".md")
        if not page.is_file():
            raise ValueError("generated wiki page is missing: {}".format(page))
        text = page.read_text(encoding="utf-8")
        html_parser = _ImageParser()
        html_parser.feed(text)
        for image in html_parser.images:
            actual.append((image.get("alt", ""), image.get("src", "")))
        actual.extend(_wiki_images(page, pandoc))
    _check_alts(actual, expected, "Wiki")

    home = wiki_dir / "Home.md"
    if not home.is_file():
        raise ValueError("generated wiki landing page is missing")
    parser = _ImageParser()
    parser.feed(home.read_text(encoding="utf-8"))
    if not parser.images:
        raise ValueError("wiki landing page has no images to check")
    for index, image in enumerate(parser.images, 1):
        if not image.get("alt", "").strip():
            raise ValueError("wiki landing page img {} has no alt".format(index))

    print(
        "Wiki: {} source-matched figure images; {} landing-page img tags have alt text".format(
            len(actual), len(parser.images)
        )
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("epub", "wiki"))
    parser.add_argument("path", type=Path)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--pandoc", default=os.environ.get("PANDOC", "pandoc"))
    args = parser.parse_args()
    root = args.root.resolve()
    expected = _expected_figures(root)
    if args.mode == "epub":
        validate_epub(args.path.resolve(), expected)
    else:
        validate_wiki(args.path.resolve(), root, expected, args.pandoc)


if __name__ == "__main__":
    main()
