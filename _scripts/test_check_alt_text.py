import unittest

from check_alt_text import scan_source


class AltTextScannerTests(unittest.TestCase):
    def test_multiline_options_and_nested_braces(self):
        source = r"""\begin{figure}
\includegraphics[
  width=.5\textwidth,
  alt={A {nested, phrase} with a comma}
]{diagram.eps}
\caption{A short caption}
\end{figure}
"""
        report = scan_source("networking/sample.tex", source)
        self.assertEqual(report["errors"], [])
        self.assertEqual(len(report["figures"]), 1)
        self.assertEqual(report["figures"][0]["alt"], "A {nested, phrase} with a comma")
        self.assertEqual(report["figures"][0]["file"], "diagram.eps")

    def test_tex_and_percent_comments_are_ignored(self):
        source = r"""% \includegraphics[alt={commented}]{ignored.png}
\begin{comment}
\includegraphics[alt={}]{also-ignored.png}
\end{comment}
\includegraphics[alt={A visible \% sign}]{visible.png}
"""
        report = scan_source("sample.tex", source)
        self.assertEqual(report["errors"], [])
        self.assertEqual(len(report["figures"]), 1)
        self.assertEqual(report["figures"][0]["file"], "visible.png")

    def test_missing_empty_and_whitespace_alt_are_errors(self):
        source = r"""\includegraphics[width=1in]{missing.png}
\includegraphics[alt={}]{empty.png}
\includegraphics[alt={   }]{spaces.png}
"""
        report = scan_source("sample.tex", source)
        self.assertEqual(len(report["errors"]), 3)

    def test_caption_generic_and_latex_warnings(self):
        source = r"""\begin{figure}
\includegraphics[alt={Short caption}]{caption.png}
\caption{Short caption}
\end{figure}
\includegraphics[alt={diagram}]{generic.png}
\includegraphics[alt={c\_str}]{escaped.png}
"""
        report = scan_source("sample.tex", source)
        warnings = [warning for figure in report["figures"] for warning in figure["warnings"]]
        self.assertIn("alt text repeats the figure caption", warnings)
        self.assertIn("alt text is a generic label", warnings)
        self.assertIn("alt text contains a LaTeX escape or command", warnings)

    def test_title_allowlist_is_limited_to_named_lines(self):
        lines = [""] * 41
        lines[11] = r"\let\oldgraphics\includegraphics"
        lines[12] = r"\renewcommand{\includegraphics}[2][]{}"
        lines[28] = r"\includegraphics[width=10cm]{_images/duck.png}"
        lines[40] = r"\let\includegraphics\oldgraphics"
        report = scan_source("title.tex", "\n".join(lines))
        self.assertEqual(report["errors"], [])
        self.assertEqual(report["figures"], [])
        self.assertEqual(report["macro_definitions"], [12, 13, 41])
        self.assertEqual(report["decorative"][0]["line"], 29)


if __name__ == "__main__":
    unittest.main()
