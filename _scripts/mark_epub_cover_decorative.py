#!/usr/bin/env python3
"""Mark Pandoc's generated EPUB cover image as decorative."""

import os
import re
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


COVER_PATH = "EPUB/text/cover.xhtml"
DECORATIVE_ATTRIBUTES = {
    "role": "presentation",
    "aria-hidden": "true",
    "focusable": "false",
}


def _mark_cover(data):
    root = ET.fromstring(data)
    images = [node for node in root.iter() if node.tag.rsplit("}", 1)[-1] == "image"]
    if len(images) != 1:
        raise ValueError("expected one SVG cover image, found {}".format(len(images)))
    for name, value in DECORATIVE_ATTRIBUTES.items():
        if images[0].get(name) not in (None, value):
            raise ValueError("cover image has conflicting {} attribute".format(name))

    matches = list(re.finditer(rb"<image\b[^>]*>", data))
    if len(matches) != 1:
        raise ValueError("could not locate one SVG image start tag")
    match = matches[0]
    tag = match.group(0)
    for name, value in DECORATIVE_ATTRIBUTES.items():
        if re.search(rb"\b" + name.encode("ascii") + rb"\s*=", tag):
            continue
        closing = -2 if tag.endswith(b"/>") else -1
        tag = (
            tag[:closing]
            + b" "
            + name.encode("ascii")
            + b'="'
            + value.encode("ascii")
            + b'"'
            + tag[closing:]
        )

    updated = data[:match.start()] + tag + data[match.end():]
    marked = ET.fromstring(updated)
    marked_image = next(node for node in marked.iter() if node.tag.rsplit("}", 1)[-1] == "image")
    if any(marked_image.get(name) != value for name, value in DECORATIVE_ATTRIBUTES.items()):
        raise ValueError("cover image decorative attributes did not persist")
    return updated


def mark_cover_decorative(epub_path):
    epub_path = Path(epub_path)
    with zipfile.ZipFile(epub_path, "r") as source:
        names = source.namelist()
        if COVER_PATH not in names:
            raise ValueError("{} is missing from the EPUB".format(COVER_PATH))
        cover = _mark_cover(source.read(COVER_PATH))
        entries = [
            (info, cover if info.filename == COVER_PATH else source.read(info.filename))
            for info in source.infolist()
        ]

    with tempfile.NamedTemporaryFile(dir=str(epub_path.parent), suffix=".epub", delete=False) as temporary:
        temporary_path = Path(temporary.name)
    try:
        with zipfile.ZipFile(temporary_path, "w") as target:
            for info, data in entries:
                target.writestr(info, data)
        os.replace(temporary_path, epub_path)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise

    with zipfile.ZipFile(epub_path, "r") as result:
        _mark_cover(result.read(COVER_PATH))


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: mark_epub_cover_decorative.py main.epub")
    mark_cover_decorative(sys.argv[1])


if __name__ == "__main__":
    main()
