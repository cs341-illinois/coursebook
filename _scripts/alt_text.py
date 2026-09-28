"""Shared alt-text handling for Pandoc's EPUB and wiki filters."""

import re

import panflute as pf


class NoAltTagException(Exception):
    """Raised when an image has neither useful alt text nor a caption."""


def _render_tex_escapes(text):
    text = re.sub(r"\\textbackslash\s*", r"\\", text)
    text = re.sub(r"\\([#$%&_{}])", r"\1", text)
    return re.sub(r"\s+", " ", text).strip()


def image_alt_text(image):
    """Return rendered image alt text, falling back to the nearest Figure caption."""
    text = pf.stringify(image)
    if text == "":
        parent = image.parent
        while parent is not None:
            if isinstance(parent, pf.Figure):
                text = pf.stringify(parent.caption)
                break
            parent = parent.parent

    text = _render_tex_escapes(text)
    if not text or text.casefold() == "image":
        raise NoAltTagException(image.url)
    return text


def inlines_from_alt(text):
    """Build plain Pandoc inlines without interpreting alt text as Markdown."""
    inlines = []
    for token in re.split(r"(\s+)", text.strip()):
        if not token:
            continue
        if token.isspace():
            inlines.append(pf.Space())
        else:
            inlines.append(pf.Str(token))
    return inlines


def set_image_alt_text(image, text):
    image.content = inlines_from_alt(text)
