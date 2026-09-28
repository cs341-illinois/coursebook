#!/usr/bin/env python3
"""Exercise both image filters with real Pandoc 3 LaTeX input."""

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

import panflute as pf

import pandoc_epub_filter
import pandoc_wiki_filter
from alt_text import NoAltTagException


ROOT = Path(__file__).resolve().parents[1]
PANDOC = os.environ.get("PANDOC", "pandoc")
FILTERS = {
    "epub": ROOT / "_scripts" / "pandoc_epub_filter.py",
    "wiki": ROOT / "_scripts" / "pandoc_wiki_filter.py",
}


def _walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


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


class PandocFilterTests(unittest.TestCase):
    def run_fixture(self, filter_name, body):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory) / "fixture.tex"
            (Path(directory) / "diagram.png").write_bytes(b"test image")
            fixture.write_text(
                "\\documentclass{article}\n"
                "\\begin{document}\n"
                + body
                + "\n\\end{document}\n",
                encoding="utf-8",
            )
            return subprocess.run(
                [
                    PANDOC,
                    "--from=latex",
                    "--to=json",
                    "--filter",
                    str(FILTERS[filter_name]),
                    str(fixture),
                ],
                cwd=directory,
                check=False,
                capture_output=True,
                text=True,
            )

    def assert_filter_alt(self, filter_name, body, expected):
        result = self.run_fixture(filter_name, body)
        self.assertEqual(result.returncode, 0, result.stderr)
        document = json.loads(result.stdout)
        images = [node for node in _walk(document) if node.get("t") == "Image"]
        self.assertEqual(len(images), 1)
        self.assertEqual(_inline_text(images[0]["c"][1]), expected)
        self.assertTrue(images[0]["c"][2][0].endswith("diagram.png"))
        if filter_name == "wiki":
            self.assertFalse(any(node.get("t") == "Figure" for node in _walk(document)))
            paragraphs = [node for node in document["blocks"] if node.get("t") == "Para"]
            self.assertTrue(any(any(child.get("t") == "Image" for child in _walk(p)) for p in paragraphs))
            if "Caption fallback" in body:
                self.assertTrue(any(_inline_text(p.get("c")) == "Caption fallback" for p in paragraphs))

    def test_alt_and_caption_and_eps_rewrite(self):
        body = (
            "\\begin{figure}\n"
            "\\includegraphics[alt={A useful description}]{diagram.eps}\n"
            "\\caption{Caption fallback}\n"
            "\\end{figure}"
        )
        for filter_name in FILTERS:
            with self.subTest(filter=filter_name):
                self.assert_filter_alt(filter_name, body, "A useful description")

    def test_caption_fallback_when_alt_is_absent(self):
        body = (
            "\\begin{figure}\n"
            "\\includegraphics{diagram.eps}\n"
            "\\caption{Caption fallback}\n"
            "\\end{figure}"
        )
        for filter_name in FILTERS:
            with self.subTest(filter=filter_name):
                self.assert_filter_alt(filter_name, body, "Caption fallback")

    def test_missing_whitespace_and_generic_alt_fail(self):
        body = "\\begin{figure}\\includegraphics{diagram.eps}\\end{figure}"
        for filter_name in FILTERS:
            with self.subTest(filter=filter_name, body=body):
                result = self.run_fixture(filter_name, body)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("NoAltTagException", result.stderr)

        # Pandoc 3.10.2 serializes alt="image" and whitespace-only alt as an
        # empty Image content list, so exercise those explicit AST values at
        # the shared filter boundary.
        callbacks = [pandoc_epub_filter.doc_filter, pandoc_wiki_filter.doc_filter]
        for callback in callbacks:
            for alt in ("   ", "image"):
                with self.subTest(callback=callback.__module__, alt=alt):
                    image = pf.Image(pf.Str(alt), url="diagram.eps")
                    with self.assertRaises(NoAltTagException):
                        callback(image, None)

    def test_latex_escapes_are_rendered(self):
        body = r"\includegraphics[alt={c\_str and \textbackslash 0}]{diagram.eps}"
        for filter_name in FILTERS:
            with self.subTest(filter=filter_name):
                self.assert_filter_alt(filter_name, body, r"c_str and \0")


if __name__ == "__main__":
    unittest.main()
