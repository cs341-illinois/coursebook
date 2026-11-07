# Current
* [Jah-yee] Fix the margin overflow in the mutex-initialization paragraph: the
  `pthread_mutex_init(&m, NULL)` call now starts on its own line instead of running
  past the page margin (#255).
* [Name] [Change]
* [Lawrence Angrave] Figure alt text now reaches readers in all three outputs (#238): the PDF is tagged and carries each figure's /Alt, pandoc 3 delivers the `alt=` key to the EPUB and the wiki, and CI keeps every content figure's alt text in place.
* [Wu Shuwen] Alt-text lint: fail when a figure sits in a `.tex` file that nothing the book builds reaches, so a figure orphaned out of the book is caught instead of passing unnoticed; and report a malformed `\includegraphics` instead of skipping it.
* [Wu Shuwen] CI: compare the pandoc AST of `main.tex` before and after a pandoc change, reporting the element-count difference and checking that wiki citations still render as links, with both versions' EPUB, wiki and AST kept as artifacts.
* [Lawrence Angrave, Cay Zhang] Deadlock: replace the resource allocation graph cycle detection snippet with a correct directed graph DFS, and explain why the "already seen" shortcut reports deadlocks that do not exist.

# Previous
