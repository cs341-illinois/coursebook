# Future concerns for review

Items found during a full proofreading pass over every chapter that were
**deliberately not fixed**, because they need an author's judgement rather
than a copy-edit: technical claims that look wrong or outdated, garbled
sentences whose intent is unclear, structural gaps, and errors inside code
listings (where a "bug" is often the whole point of the example).

The language fixes from the same pass are in the accompanying commit. This
file is the leftovers.

## How to read this

- Items are grouped by chapter and carry `file:line` references. Line
  numbers refer to the commit this file was added in.
- **These findings are unverified unless marked otherwise.** They were
  produced by an automated pass and will contain false positives. Confirm
  before acting, especially on technical claims.
- The section immediately below is the exception: those items were checked
  by hand against the source and the published PDF.

---

## Verified by hand

### The PDF build cannot fail, so LaTeX errors accumulate silently

`Makefile:45,51` invoke latexmk as:

```
-@latexmk -interaction=nonstopmode -quiet -pdflatex=lualatex -f -pdf ... 2>&1 >/dev/null
```

Four separate things suppress failure: `-interaction=nonstopmode` does not
stop on errors, `-f` forces latexmk past them, the leading `-` makes GNU make
ignore the exit code, and `-quiet` plus the redirect hide the output. A
chapter can therefore contain real LaTeX errors, produce a damaged PDF, and
still show a green CI run.

Two such errors are live right now (both confirmed present in body text, not
inside listings):

- `processes/processes.tex:618,624` — `\begin{enunmerate}` / `\end{enunmerate}`.
  The environment `enunmerate` does not exist; this should be `enumerate`.
- `networking/networking.tex:448` — `\keyowrd{read}`, a typo for `\keyword`.
  Confirmed consequence: on page 254 of the published PDF the sentence reads
  "check the return value of read and write" with `read` in body font instead
  of code font, because LaTeX skipped the undefined macro.

Both are fixed in the accompanying commit. The build behaviour is not, and is
the more important issue: consider dropping `-f` and the leading `-` so that
a broken chapter fails the build instead of shipping quietly.

### Two source files are orphaned — written, but never built

- `introc/topics.tex` is never `\input`, and its content is duplicated
  verbatim inside `introc/introc.tex`. Editing the standalone file has no
  effect on the book.
- `honors/tcp.tex` is never `\input` by `honors/honors.tex`, and is a single
  truncated sentence.

Decide whether each should be wired in or deleted; leaving unreferenced
sources invites edits that silently do nothing.

### The POSIX signals table is rendering broken in the published PDF

`signals/signals.tex:70` declares `\begin{tabular}{|c|c|c|}` — three columns —
but every row supplies four cells. That is a fatal "Extra alignment tab"
error, swallowed by the build suppression described above.

Confirmed consequence: on **page 307 of the published PDF** the fourth column
breaks onto its own line for every row:

```
Name Portable Number Default Action
Usual Use
SIGINT 2 T erminate (Can be caught)
Stop a process nicely
```

Fixed in the accompanying commit (declared four columns). Listed here because
it is the third confirmed instance of a real LaTeX error surviving into the
published book, which is the strongest argument for tightening the build.

### `honors/containers.tex` has three empty subsections

"Linux Namespaces", "Building a container from scratch" and "Containers in
the wild" are headings with no body text. They render as empty sections in
the published book.

---

## introduction

### introduction/introduction.tex:6 — dangling pronoun "It"

> "It is a message etched into our Alma Mater and makes up the DNA of our course staff."

The preceding sentence's subject is "we", not a message, so "It" has no clear antecedent — the intended referent is presumably the *belief* stated in line 5. Rewriting requires knowing the author's intent, so flagging rather than changing.

### introduction/introduction.tex:14 — possibly stale staff URL

> \href{http://cs341.cs.illinois.edu/staff}{CS 341 course staff}

Plain `http` (not `https`) and a course-site path that may have moved between semesters. A human should confirm the link still resolves.

### introduction/introduction.tex:17 — vague link text

> "This work is based on the original coursebook located \href{...}{at this url}."

I removed a duplicated "at" ("located at ... at this url"). The remaining link text "at this url" is still non-descriptive, which is an accessibility concern for screen readers; naming the target (e.g. the original SystemProgramming wiki) would be better, but that is a wording change, so left to a human.

### introduction/introduction.tex:20 — reference to "the duck"

> "Oh and the duck? Keep reading until synchronization :)."

Depends on a duck image/joke appearing in the synchronization chapter. Worth a human check that the referenced content still exists in the current build; there is no `\ref{}` tying the two together.

### introduction/introduction.tex:28 — AUTHORS.md included as a code listing

> \lstinputlisting[language=console]{AUTHORS.md}

The Authors section renders a markdown file in a monospaced listing environment. If AUTHORS.md is missing or moves, the build breaks silently in terms of content; also renders prose as code, which is an accessibility/presentation concern. Human decision.

---

## background

### Stale per-student repository URL — background/background.tex:141

```
$ git clone https://github.com/illinois-cs-coursework/fa23_cs341_<netid>
```

Hardcodes the FA23 semester prefix. For FA26 this should be `fa26_cs341_<netid>` (or be written generically). Flagged as requested; needs a human to confirm the semester naming scheme actually in use.

### Wrong macro named for disabling assertions — background/background.tex:304

> "The \keyword{DEBUG} macro will disable all assertions, so don't forget to set that once you finish debugging"

The standard C macro that disables `assert()` is `NDEBUG`, not `DEBUG`. This looks like a genuine technical error (and elsewhere in the chapter, line 770, `DEBUG` is used to *enable* logging — the opposite sense). A human should confirm and correct.

### "Hyperthreading is a new technology" — background/background.tex:82

Hyper-Threading shipped commercially in 2002. Calling it "new" is dated. Also the subsection asserts it "is in no way shape or form multithreading", which is a strong claim a student may find confusing given the name. Needs an author decision on rewording.

### gdb transcript values look wrong — background/background.tex:611-617

```
(gdb) print (31415/1000)
$2 = 0x31
(gdb) print (31415/1000.0)
$3 = 201.749
```

`31415/1000` is 31 (`0x1f`, not `0x31`), and gdb's `print` does not inherit the `/x` format from the previous command anyway. `31415/1000.0` is `31.415`, not `201.749`. These appear to be fabricated/garbled outputs; since this is the punchline of the debugging walkthrough, a human should regenerate the real transcript. (Left untouched: inside `lstlisting`.)

### Valgrind example comment states the wrong reason — background/background.tex:338

```
}                    // error 2: Memory Leak, x is allocated at function exit.
```

The leak is that `x` is *not freed* at function exit; "is allocated" doesn't describe the error. Inside a listing so left alone, but it teaches the wrong wording.

### ltrace example output does not match its source — background/background.tex:670-687

The C snippet calls `fprintf(fp, "a")`, but the ltrace output shows `fwrite("Invalid Write\n", 1, 14, 0x0 ...)`. The string and length do not correspond to the program shown. A human should regenerate or reconcile the example.

### "Setting breakpoints programmatically" paragraph is self-contradictory — background/background.tex:443-489

The paragraph titled "Setting breakpoints programmatically" first shows the `asm("int $3")` technique (which *is* the programmatic one), then says "You can also set breakpoints programmatically" and demonstrates `break main.c:4` — an interactive, non-programmatic breakpoint. The labels appear swapped. Confusing for a first-time gdb user.

### Truncated memory address in prose — background/background.tex:533

> "starting at memory address \keyword{0x7fff5fbff9c}"

The gdb output above it shows `0x7fff5fbff9cd` (14 hex digits vs 13). Looks like a dropped character, but it is an address inside a `\keyword{}` so I did not touch it.

### "add one to the memory address 20" — background/background.tex:14

The instruction is `add BYTE PTR [0x20], 1`, i.e. address `0x20` = 32 decimal. Prose says "memory address 20", which a student will read as decimal 20. Suggest "0x20".

### Broken logic in the git-status troubleshooting flow — background/background.tex:168-201

"If you are currently on a branch, and you don't see either \<A\> or \<B\>" ... then line 193 continues "And something like \<C\>". The condition never resolves grammatically or logically: is the trigger *not* seeing A/B, or *seeing* C? As written a student can't tell what state means "don't panic, but your repository may be in an unworkable state". Needs an author rewrite.

### Undefined reference to "the \keyword{release}" — background/background.tex:203

> "delete your repository and re-clone (you'll have to add the \keyword{release} as above)"

Nothing "above" explains a `release` remote or branch — the git subsection only covers clone/add/commit/push and mentions a feedback branch. Missing context a student following this emergency procedure would need.

### Outdated strace claim — background/background.tex:729

> "The problem is as of early 2019, that version is missing from Ubuntu repositories."

Fault injection (`-e inject=`) has been in Ubuntu's strace for many releases now. Time-stamped claim that is almost certainly no longer true.

### Windows Subsystem for Linux named incorrectly — background/background.tex:126

> "you'll have to use the Windows Linux Subsystem"

The product is "Windows Subsystem for Linux" (WSL). Left as-is because it is a proper-noun/technical name rather than a plain typo.

### Markdown emphasis leaking into LaTeX — background/background.tex:1013

> "Did I include the console/GDB/Valgrind output **AND** code surrounding the bug"

`**AND**` is Markdown syntax; in LaTeX it renders as literal asterisks. Presumably should be `\textbf{AND}`. Not changed because it alters markup, not prose.

### Extra closing parenthesis in Homework 0 listing — background/background.tex:809

```
execlp("make","make", (char*)0));
```

One `)` too many. Might be a deliberate "spot the bug" element of the lyrics puzzle, so I left it — but it is worth confirming it is intentional.

### Grammatical error inside the HW0 `minted` block — background/background.tex:821

```
puts("Bring your near-completed answers the problems below");
```

Missing "to" ("answers to the problems below"). This is student-facing output text, but it lives inside a code listing, so I did not edit it.

### Generic Edstem link — background/background.tex:847-848

> "Use the current semester's CS341 Edstem: \url{https://edstem.org/}"

Left exactly as-is per instructions; noting only that it points at the site root rather than a course, which may be intentional.

### Inconsistent list-introduction punctuation — throughout

Several sentences that introduce an enumerate/lstlisting end without a period (e.g. lines 55, 126, 156, 207, 512, 972). This is consistent enough across the chapter to read as house style, so I left all of them alone rather than making a large punctuation-only diff.

---

## introc

### introc/the_c_and_linux.tex:36 — broken sentence about system calls
"Next, the kernel executes the system call to the best of its ability in kernel space and is a privileged operation."
The clause "and is a privileged operation" has no valid subject (the kernel is not the privileged operation). Needs a rewrite that a human should own, e.g. "...in kernel space; executing a system call is a privileged operation."

### introc/crash_course_introduction_to_c.tex:19 — incomplete sentence
"In C, no two functions can have the same name in a single compiled program, although shared libraries may be able."
"may be able" is missing its complement ("may be able to have duplicates"?). The intended claim about shared libraries/symbol interposition is unclear enough that a human should decide the wording.

### introc/language_facilities.tex:125 — garbled explanation of `extern`
"...so the program compiles on missing variable because the program will reference a variable in the system or another file."
"compiles on missing variable" is not grammatical and the causal clause is circular. Needs a real rewrite of the explanation.

### introc/language_facilities.tex:240 — mislabelled code comment
The fourth example in the if/else listing is commented `// (1)` but should be `// (4)` (it matches "an if with an else if and else" from line 214). It is inside a listing, so I did not touch it, but it looks like a genuine copy-paste error rather than a deliberate bug example.

### introc/language_facilities.tex:250-252 — `inline` description contradicts itself / wrong term
"tells the compiler it's okay to omit the C function call procedure and \"paste\" the code in the callee. Instead, the compiler is hinted at substituting..."
The code is pasted into the *caller*, not the callee. Also "Instead," makes no sense between the two sentences since they say the same thing. Technical claim — needs an author.

### introc/language_facilities.tex:255-256 — `max` returns the minimum
"inline int max(int a, int b) { return a < b ? a : b; }" returns the smaller value. This is in a listing so I left it, but nothing in the surrounding text suggests the bug is intentional (the example is about `inline`, not about a bug).

### introc/language_facilities.tex:265 — `restrict` wording
"tells the compiler that this particular memory region shouldn't overlap with all other memory regions" — "with all other" should probably be "with any other"; as written it is ambiguous and technically weaker than intended. Left alone as a semantics claim.

### introc/language_facilities.tex:347-352 — count mismatch
"\keyword{static} is a type specifier with three meanings." but only two enumerated items follow. Either a third meaning was dropped or the count is wrong.

### introc/language_facilities.tex:369 — ungrammatical struct definition
"C-structs are contiguous regions of memory that one can access specific elements of each memory as if they were separate variables."
The relative clause is broken; needs rewriting by someone who knows the intended sentence.

### introc/language_facilities.tex:497-498 — `void` / lvalue claim
"The other use of \keyword{void} is when you are defining an \keyword{lvalue}." and "it can be promoted to any time to any other type."
"any time" appears to be a typo for "any type", but the whole sentence (void* and lvalues) is technically confused, so I did not guess. Also "Pointer arithmetic with this pointer is undefined behavior" contradicts pointers.tex:147-148 which says gcc/clang permit it as a char*.

### introc/language_facilities.tex:565 — increment operator example looks wrong
"\keyword{a = 0; ++a == 1} and \keyword{a = 1; a++ == 0}."
The second should presumably be `a = 0; a++ == 0` (or `a = 1; a++ == 1`). As written the postfix example is false.

### introc/common_c_functions.tex:12 — broken sentence
"know that most functions in C handle errors return oriented."
Probably "handle errors in a return-oriented way". Needs an author's wording.

### introc/common_c_functions.tex:118-121 — sprintf/snprintf advice inverted
"If printf is dealing with variadic input, it is safer to use the former function..." The "former" of "\keyword{sprintf} or better \keyword{snprintf}" is `sprintf`, but the safe one — and the one shown under "// Variable length" in the listing — is `snprintf`. Reads as a factual error.

### introc/common_c_functions.tex:198-199 — "Instead of" appears to be backwards
"Also naturally like \keyword{printf}, \keyword{scanf} functions require valid pointers. Instead of pointing to valid memory, they need to also be writable."
The intended meaning is surely "In addition to pointing to valid memory, they need to be writable."

### introc/common_c_functions.tex:211 — prose refers to a variable that isn't in the example
"We wanted to write the character value into c..." but the listing declares `char type`, not `c`.

### introc/common_c_functions.tex:317 — broken sentence
"The caller has to be careful from a valid 0 and an error."
Presumably "has to distinguish a valid 0 from an error."

### introc/common_c_functions.tex:325 — missing semicolon in listing
"errno = 0" in the strtol errno-trampoline example has no semicolon, so the snippet would not compile. In a listing, and this example is not presented as buggy code, so it looks accidental.

### introc/common_c_functions.tex:240 — strlen/strcmp prototypes
"\keyword{int strlen(const char *s)}" — the real prototype returns `size_t`. Since these are presented as reference prototypes rather than bug examples, a human may want to correct it. Same section, line 242: strcmp is documented as returning exactly -1/0/1, which is not guaranteed by the standard (only the sign is).

### introc/common_c_functions.tex:341 — dangling fragment
"\keyword{memcpy} and \keyword{memmove} both in \keyword{string.h}?"
This is not a sentence and the itemize ends on it. Possibly a leftover note ("Why are memcpy and memmove both in string.h?").

### introc/c_memory_model.tex:9 — dangling reference
"Consider the contact struct declared above." Nothing is declared above — the struct listing comes *after* this sentence, and this is the first mention of it in the chapter.

### introc/c_memory_model.tex:75-76 — endianness claim vs. the figure
"We will assume that our machine is big endian. This means that the least significant byte is last." The following figure caption says the four bytes are "filled with 0006", which is the big-endian layout, so the text and figure agree — but the memory-layout example at lines 35-38 and the "zero length array" hack do not depend on endianness at all. Worth a human check that this aside is not confusing students.

### introc/c_memory_model.tex:211 — contradicts the rest of the section
"Unlike pointers, that hold addresses to variables on the heap, or stack, char arrays (string literals) point to read-only memory located in the data section of the program."
The section just spent a page explaining that char arrays are *mutable* copies and that string literals are the read-only ones. Equating "char arrays" with "string literals" here is backwards.

### introc/c_memory_model.tex:66-98 — figures have no alt text
The three \includegraphics figures (memory_model_empty.eps, memory_model_length.eps, memory_model_full.eps) rely on captions only. The captions are descriptive, but there is no alt-text mechanism for screen readers.

### introc/pointers.tex:94 — confusing sentence
"In addition to adding to an integer, pointers can be added to."
Presumably "In addition to being able to add integers to integers, you can add an integer to a pointer." As written it is close to meaningless.

### introc/pointers.tex:115 — Markdown markup left in LaTeX
"we are increasing the **integer** pointer by 1" uses Markdown bold inside a .tex file; it will render literally as asterisks. Should probably be \textbf{integer}.

### introc/pointers.tex:116 — attribution of the void-pointer rule
"POSIX standards forbid arithmetic on void pointers." It is ISO C, not POSIX, that makes arithmetic on `void*` a constraint violation (POSIX actually leans the other way for some interfaces). Technical claim — left alone.

### introc/logic_and_program_flow_mistakes.tex:26 — confusing and possibly wrong claim
"Most modern compilers disallows assigning variables a condition without parenthesis."
Compilers *warn* (-Wparentheses), they do not disallow it; and "assigning variables a condition" is garbled. I fixed only the verb agreement.

### introc/logic_and_program_flow_mistakes.tex:52 — logic inverted
"The compiler fails to catch this error because the programmer omitted the valid function prototype by including \keyword{time.h}."
The prototype is missing because the programmer *did not* include time.h. As written it says the opposite.

### introc/logic_and_program_flow_mistakes.tex:29 — example does not compile
"if (42 = answer)" is offered as "the quick way to fix" the previous bug, but assigning to a constant is a compile error, which is the actual point being made. The surrounding text never says so explicitly, so a student may read this as recommended working code.

### introc/introc.tex:25-73 vs introc/topics.tex — duplicated content
The "Topics" itemize in introc.tex:25-73 is byte-for-byte the same list as introc/topics.tex, and topics.tex is never \input by introc.tex. One of the two is dead/duplicated.

### introc/history_of_c.tex:6 — dated hardware claim
"it was made to target the most popular computers at the time, such as the PDP-7." C was developed on the PDP-11; the PDP-7 was the machine for the earlier B/assembly UNIX. Historical claim worth checking against the cited source.

### introc/crash_course_introduction_to_c.tex:29 — flushing claim
"If the newline isn't included, the buffer will not be flushed (i.e. the write will not complete immediately)." True only for a line-buffered stdout, and the buffer is still flushed at exit. common_c_functions.tex:99-101 states the nuanced version; this simplified claim may mislead.

### introc/crash_course_introduction_to_c.tex:112 — missing word
"taking the sizeof the pointer and dividing it by the size of the first entry" — reads as if a word is missing ("the size of the pointer"). I left it because `sizeof` is being used as an operator name and a fix could change the technical reading.

---

## processes

### processes/processes.tex:618,624 — `\begin{enunmerate}` / `\end{enunmerate}` is not a real environment
The nested option list under "The last parameter to waitpid is an option parameter." is wrapped in
`\begin{enunmerate}` ... `\end{enunmerate}` (misspelled `enumerate`). This is an undefined LaTeX
environment and will either fail to compile or be silently swallowed by a custom fallback. I did not
touch it because it is a LaTeX command name rather than prose, and because whoever owns the build
should confirm nothing else defines it.

### processes/processes.tex:657 — likely inverted technical claim about exit-status macros
"For example, a process' exit status won't be defined if the process isn't signaled." The exit status
(`WEXITSTATUS`) is meaningful when the process *exited* (`WIFEXITED`), not when it was signaled; the
signal number (`WTERMSIG`/`WSTOPSIG`) is what requires the signaled/stopped precondition. The next
sentence talks about `WIFSTOPPED`/`WSTOPSIG`, so this looks like a mixed-up example. Needs an author
decision, not a guess.

### processes/processes.tex:483,494 — example code calls `fork` without parentheses
Both fork-and-FILEs snippets use `if(!fork) {`, which takes the address of the function (always
non-NULL, so the branch never runs) instead of calling it. Presumably should be `if (!fork())`. It is
inside a listing, so I left it, but it is very likely an unintended bug rather than a teaching bug.

### processes/processes.tex:520,550 — unbalanced parentheses in the getline loop
`while((nread = getline(&buffer, &buffer_cap, file) != -1) {` has three opening parens and two
closing; it will not compile. Also the `!= -1` binds to the `getline` result before the assignment,
so `nread` gets 0/1. The surrounding prose is about buffering/fork semantics, so this looks accidental
rather than the intended lesson.

### processes/processes.tex:225 — sentence appears to contradict/duplicate line 223
"Another is to use the built-in \keyword{exec} command to kill all the user processes (you only have
one attempt at this)." then "Finally, you could reboot the system, but you only have one shot at this
with the exec function." The reboot option and the exec option are conflated, and the parenthetical is
repeated. Needs an author to say what was meant.

### processes/processes.tex:142 — "starts at ... and starts at a constant size"
"This section starts at the end of the text segment and starts at a constant size because the number of
globals is known at compile time." The second "starts at" reads like it should be "stays at" / "has a
constant size", but since this is a statement about segment layout I did not want to alter the meaning.
(Compare line 163, which says the BSS "is also static in size".)

### processes/processes.tex:142 vs 127 — two different definitions of "program break"
Line 127 says the program break is the top of the heap ("\keyword{malloc} may push the heap boundary --
called the program break -- upward"); line 142 says "The end of the data segment is called the
\keyword{program break}". Both are defensible historically, but stating both without comment will
confuse students.

### processes/processes.tex:928 — "environment variables cannot be read by an outside process"
On Linux an outside process with the right privileges can read `/proc/<pid>/environ`, so environment
variables are not a security boundary in the way this sentence implies. The intended point is probably
that they do not appear in `ps` output the way `argv` does. Worth an author correction.

### processes/processes.tex:834 — confusing claim about stdin/stdout/stderr after exec
"The operating system may open up 0, 1, 2 -- stdin, stdout, stderr, if they are closed after exec; most
of the time they leave them closed." Subject shifts from "operating system" to "they", and it is unclear
what a student should take away. Needs rewording by someone who knows which behavior is intended.

### processes/processes.tex:977 — question is cut off mid-sentence
"What is the difference between execs with a p and without a p? What does the operating system" — the
second question has no verb, object, or terminal punctuation. I cannot guess the intended completion.

### processes/processes.tex:683-692 — person shifts between "your" and "its"
"It is good practice to wait on your process' children. If a parent doesn't wait on your children they
become ... If a long-running parent never waits for your children ... Having said that, a program doesn't
always need to wait for your children! Your parent process can continue ..." The second-person "your"
is attached to the parent process rather than the reader, which reads as an error, but fixing it means
rewriting most of the paragraph, so I left it.

### processes/processes.tex:10 — dangling comparison
"most systems that we'll be studying are almost POSIX compatible due more to political reasons." "due
more to" invites a "than ..." that never arrives, and the claim itself (political reasons) is asserted
with no context a student could use.

### processes/processes.tex:812 — capitalization mismatch with the example
Prose says the example writes "Captain's Log"; the code at line 802 writes `"Captain's log"`. Trivial,
but the prose is quoting the program output.

### processes/processes.tex:185,340,881 — figures have captions but no alt text
`\includegraphics` of `address_space.eps`, `sleepsort_timing.eps`, and `fork_exec_wait.eps` carry only
`\caption{}`. For an accessible PDF these need real alternative descriptions (the sleepsort timing
diagram in particular carries information not present in its caption).

---

## malloc

### malloc/malloc.tex:9 — "use as its accord"
"a contiguous series of addresses that the program can expand or contract and use as its accord". "as its accord" is not an English idiom; likely intended "as it sees fit" or "at its discretion". Needs an author decision on intended meaning rather than a guess.

### malloc/malloc.tex:83 — "these limitations" has no antecedent
"An advanced discussion of these limitations is \href{...}{in this article}." The preceding sentence describes what `calloc` does; no limitations have been mentioned yet. A student cannot tell what limitations are meant. Also the linked host (locklessinc.com) may be dead — worth checking.

### ~~malloc/malloc.tex:85 — "calloc(x,y) is identical to calloc(y,x)"~~ WITHDRAWN — false positive
This item was raised and then **withdrawn on review**. The original claim
argued the book's statement was unsafe "once overflow checking is
considered", while simultaneously conceding that `n * size` overflow is
symmetric — which is self-contradictory. Multiplication is commutative, so
`calloc(x,y)` and `calloc(y,x)` request the same size and overflow at
exactly the same point. **The book is correct as written.** No action needed.

### malloc/malloc.tex:211 vs figure caption — "perfect-fit" vs "Best fit"
Prose says "A perfect-fit strategy finds the smallest hole"; the figure caption immediately below says "Best fit finds an exact match", and the rest of the chapter (and the Topics list) uses "Best Fit". Terminology inconsistency that could confuse a student; renaming is an editorial call.

### malloc/malloc.tex:237 — "don't need to replace the block"
"those placement strategies don't need to replace the block". Given the surrounding discussion of splitting and the following sentence about returning "the original block unbroken", this almost certainly should be "don't need to *split* the block". Changing it alters a technical claim, so flagging rather than fixing.

### malloc/malloc.tex:242 — "continuous block"
"it may be divided up in a way so a continuous block of that size is unavailable." Should almost certainly be "contiguous" — the standard term used elsewhere in this chapter (lines 8, 330). Flagged rather than fixed because it is a technical term.

### malloc/malloc.tex:266 — survey date vs citation
"a more rigorous survey conducted in 2005 \cite{10.1007/3-540-60368-9_19}". That DOI prefix (3-540-60368-9) is the 1995 Springer LNCS volume — Wilson, Johnstone, Neely & Boles, "Dynamic Storage Allocation: A Survey and Critical Review" (1995). The stated year appears wrong. Verify against malloc/malloc.bib.

### malloc/malloc.tex:290 — Fibonacci heaps claim
"Your heap could be represented with the max-heap data structure ... Using Fibonacci heaps, however, could be extremely inefficient." Fibonacci heaps have excellent amortized bounds; the claim as written is surprising and unexplained (presumably about constant factors / pointer overhead / cache behavior). Either justify or drop.

### malloc/malloc.tex:293 — next-fit definition is circular
"one is next-fit which is first fit on the next fit block" defines next-fit in terms of "the next fit block", which is undefined. A student reading only this sentence learns nothing. Needs a real one-line definition (resume the search where the last one stopped).

### malloc/malloc.tex:430-432 — broken quotation
The `quote` block ends: "...a multiple of 16 on 64-bit systems." For example, if you need to calculate how many 16 byte units are required, don't forget to round up." There is a stray closing double-quote mid-block, and the "For example..." sentence is the book's own commentary sitting inside the glibc quotation. Also the quoted text is self-contradictory ("always a multiple of eight on most systems"). Fixing requires deciding where the quotation actually ends, and possibly re-checking the glibc manual wording.

### malloc/malloc.tex:456-458 — free() sets is_free = 0
Prose says "A naive implementation would simply mark the block as unused. If we are storing the block allocation status in a bitfield, then we need to clear the bit", and the listing does `p->info.is_free = 0;`. With a field named `is_free`, marking a block unused means setting it to 1, not clearing it. Either the field name or the code is wrong. Not touched (code listing), but it reads as a genuine error rather than a deliberate teaching bug.

### malloc/malloc.tex:487 — incomplete sentence
"No more than 3 blocks will need to coalesce into a single block, and using a most recently used block scheme only one linked list entry." The second clause has no verb (presumably "...only one linked list entry needs to be updated"). Repairing it requires knowing the intended claim, so flagged rather than guessed.

### malloc/malloc.tex:646 — unit capitalization in exercise
"a new slab of 64kb ... allocating 1.5kb". Elsewhere the chapter uses KiB/KB consistently; "kb" reads as kilobits. Left alone since these are exercise numbers, but worth normalizing.

### Figures — no alt text
All figures (lines ~199-235, 306-319, 410-414, 475-479, 512-516, 530-534) use `\includegraphics` with a `\caption` only. The captions ("Malloc addition", "Free list good and bad coalesce") do not describe what the diagram shows, so a student using a screen reader or reading the text alone gets nothing. Accessibility improvement needs an author who knows the drawings.

---

## threads

### threads/threads.tex:510 — code listing references undeclared `stack` (compile error)

The listing declares:

```
  char *child_stack = malloc(STACK_SIZE);
```

but two lines later uses:

```
  char *stack_top = stack + STACK_SIZE;
```

`stack` is never declared; the printed example does not compile. Open PR #212 proposes exactly this fix (`stack` -> `child_stack`). Left untouched because it is inside a `lstlisting`. Needs a human to land the fix / reconcile with the PR.

### threads/threads.tex:495-496 — comment says 8 KiB but the macro is 8 MiB

```
// 8 KiB stacks
#define STACK_SIZE (8 * 1024 * 1024)
```

`8 * 1024 * 1024` is 8 MiB. Inside a listing, so not edited; a human should decide whether the comment or the constant is wrong.

### threads/threads.tex:500 — missing semicolon in listing

```
  puts("Hello Clone!")
```

No terminating semicolon; the example as printed does not compile.

### threads/threads.tex:501 — subject/verb in listing comment

```
  // This share the same heap and address space!
```

"This share" should be "This shares" (or "These share"), but it is inside a listing, so not edited.

### threads/threads.tex:351,354,357 — bugs in the "thread-safe" solution listing

```
    written = snprintf(buf, nbtytes, "%d : blah blah" , num);
```
`nbtytes` is a typo for `nbytes` (won't compile).

```
    buf[nbytes] = '\0';
```
Writes one past the end of a buffer of `nbytes` bytes — a buffer overflow in a listing presented as "one valid solution". Also, `strncpy` already NUL-terminates here since "Unknown" is short.

`return written <= nbytes;` returns a truth value from a function whose name/usage suggests a byte count; worth a human check.

### threads/threads.tex:324 — "Race conditions aren't in our code."

```
Race conditions aren't in our code.
They can be in provided code.
```

As written the first sentence flatly denies race conditions exist in our code, which contradicts the preceding examples. The intended meaning is almost certainly "aren't only in our code". Meaning-changing, so left for a human.

### threads/threads.tex:205 — sentence fragment / duplicated "means"

```
This means that the execution of the code is non-deterministic.
Meaning that the same program can run multiple times and depending on how the kernel schedules the threads could produce inaccurate results.
```

The second sentence is a fragment and repeats "means"; it also needs commas around the "depending on..." clause. Rewriting it is more than a mechanical fix.

### threads/threads.tex:32 — "processes" where "threads" is meant

```
\item When you want communication between the processes simplified
```

This bullet is in the list of reasons to prefer *threads*; "the processes" should probably be "threads". Technical wording, so not changed.

### threads/threads.tex:44 — missing qualifier changes the claim

```
It's easy to `free' the memory used by automatic variables because the program needs to change the stack pointer.
```

Intended sense is "because the program only needs to change the stack pointer". As printed the reasoning does not follow.

### threads/threads.tex:230-231 — confusing register description

```
We will assume that data is stored in the \keyword{eax} register.
The code to increment is the following with no optimization (assume int\_ptr contains eax).
```

"assume int_ptr contains eax" reverses the relationship, and the following assembly actually loads from `[rbp-4]`, not from a register holding `data`. Also the operation is a doubling, described as "increment". Needs an author's eye.

### threads/threads.tex:304 — description of the cast is inaccurate

```
We will instead treat i as a pointer and cast it by value.
```

The code passes the *value* of `i` cast to `void *`; "treat i as a pointer" is backwards, and "cast it by value" is not standard terminology. (The listing itself also uses `int data = ((int) ptr);`, which is implementation-defined on LP64 and normally warns.)

### threads/threads.tex:437 — complexity claim

```
The parallel algorithm runs in $O(\log^3(n))$ running time because the analysis assumes that we have a lot of cores.
```

The usual PRAM bound for parallel merge sort is $O(\log^2 n)$ (or $O(\log n)$ with the best merge). The exponent should be checked by a human.

### threads/threads.tex:3 — epigraph

```
\epigraph{If you think your programs were crashing before, wait until they crash ten times as fast}{}
```

I inserted the missing verb ("programs crashing" -> "programs were crashing"). The original may have been intended as "your program's crashing"; flagging in case the author prefers that reading. No terminal punctuation, left as-is (epigraph style).

### threads/threads.tex:551 — awkward question

```
What are a few things that threads share in a process? What are a few things that threads have different?
```

"have different" is ungrammatical but the intended phrasing ("that differ between threads"?) is a judgement call, so left alone.

---

## synchronization

### Output string in prose does not match the code

`synchronization/synchronization.tex:44` — prose says a typical output is `\keyword{ARGGGH sum is <some number less than expected>}`, but the listing above (and the later corrected listing) both `printf("ARRRRG sum is %d\n", sum)`. One of the two spellings should win; I left the code alone per instructions.

### Loop counts in prose contradict the code

`synchronization/synchronization.tex:212-214` — the code loops `10000000` times, but the prose says "we lock and unlock the mutex a million times" and "add one million using an automatic (local) variable". Also line 213, "we could have added up twice!", is hard to parse — presumably "we could have just added the total twice" or similar. Needs an author decision on the intended wording/number.

### Broken initializer inside a listing (deliberate or not?)

`synchronization/synchronization.tex:243` — `m2 = = PTHREAD_MUTEX_INITIALIZER;` has a doubled `=` and would not compile. The listing's point is that two different mutexes protect the same variable, so the doubled `=` looks like an accidental typo rather than a deliberate bug, but it is inside a listing so I did not touch it.

### Mutex description may be misleading

`synchronization/synchronization.tex:235-236` — "If a mutex is locked, the other threads will continue. It's only when a thread attempts to lock a mutex that is already locked, will the thread have to wait." The second sentence is ungrammatical (a mixed "It is only when… that…" / "Only when… will…" construction). Rewording touches a technical claim, so I left it.

### Wrong identifier in prose

`synchronization/synchronization.tex:311` — "both threads would read \keyword{m\_locked} as zero" refers to the field written `m->locked` in the listing above. Identifier, so not changed.

### Factually wrong sentence about mutex initialization

`synchronization/synchronization.tex:354` — "We set the state of the mutex to unlocked and set the owner to locked." The code sets `mtx->owner = UNASSIGNED_OWNER`. "set the owner to locked" is meaningless; likely should be "unassigned".

### Description of weak vs strong CAS is garbled and arguably backwards

`synchronization/synchronization.tex:393` — "there are two versions to these atomic functions a \emph{strong} and a \emph{weak} part, strong guarantees the success or failure while weak may fail even when the operation succeeds." Missing punctuation, "part" is the wrong noun, and "may fail even when the operation succeeds" is a confusing way to state spurious failure (weak may fail even when the comparison succeeded). Needs an author rewrite.

### Confusing mutual-exclusion justification

`synchronization/synchronization.tex:404-405` — "How does this guarantee mutual exclusion? When working with atomics we are unsure! But in this simple example, we can because the thread that can successfully expect the lock to be UNLOCKED (0) and swap it…". The sentence has no clear main clause ("we can" what?) and "successfully expect" is odd. Technical passage, left alone.

### Semaphore wait/post description

`synchronization/synchronization.tex:852` — "Remember \keyword{sem\_wait} will wait if the semaphore's count has been decremented to zero (by another thread calling sem\_post)." `sem_post` increments; a count reaches zero via `sem_wait`. Probably should read "by other threads calling sem\_wait".

### Semaphore-vs-mutex passage looks logically inverted

`synchronization/synchronization.tex:472` and `:527` — "That is usually why a mutex is used to implement a semaphore and vice versa." reads as a non-sequitur after the warning about breaking the mutex abstraction. And line 527, "binary semaphores are different than mutexes because one thread can unlock a mutex from a different thread", states the opposite of the book's own earlier rule ("The thread that locks a mutex is the only thread that can unlock it"). Presumably it should say a thread can `sem_post` a semaphore it never waited on. Factual — not fixed.

### Lock-inversion example explanation contradicts itself

`synchronization/synchronization.tex:490-491` and `:509` — "A mutex can handle what we call lock inversion well. Meaning the following code breaks with a traditional mutex, but produces a race condition with threads." followed later by "If we replace it with mutex lock, it won't work now." Both sentences seem to say the opposite of the intended point (the mutex version *is* the safe one, per the code comments "Foiled!" / "Now it's thread-safe"). Needs an author rewrite.

### Run-on sentence spanning a technical claim

`synchronization/synchronization.tex:531` — "\keyword{sem\_post} is one of a handful of functions that can be correctly used inside a signal handler \keyword{pthread\_mutex\_unlock} is not." Two sentences fused with no punctuation. I did not insert punctuation because the fix (semicolon vs. period vs. "whereas") changes emphasis on an async-signal-safety claim; a one-character insert is easy for the author.

### Structural: "Sketch #1" is never analysed; text jumps to Sketch #2

`synchronization/synchronization.tex:855-877` — the listing is labelled `// Sketch #1` and is syntactically broken (a `push` nested inside `pop`, unbalanced braces), and the very next paragraph starts "Sketch \#2 has implemented the \keyword{post} too early." Sketch #1 is never discussed. Reads like a missing paragraph.

### Typo'd identifier in a "correct" listing

`synchronization/synchronization.tex:935` — the fixed implementation calls `sem_init(&sremains, 0, SPACES)` while everything else uses `sremain`. As presented as the correct solution, this would not compile. In-listing, so not changed.

### Forward/backward cross-reference confusion

`synchronization/synchronization.tex:784-785` — "how would we fix the problems with condition variables? Try it out before you look at the code in the previous section." The condition-variable code being referenced follows immediately below, not in a previous section. Similarly line 810, "Does the following solution work?", appears *after* the listing it refers to.

### Wrong type name in the semaphore struct

`synchronization/synchronization.tex:1238` — `pthread_condition_t cv;` should be `pthread_cond_t`. Inside a listing, so not changed, but it will not compile as shown.

### "Notice that we are calling sem_post every single time"

`synchronization/synchronization.tex:1292` and `:1297` — the surrounding paragraph is about calling `pthread_cond_signal` unconditionally, so "calling \keyword{sem\_post} every single time" looks like the wrong function name. Also, the code comment in the optimisation snippet says "a thread sleeping inside sem\_post" where it means `sem_wait`.

### "Three actions" list only has two ordinals

`synchronization/synchronization.tex:1610-1612` — "performs \emph{Three} actions. Firstly, it atomically unlocks the mutex and then sleeps … Thirdly, the awoken thread must re-acquire the mutex lock". "Secondly" is missing; either split the first sentence or renumber.

### Peterson's solution walkthrough is a fragment and possibly wrong

`synchronization/synchronization.tex:1204-1206` — "If thread \#2 has set turn to 2 and is currently inside the critical section. Thread \#1 arrives, \emph{sets the turn back to 1} and now waits until thread 2 lowers the flag." The first sentence is a fragment, and in the pseudocode above each thread sets `turn = other_thread_id`, so thread #2 would set turn to 1 and thread #1 would set it to 2. Technical — not touched.

### Bounded-wait definition is awkward

`synchronization/synchronization.tex:1034` — "A thread/process cannot get superseded by another thread infinite amounts of time." Probably "an infinite number of times". Left because the fix is a judgement call on the intended definition.

### Shared-mutex example uses undeclared variable names

`synchronization/synchronization.tex:2097-2125` — the listing declares `pthread_mutex_t *mutex` and `pthread_mutexattr_t attr`, then `main` uses `pmutex` and `attrmutex` throughout, and `write_string` locks `mutex` (never assigned). The code as printed cannot compile and the two halves do not share a mutex. It also ignores `write` returning -1 in the retry loop. Needs an author fix.

### Garbled question

`synchronization/synchronization.tex:2267` — "How might the above be a producer consumer problem be used in the above section?" Doubled "be" and duplicated "the above"; the intended question is unclear.

### Possibly incomplete question prompt

`synchronization/synchronization.tex:2357` — "Remember in addition to mutual exclusion, a mutex can only ever be unlocked by the thread who called it." "the thread who called it" is missing what was called (presumably "the thread that locked it").

### Figure without alt text

`synchronization/synchronization.tex:1792-1795` — `\includegraphics{synchronization/drawings/ring_buffer.eps}` with only `\caption{Ring Buffer Visualization}`. No descriptive alternative text for a figure carrying real content (index wrap-around). Accessibility.

---

## deadlock

### deadlock/deadlock.tex:36-40 and 42-66 — cycle detection presented as sufficient for deadlock, and `isCyclic` conflates "visited" with "on the current DFS path"
The text says "If there is a cycle in the Resource Allocation Graph and each resource in the cycle provides only one instance, then the processes will deadlock", then presents pseudocode whose only check is `if (this graph has been visited)`. Marking a node visited permanently and returning true on any revisit reports a cycle for a re-encountered node that is merely already finished (a DAG with a diamond), rather than one on the current recursion stack. A correct DFS cycle check needs a separate on-stack/in-progress marker. **This overlaps with open PR #195**, which proposes replacing this algorithm; per instructions I did not touch it. A human should decide between fixing the marker logic here and adopting #195.

### deadlock/deadlock.tex:79 — "necessary *and* sufficient conditions ... non-zero probability"
"There are four \emph{necessary} and \emph{sufficient} conditions for deadlock -- meaning if these conditions hold then there is a non-zero probability that the system will deadlock at any given iteration." Sufficiency normally means deadlock *does* occur, not that it *may* occur with non-zero probability; the gloss contradicts the term. The Coffman conditions are standardly stated as necessary (and sufficient only for single-instance resources). Needs an author decision, not a copy-edit.

### deadlock/deadlock.tex:111 — garbled definition of the state functions
"$h_t: R \rightarrow P \cup \{\text{unassigned}\}$ that maps resources to the processes that own them (this is a function, meaning that we have mutual exclusion) and or unassigned and $w_t: ...$". The stray "and or unassigned and" makes the sentence unparseable. Rewriting it means deciding what the author meant, so I left it.

### deadlock/deadlock.tex:114 — "The evolution of the system is at each step at every time."
Not a sentence, and it introduces the bulleted transition rules. Probably intended something like "At each time step the system evolves as follows:". Needs an author's intent.

### deadlock/deadlock.tex:123-129 — proof of the reverse direction
Line 124 begins "More formally, this system is deadlocked means if $\exists t_0, ...$" (missing a word/"that"), and line 129 claims "Hold and wait simply proves the condition that from this point onward, the system will not change, which is all the conditions that we needed to show." The logic of what is assumed versus proved is hard to follow, and line 107 says "let us build a system with the three requirements not including circular wait" while the argument then uses circular wait (lines 127-128). This is a substantive correctness question about the proof, not a wording issue.

### deadlock/deadlock.tex:137 — pen/paper contradiction example is wrong
"a student would have to be waiting on a pen while holding the paper and the other waiting on a pen and holding the paper." Both students are described identically. For the contradiction to work the second student must be waiting on the *paper* while holding the *pen*. This is a factual error in the example; I did not silently correct it because the intended assignment of items should be confirmed against the ordering rule stated on line 135.

### deadlock/deadlock.tex:145 — "philosopher" appears before the Dining Philosophers section
The livelock paragraph continues the pen-and-paper students example but says "if the philosopher picks up the same device again and again". Dining Philosophers is not introduced until section 4 (line 181). A student reading linearly has no referent yet.

### deadlock/deadlock.tex:148 — "You must formally prove in a system by what is known as an invariant."
Missing an object ("prove *what*?"). Likely "You must formally prove freedom from livelock in a system by ...". Author's meaning needed.

### deadlock/deadlock.tex:161 — "What the algorithm refers to is that if there is an adversary -- or equivalently a user who poorly writes a program -- that the OS deadlocks."
The sentence has no main clause resolution ("if there is X ... that the OS deadlocks"). It is also the key point of the ostrich-algorithm paragraph, so a student is likely to be confused exactly where it matters.

### deadlock/deadlock.tex:188 — claim about the original problem
"The original problem required each philosopher to have two forks, but one can eat with a single fork so we rule this out." The reasoning is unclear (the problem is defined with two utensils precisely to create contention), and it sits oddly beside the chopstick framing on lines 185-187. A human should decide whether to keep, reword, or drop it.

### deadlock/deadlock.tex:221 — "This looks good but."
Reads as a truncated sentence. It may be a deliberate deadpan joke (the chapter is informal elsewhere), so I left it rather than adding "...". Flagging for the author to confirm.

### deadlock/deadlock.tex:299 — "with only one philosopher acting in pickup the left then the right fork"
Ungrammatical inside a proof; the intended sense is probably "acting under the pick-up-left-then-right rule". Since it is proof text, I left the wording to the author.

### deadlock/deadlock.tex:378-383 — Dijkstra proof reduction
Line 378 "If the last philosopher $p_{n-1}$ holds the first lock meaning the previous philosopher $p_{n-2}$ is waiting on $r_{n-1}$ meaning $r_{n-2}$ is available" is a run-on with no main verb, and line 380 concludes "we now have $n$ resources but only $n-1$ philosophers" without stating which philosopher was removed. Also line 379 uses "her" while the rest of the passage uses "he/his". The substance of the reduction needs an author's check.

### deadlock/deadlock.tex:390 — figure caption does not match its section
The figure at the end of the Dijkstra / Partial Ordering subsection is captioned "Stalling solution partial deadlock", referencing Stallings' solution from the previous subsection. The image file is `dining_partial.eps`, so the caption looks like a copy-paste error from line 348 ("Stalling solution almost deadlock"). Also note the chapter spells the author "Stallings'" in the section title but "Stalling" in both captions.

### deadlock/deadlock.tex:37 — bare `\ref` without a prefix
"then processes 1 and 2 will be deadlocked \ref{ragfigure}." renders as "...deadlocked 1.1." with no "Figure" word and no punctuation cue. Should probably be "(see Figure~\ref{ragfigure})". Left alone since it touches a cross-reference.

### deadlock/deadlock.tex:24-29, 68-72, 191-195, 227-231, 268-272, 303-307, 345-349, 387-391 — figures have no alt text
Eight `\includegraphics` calls, none with alt text; several carry load-bearing content (the deadlock cycle, the livelock time evolution, the arbitrator diagram). Only three of the eight are referenced from the prose at all (`ragfigure` is the sole `\label`), so a reader relying on a screen reader loses the content entirely. Needs an accessibility decision at the book level.

---

## ipc

### ipc/ipc.tex:130 — Sentence truncated mid-thought, number missing
> "Meaning we need roughly
> With $2^{52}$ entries, that's $2^{55}$ bytes (roughly 40 petabytes)."

"Meaning we need roughly" is a dangling fragment with the value missing. Also the arithmetic needs a human check: 52-bit entries rounded to 8 bytes x $2^{52}$ entries = $2^{55}$ bytes = 32 PiB (~36 PB), not "roughly 40 petabytes". Fixing requires deciding the intended number, so I left it.

### ipc/ipc.tex:184 — Multi-level page table size arithmetic is confusing/possibly wrong
> "shrunk from 4MiB for the single-level implementation to three page tables of memory or 2KiB for the top-level and 4KiB for the two intermediate levels of size 10KiB."

Ungrammatical and technically muddled: it says "two intermediate levels" when the surrounding text (line 186-188) describes two *sub-tables*, and "4KiB for the two intermediate levels" reads as 4KiB total while 2+4+4=10KiB implies 4KiB each. A human should restate this sentence.

### ipc/ipc.tex:204 — "cache coherence" appears to be the wrong term
> "if a program has inadequate cache coherence, the address will be missing in the TLB"

The intended concept is locality of reference / poor TLB hit rate; "cache coherence" means something else entirely. Technical wording, so not silently changed.

### ipc/ipc.tex:217 — "read and write" in MMU pseudocode
> "get the physical frame from the TLB and perform the read and write."

Should presumably be "the read or write" (a single access is either). Left alone as it is inside the algorithm description.

### ipc/ipc.tex:223 — Broken pseudocode step
> "If so then do the dereference provide the address, cache the results in the TLB"

Run-on with words apparently missing ("provide the address" is unattached) and no terminal punctuation. Intent unclear, needs an author.

### ipc/ipc.tex:248 — Sentence ends with a dangling verb
> "it all depends on if your hardware says that a program can access."

"can access" has no object (access what — that page?). Needs an author to complete.

### ipc/ipc.tex:331 — Possibly outdated/overly narrow claim about mmap
> "Currently it only supports regular files and POSIX \keyword{shmem}"

Linux mmap also supports anonymous mappings (used later in this very chapter at line 415 with MAP_ANONYMOUS), device files, hugetlbfs, etc. Technical claim — flagged, not changed.

### ipc/ipc.tex:335-341 — PROT_* flags attributed to the wrong mmap argument
> "The first option is that the \keyword{flags} argument of mmap can take many options."

The list that follows starts with PROT_READ / PROT_WRITE / PROT_EXEC / PROT_NONE, which belong to the `prot` argument, not `flags`; only MAP_SHARED / MAP_PRIVATE are `flags`. Also line 339 says "If this is supplied and \keyword{PROT\_NONE} is also supplied, the latter wins" — PROT_NONE is 0, so OR-ing it changes nothing; that claim looks wrong. Both are technical statements about mmap.

### ipc/ipc.tex:375,385,389-398 — Inconsistent variable name in the mmap walkthrough
The text and code define `page_offset` (line 375) but the argument list (line 385) says "pa\_offset" and the `munmap` call (line 398) uses `pa_offset`, which would not compile as written. Inside listings, so not touched.

### ipc/ipc.tex:495-503 — Example command and its explanation disagree on the filename
The command is `tee dirents` but the prose says "\keyword{tee} outputs the contents to the file \keyword{dir\_contents}". One of the two needs to change; a human should pick which.

### ipc/ipc.tex:636 — Badly broken sentence about pipe writes
> "If a process tries to write with some reader's read goes through, or fails -- partially or completely -- if the pipe is full."

Words are clearly missing/garbled; the intended meaning (a write succeeds if there is a reader, and may block or partially fail when the pipe is full) needs an author to restate.

### ipc/ipc.tex:645 — "your special byte" mixes person
> "a program could write your special byte (e.g.~0xff)"

Probably "a special byte". Left as-is since the chapter deliberately mixes second person elsewhere.

### ipc/ipc.tex:775-780 — fdopen example listing has real bugs
`open("mydata.txt", "w", O_CREAT, ...)` passes a string as the flags argument (should be `O_WRONLY | O_CREAT`), and the listing is missing its closing `return`/`}`. Inside a listing, so untouched, but this one does not look like a deliberate teaching bug.

### ipc/ipc.tex:859 — Reader/writer roles appear reversed
> "echo calls \keyword{open(..,\ O\_RDONLY)} but that blocks until cat calls \keyword{open(..,\ O\_WRONLY)}"

In the example above it, `echo Hello > fifo` is the *writer* (O_WRONLY) and `cat fifo` is the *reader* (O_RDONLY). The two look swapped. Technical claim, flagged rather than fixed.

### ipc/ipc.tex:890-901 — "Fine Pipe Access Pattern" table attributes print() to the wrong process
Time 4 lists "print() \& exit()" under Process 1, but Process 1 already did "close() \& exit()" at Time 3 and it is Process 2 that prints. Looks like a column error.

### ipc/ipc.tex:955,980 — "this"/"That quirk" with no antecedent
Section "Determining File Length" opens "using fseek and ftell is a simple way to accomplish this" (no prior referent), and section "Use stat instead" opens "This only works on some architectures and compilers. That quirk is that longs only need to be 4 Bytes big" — the quirk is named only after it is referred to. Reads as if an introductory sentence was lost.

### ipc/ipc.tex — Figures have no alt text
All figures (lines 72-76, 95-99, 104-108, 112-116, 143-147, 161-165, 169-173, 506-510) carry only short `\caption{}` text such as "Splitting Address" and "One level dereference". For an accessible PDF these diagrams — which carry the core address-translation explanation — need real descriptions.

---

## scheduling

### FCFS "Disadvantages" list duplicates the "Advantages" list verbatim
`scheduling/scheduling.tex:272-277`

The Disadvantages block reads:

> \item Simple algorithm and implementation
> \item Context switches infrequent when there are long-running processes

which is a word-for-word copy of the Advantages block at lines 266-270 (minus the third bullet). These are clearly not disadvantages of FCFS; the real ones (convoy effect, poor average response time for short jobs arriving behind long ones, no preemption) appear to have been lost. Needs an author to write the intended content — not a language fix. There is also a stray blank line before `\end{itemize}` at line 276.

### "Unless otherwise stated" is a dangling fragment
`scheduling/scheduling.tex:134`

The line introducing the shared example process list is just `Unless otherwise stated` with no verb and no terminal punctuation. Presumably intended as something like "Unless otherwise stated, the following processes are used in each example:". I did not guess at the intended wording.

### Cross-reference to "the appendix and the section conceptually scheduling" is informal/unverifiable
`scheduling/scheduling.tex:331`

> \textbf{If you need a math-y way of comparing scheduling algorithms, please check out the appendix and the section conceptually scheduling}

There is no `\ref`/`\label` here, and "the section conceptually scheduling" does not read like an actual section title. A human should confirm the target exists and ideally replace this with a real `\ref{}`. The sentence also has no terminal period, but I left it since the whole line may be rewritten.

### "time quanta" used as a singular noun
`scheduling/scheduling.tex:284-285`

> The maximum amount of time that a process can execute before being returned to the ready queue is called the time quanta.
> As the time quanta approaches infinity, ...

"quanta" is plural; the singular is "quantum" (and the chapter itself writes `Quantum = 1000ms` at line 307). Changing it is arguably a terminology decision for the course, so I left both occurrences alone. (I did fix "approaches to infinity" -> "approaches infinity" on line 285.)

### Stray capitalization "Convoy Behind them"
`scheduling/scheduling.tex:120`

> ...leaving all other processes with potentially smaller resource needs following like a Convoy Behind them.

"Behind" is capitalized mid-sentence for no apparent reason. It may be deliberate emphasis in this book's informal voice, so I left it. Also note "Convoy effect" (line 260) vs "Convoy Effect" (line 57) vs "convoy effect" (lines 118, 120, 262, 354) are inconsistently capitalized throughout.

### PSJF worked example: preemption description may not match the figure
`scheduling/scheduling.tex:213-220`

> Then P1 comes in at 1000ms, P2 runs for 2000ms, so our scheduler preemptively stops P2, and lets P1 run all the way through.

Two things a human should check against `scheduling/drawings/psjf.eps`: (a) the text says PSJF compares *total* runtimes (line 190), and P1 (1000ms) is strictly shorter than P2 (2000ms), so "the times are equal" / "completely up to the algorithm" (line 216) looks wrong here — the tie case is P4 vs P5, not P1 vs P2; (b) line 218 says "since the runtimes are equal to P5, the scheduler stops P5 and runs P4", but P4 is 4000ms and P5 is 5000ms, which are not equal. Per instructions I did not alter the example's logic or numbers.

### Figures have captions but no alt text
`scheduling/scheduling.tex:146-150, 193-197, 237-241, 287-291`

All four `\includegraphics` calls (sjf.eps, psjf.eps, fcfs.eps, rr.eps) carry only short captions such as "Shortest job first scheduling". The Gantt-chart content — arrival times, ordering, and the resulting timeline — exists only in the image, so a student using a screen reader gets none of it. Worth adding descriptive alt text or an in-text summary of each chart.

### "with a high priority" where "higher" is likely meant
`scheduling/scheduling.tex:66`

> Thus once a process is scheduled it will continue even if another process with a high priority appears on the ready queue.

The point being made is about a process of *higher* priority than the running one. Reads as a wording slip rather than a plain grammar error, so I left it for a human.

---

## networking

### OSI acronym expanded incorrectly — networking/networking.tex:19

"The Open Source Interconnection 7 layer model (OSI Model)". OSI stands for **Open Systems Interconnection**. This is a factual error in a definition students will memorize, but it is a technical claim so I did not change it.

### Outdated IPv4/IPv6 adoption statistics — networking/networking.tex:64, 73

"Even as of 2018, IPv4 still dominates Internet traffic, but Google reports that 24 countries now supply 15\% of their traffic through IPv6" and "However, little web traffic is IPv6 based on comparison as of 2018". These 2018 figures are badly stale (Google's IPv6 adoption is far higher now). Needs a human to refresh the numbers and the `\cite{internet_society_2018}` reference.

### "The world ran out of IP addresses a while ago" — networking/networking.tex:93

Loose claim; IANA exhausted the free pool in 2011 and RIRs at various later dates. A human may want to make this precise. Also line 96: "these addresses are leased not bought" — IPv4 addresses are also allocated/leased rather than owned, so the stated contrast with IPv4 is questionable.

### Garbled IPv4 address-splitting sentence — networking/networking.tex:70

"Conceptually the source and destination addresses can be split into two: a network number the upper bits and lower bits represent a particular host number on that network." The sentence has no working structure and a student cannot extract the network/host split from it. Rewriting requires deciding what was meant, so I left it.

### Confusing IPv6 address-notation description — networking/networking.tex:74-75

"We write IPv6 addresses in a sequence of eight, four hexadecimal delimiters like \"1F45:0000:...\"". "eight, four hexadecimal delimiters" is not meaningful — presumably "eight groups of four hexadecimal digits". Also "Since that can get unruly, we can omit the zeros \"1F45::\"" understates the `::`-may-appear-once rule. Technical wording, so left for a human.

### TCP expanded incorrectly — networking/networking.tex:242

"TCP or Transport Control Protocol". TCP is the **Transmission** Control Protocol. Factual naming error; not fixed per the technical-claims rule.

### "Ports" bullet says socket where it means port — networking/networking.tex:252-253

"TCP gives the programmer a set of virtual sockets. Clients specify the socket that you want the packet sent to". The concept being introduced is the *port*; calling it a socket here conflicts with the socket API introduced later and will confuse students.

### "High performance and error-prone code won't even assume that!" — networking/networking.tex:244

Unclear as written — presumably means high-performance / error-tolerant code should not assume delivery. As phrased ("error-prone code") it reads as praising buggy code. Needs an author decision.

### AF_INET4 does not exist — networking/networking.tex:379

"The other modes for `family` are \keyword{AF\_INET4} and \keyword{AF\_UNSPEC}". The correct constant is `AF_INET` (used correctly elsewhere in the chapter). Identifier, so not touched.

### AF_UNSPEC described backwards — networking/networking.tex:214

"One can specify IPv4 or IPv6 with \keyword{AF\_UNSPEC}." `AF_UNSPEC` means *unspecified* — it does not specify a version, it accepts either. Reads as a technical error.

### Garbled HTTP body description — networking/networking.tex:557

"The actual body of the request delimited by two new lines. The body of the request is either if the size is specified or until the receiver closes their connection." The second sentence is missing its predicate ("either read until the specified length..."). Needs an author rewrite.

### HTTP version/RFC currency — networking/networking.tex:574

"RFC 7231 has the most current specifications on the most common HTTP method today". RFC 7231 was obsoleted by RFC 9110 (HTTP Semantics, 2022), and the chapter's examples are all HTTP/1.0 while HTTP/1.1 and HTTP/2/3 dominate. A human should decide how much to update. Also line 553, "the HTTP/1.0 method" should probably be "protocol"/"version".

### Passive-socket paragraphs appear to have lost their negations — networking/networking.tex:589-593

Three consecutive "Instead" sentences with no preceding negative:
- "Passive server sockets wait for another host to connect. Instead, they wait for incoming connections."
- "Additionally, server sockets remain open when the peer disconnects. Instead, the client communicates with a separate active socket..."
These read as self-contradictory; the first clause of each pair was probably meant to be negative ("do not send/receive data", "are not used for data transfer"). Text repair needs the author.

### Same missing-negation problem for bind / TIME-WAIT — networking/networking.tex:602, 606-607

"It is possible to call bind on a TCP client." (probably "possible but not usual/necessary") and "By default, a port is released after some time when the server socket is closed. Instead, the port enters a ``TIMED-WAIT'' state." — the "Instead" contradicts the sentence before it; presumably "is *not* released immediately". Also the state is conventionally written `TIME-WAIT`, not `TIMED-WAIT`.

### SO_REUSEPORT vs SO_REUSEADDR — networking/networking.tex:611

"To be able to immediately reuse a port, specify \keyword{SO\_REUSEPORT} before binding". The TIME-WAIT problem being described is normally solved with `SO_REUSEADDR` (which the chapter's own example at line ~527 uses); `SO_REUSEPORT` has different semantics (load-balancing multiple listeners). Potentially wrong advice — needs a human.

### Level-triggered epoll described in terms of the wrong call — networking/networking.tex:1286

"Level triggered means that while the file descriptor has events on it, it will be returned by epoll when calling the ctl function." Events are returned by `epoll_wait`, not `epoll_ctl`. Same issue at line 1291: "ctl will reset the state to zero events".

### Vague claim about epoll vs select — networking/networking.tex:1214

"There are reasons to use epoll over select but due to interface, there are fundamental problems with doing so." Ungrammatical and the point is unrecoverable — is the problem with select's interface or epoll's? Needs the author.

### "There are a variety of function calls available to send UDP sockets" — networking/networking.tex:902

You send *packets*, not sockets. Likely "to send data over UDP sockets". I could not fix it without guessing the intent.

### Garbled UDP-vs-TCP efficiency sentence — networking/networking.tex:825

"TCP has \textit{decades} of optimization, meaning your protocol for its use cases needs to be more efficient that to be more beneficial to use it." Not parseable; needs an author rewrite (also contains a then/than-adjacent "that").

### Server stub sentence missing a word — networking/networking.tex:1361

"unmarshal the request into a valid in-memory data call the underlying implementation and send the result back". Probably "into a valid in-memory representation, call the underlying implementation, and send...". Comma/word insertion needs the author's intent.

### Interface-Description-Language sentence loses its subject — networking/networking.tex:1372

"Writing stub code by hand is painful, tedious, error-prone, difficult to maintain and difficult to reverse engineer the wire protocol from the implemented code." The final clause does not attach to the list.

### Bug in the RPC marshaling listing — networking/networking.tex:1330-1336

`int getHighScore(char* game)` but the body does `asprintf(&buffer,"getHiscore(%s)!", name);` — `name` is undeclared (should be `game`), and the comment says `'getHiscore'` while the function is `getHighScore`. Also `read(fd, buffer, sizeof(buffer))` uses `sizeof` on a `char*`. In a code listing, so possibly deliberate — but if not, students will copy it.

### "Unicode Text Format 8" — networking/networking.tex:1348

UTF-8 is "Unicode **Transformation** Format". Small factual naming error inside a technical list.

### DNS expanded as "Domain Name Service" — networking/networking.tex:1007, 1021

Conventionally "Domain Name System". Also line 1032 writes "DNSSec"; the standard capitalization is DNSSEC, and "recently issued a request" is undated and likely stale.

### Comma splice left as-is — networking/networking.tex:1319

"To marshal a linked list, it is unnecessary to send the link pointers, stream the values." Reads as a splice; the fix ("instead, stream the values") is a wording choice so I left it.

### "host-ordered ordering" — networking/networking.tex:333

"convert network ordered byte values to host-ordered ordering". Redundant/garbled; the natural fix is "host byte ordering" but it borders on style, so I left it.

### Figures have no alt text — networking/networking.tex:88-92, 236-240

Both `\includegraphics` figures (`ipv6_datagram.eps`, `tcp_header.eps`) carry only captions ("IPv6 Datagram divisibility", "Extra: TCP Header Specification") and no textual description. The IPv6 caption in particular does not explain what the diagram shows. Accessibility issue for screen-reader users.

---

## filesystems

### Permission bits described as "bytes", and read/execute swapped — filesystems.tex:599

> "For each digit, the least significant byte corresponds to read privileges, the middle one to write privileges and the final byte to execute privileges."

Two problems, both technical so left untouched: (a) these are *bits*, not bytes; (b) the ordering is backwards — in an octal digit the least significant bit is execute (1) and the most significant is read (4). As written it contradicts the "read(4), write(2), execute(1)" line at filesystems.tex:688 and the `755`/`644` table. Needs an author to rewrite.

### Garbled enumerate item in the chmod 755 example — filesystems.tex:693

> "\item r + w + x = digit * user has 4+2+1, full permission"

The "= digit \*" fragment looks like a mangled sub-bullet or a lost line break; the item also mixes the general rule and the user-specific case. The following two items ("group has...", "all users have...") are fine. Needs an author to decide the intended wording.

### uid said to live in `st_mode` — filesystems.tex:645

> "This owner's user ID (\keyword{uid}) can be found inside the \keyword{st\_mode} file of a \keyword{struct stat}"

The uid is in `st_uid`, not `st_mode`, and "file" should be "field". Both are technical/identifier changes, so not fixed here.

### `readdir` thread-safety advice appears inverted — filesystems.tex:370-371

> "\keyword{readdir} is not thread-safe! You shouldn't use the re-entrant version of the function."

The natural advice after "not thread-safe" is to *use* the re-entrant version (`readdir_r`), or to explain why `readdir_r` is deprecated in glibc and locking is preferred instead. As written the two sentences fight each other. Needs an author decision (the modern answer is "don't use `readdir_r`, use per-directory-stream locking", which the next sentence hints at but never says).

### Symlink `cat` example is internally inconsistent — filesystems.tex:425-446 (verbatim block)

`cat file1.txt` prints `file1!` but `cat file2.txt` prints `I'm file1!` even though `file2.txt` is a symlink to `file1.txt` and should print identical contents. Also `$ readlink myfile.txt` returns `file2.txt`, but `myfile.txt` is never created anywhere in the example — presumably it should be `readlink file2.txt` returning `file1.txt`. Inside a verbatim block, so not touched.

### ISO filename changes between mount example steps — filesystems.tex:950 vs 955 and 965

The download/mount commands use `archlinux-2015.04.01-dual.iso`, but the following prose and the `mount | grep arch` output use `archlinux-2014.11.01-dual.iso`. Filenames, so not touched — an author should pick one.

### `/dev/null/` with a trailing slash — filesystems.tex:811

> "Bytes sent to \keyword{/dev/null/} are never stored"

Every other mention is `/dev/null`. The trailing slash would actually fail (`/dev/null` is not a directory). Identifier, so not touched.

### "three times as slow" claim for indirection — filesystems.tex:226

> "This is three times as slow for reading between blocks, due to increased levels of indirection."

Unclear what the baseline is (three times slower than a direct block? than a single indirect block?), and the factor is asserted without justification. Ambiguous enough to need an author.

### Sentence fragment in the Google disk-failure statistics — filesystems.tex:1142

> "Multiplying that by 60,000+ disks in a single warehouse."

No main verb, and the conclusion (how many failures per day that implies) is never stated — a student cannot finish the arithmetic from what is given. Also worth a date check on the "2-10\% of disks fail per year" figure.

### RAID-10 description is hard to follow — filesystems.tex:1101-1105

> "This means you would get roughly the same speed from the slowdowns but now any one disk can fail and you can recover that disk."

"the same speed from the slowdowns" is not parseable, and the redundancy claim needs care: in RAID-10 any single disk can fail, and *some* two-disk failures are survivable while a mirror pair failing is not. Technical, so left alone.

### RAID-3 bottleneck reasoning — filesystems.tex:1114-1115

> "This means that there is effectively a bottleneck in a separate disk. In practice, this is more likely to cause a failure because one disk is being used 100\% of the time and once that disk fails then the other disks are more prone to failure."

"a bottleneck in a separate disk" is confusing (the bottleneck *is* the dedicated parity disk), and "once that disk fails then the other disks are more prone to failure" is a non-obvious causal claim that needs justification or removal.

### Write-to-file walkthrough mixes up inodes, data blocks, and indices — filesystems.tex:1253-1256

> "For this particular example we would have to go to the 2nd or indexed number 1 inode to perform our write."

This should almost certainly be the 2nd *data block* (the inode is a single object here), and the next sentence then says "go to the $5$th data block", which does not obviously follow from "2nd". Since the whole passage depends on the figure at filesystems.tex:1176, an author who can see the figure should reconcile the numbering.

### Follow-up question is garbled — filesystems.tex:1262

> "How would a program perform a write after adding the offset would extend the length of the file?"

Not a grammatical sentence, and it is unclear how it differs from the next question ("offset is greater than the length of the original file"). Left alone because the intended meaning is genuinely ambiguous.

### "0 being the inode root" — filesystems.tex:1164

> "The nth bit is set if the nth inode -- $0$ being the inode root -- is being used."

Almost certainly means "the root inode". Left alone in case "inode root" is intentional terminology for the minixfs model used here.

### Figure has no alt text — filesystems.tex:1174-1178

`\includegraphics{filesystems/images/sample_file.png}` with caption "Sample file filling up". The whole "Simple Filesystem Model" section (file size bounds, reads, writes) is written entirely against this image — a student using a screen reader, or reading the text alone, cannot follow any of the worked calculations. Adding a textual description of the inode's block pointers would fix this.

### `\begin {itemize}` with a stray space — filesystems.tex:1260

Compiles fine in LaTeX, but is inconsistent with every other environment in the file. Left alone as it is not a language issue.

### Fragment in "Writing to directories" — filesystems.tex:1268-1270

> "If we pretend that the example above is a directory. We know that we will be adding at most one directory entry at a time. Meaning that we have to have enough space for one directory entry in our data blocks."

Two sentence fragments in a row ("If we pretend..." with no main clause, and "Meaning that..."). Fixing them requires deciding what the sentences were meant to join to, so left to an author.

---

## signals

### signals.tex:66-81 — table has four column headers but only three declared columns
`\begin{tabular}{|c|c|c|}` is followed by `Name & Portable Number & Default Action & Usual Use \\ \hline` and four-cell data rows. This is a LaTeX error (extra alignment tab) and will either fail to compile or render wrong. Also, lines 66 and 81 are bare `\\` in vertical mode outside any paragraph, and the `table` float is nested inside `center`. Fixing the column count is a structural/authorial decision, so left alone.

### signals.tex:219 — `\keyword(...)` uses parentheses instead of braces
`\item We execute \keyword(func("Hello"))` — the macro argument delimiters are wrong (compare line 222, `\keyword{func("World")}`). Needs a human to confirm intended markup rather than a blind edit. Note also that lines 220 and 223 use bare `strcmp(...)` in prose without `\keyword{}`, inconsistent with the surrounding text.

### signals.tex:256 — `\keyword{\!pleaseStop}` likely wrong escape
The sentence reads "The expression `\keyword{\!pleaseStop}` doesn't get changed in the body of the loop". `\!` is a negative thin space (math mode); in text mode it is not the `!` operator the sentence means. Probably should be a literal `!`, but the correct escaping inside `\keyword` depends on how that macro is defined, so a human should decide.

### signals.tex:468 — "any signal thread"
"A signal then can be delivered to any signal thread that is willing to accept that signal." "signal thread" looks like a typo for "single thread" or just "thread", but the two readings say different things about delivery semantics, so I did not guess.

### signals.tex:7 — "Sometimes, a program can choose to ignore events which is supported."
Circular/confusing as written; it is unclear whether the point is that ignoring is a supported disposition, or that only some signals may be ignored (SIGKILL/SIGSTOP cannot). A student would benefit from the caveat being stated explicitly here.

### signals.tex:16 — chapter promise not delivered
"This chapter will go over how to read information from a process that has either exited or been signaled." Nothing in this chapter covers `wait`/`waitpid` status macros (`WIFSIGNALED`, `WTERMSIG`, ...); that material lives in the processes chapter. Either the sentence or a cross-reference needs updating.

### signals.tex:58-62 — figure has no alt text
`\includegraphics{signals/drawings/signal_lifecycle.eps}` with caption "Signal lifecycle diagram" only. The caption does not convey the lifecycle content to a reader using a screen reader, and the surrounding text (line 56, "As a flowchart") does not describe it either.

### signals.tex:312, 355 — sample code missing statement terminators
`sigaction(SIGALRM, &sa, NULL)` and `sigprocmask(SIG_SETMASK, &set, &oldset)` both lack a semicolon; line 214 `printf("%s\n", buffer)` likewise, and `func` at 210 has no `return`. Left untouched per the code-listing rule, but if these are not deliberate they will confuse students copying them.

### signals.tex:194-195 — pseudo-C in listing
`raise(int sig);` and `kill(getpid(), int sig);` use declaration syntax as if calls. Intentional shorthand or a mistake — a human should decide whether to write `raise(sig)` / `kill(getpid(), sig)`.

### signals.tex:188 — `killall -l firefox`
The comment says "kill a process by executable name", but `-l` on `killall` lists signal names (GNU) rather than killing by name; the plain `killall firefox` seems intended. Technical, so reported rather than fixed.

### signals.tex:198-200 — "You can't SIGKILL any process!"
Ambiguous: reads as "no process can be SIGKILLed" rather than the intended "you can't SIGKILL just any process". Also `man -s2 kill` is the Solaris/BSD form; on Linux it is `man 2 kill`. Both are judgment calls.

### signals.tex:262 — sig_atomic_t range claim
"can be as small as a \keyword{char} and only able to represent (-127 to 127) values" — a technical claim about limits (C requires at least SIG_ATOMIC_MIN/MAX coverage) that I did not want to touch.

### signals.tex:46 — "the process' signal mask"
Possessive of a singular noun ending in s-sound written as `process'`; elsewhere I normalized "processes mask" to "process's mask" (lines 431-432). Left line 46 alone to avoid churn, but the book should pick one convention.

---

## security

### Wrong statute name — security/security.tex:23

> "The computer fraud and security act is a broad, and arguably terrible law..."

The US statute is the **Computer Fraud and Abuse Act** (CFAA), not the "computer fraud and security act". Also uncapitalized. I did not rename it because it is a factual/legal claim; a human should confirm the intended statute (and note the law was narrowed by *Van Buren v. United States*, 2021, which post-dates this text's framing of "any non-authorized use ... as a felony").

### Ethics step 4 contradicts itself — security/security.tex:43

> "Execute the plan with caution. If at any point something seems wrong, weigh the risks and execute the plan."

The advice reads as "if something seems wrong, do it anyway". Almost certainly the intent was "weigh the risks and **halt**" / "re-evaluate before continuing". Needs an author decision on the intended verb.

### Step 2 refers to an antecedent that doesn't exist — security/security.tex:37

> "First, you should determine if your use is intended or unintended or somewhere in the middle -- get a decision from them."

"them" has no antecedent in the sentence (presumably the system's owners/developers). I fixed "for them" -> "from them" but the referent is still dangling.

### "In lieu" used without an object — security/security.tex:51

> "In lieu, you must be able to say that you reacted as a ``reasonable'' engineer would react."

"In lieu" requires "of X"; the intended phrase is probably "In lieu of that" or "Instead". Left alone as it may be deliberate shorthand.

### Spectre code example does not match its explanation — security/security.tex:180-202

Several mismatches a student would trip on:
- `char *a[10];` then `for (int i = 10; i != 1; --i) { a[i] = calloc(1,1); }` writes `a[10]`, which is out of bounds, and never allocates `a[1]`.
- The text says "The first loop allocates 9 elements" and "The last element is `0xCAFE`", but the code sets `a[0] = 0xCAFE` — the *first* element, not the last.
- `a[0] = 0xCAFE;` assigns an integer to a `char *` (would not compile cleanly).
- The second loop `for (int i = 10; i != 0; --i, --j)` shadows the outer `i` declared on line 188 ("This will be in main memory"), so the comment about register vs memory placement does not apply to the loop variable actually used.
- Text says "For the first 9 iterations, the branch is taken", but the loop runs 10 iterations.

This is presented as illustrative pseudo-code, but the index arithmetic contradicts the prose in a way that will confuse readers. Needs an author rewrite, not a copy-edit.

### ASLR example appears backwards — security/security.tex:231-234

> "This is so that an attacker with a running executable has to randomly guess where sensitive information could be hidden. For example, an attacker may use this to easily perform a `return-to-libc` attack."

ASLR *hinders* return-to-libc; as written it reads as though ASLR enables it. Likely the sentence meant "without this, an attacker may ...". Technical claim, so not fixed.

### "each user has a certain set of permissions that they can do" — security/security.tex:227

Grammatically mismatched ("permissions ... do") and conflates capabilities with permissions. Suggest "a certain set of capabilities" / "set of actions they are permitted to perform", but the wording sits inside a technical definition, so leaving to a human.

### sudo attributed to OpenBSD — security/security.tex:268-272

> "Sudo is an openBSD project that runs everywhere!"

sudo originated at SUNY/CU-Boulder and is maintained by Todd Miller (who is an OpenBSD developer), but it is not an OpenBSD project; OpenBSD's own tool is `doas`, and OpenBSD removed sudo from base in 2015. Attribution needs a human. ("openBSD" is also miscapitalized here vs "OpenBSD" elsewhere.)

### Containers described as "virtual machines" — security/security.tex:288

> "Containers are virtual machines that don't emulate all motherboard peripherals and instead share with the host operating system, adding in additional layers of security."

Containers are not VMs (they share the host kernel), and containers are generally considered a *weaker* isolation boundary than VMs, not "additional layers of security". Technical claim — flagged, not changed.

### DNS trust sentence is confusing — security/security.tex:324

> "One just has to trust the DNS server gave a reasonable response which is almost always the incorrect answer."

Unclear what "the incorrect answer" refers to — the DNS response, or the decision to trust it. Reads as a garbled sentence; needs the author's intent.

### Dated DHS/DNSSEC paragraph — security/security.tex:344-345

> "As of 2019, the United States Department of Homeland Security released a directive to switch all services from DNS to DNSSec ..."

Three issues for a human: (a) "As of 2019" is now seven years stale and the directive (ED 19-01) was actually about mitigating DNS infrastructure tampering, not a blanket "switch all services from DNS to DNSSec"; (b) DNSSEC is not a replacement for DNS, it is an extension that adds origin authentication — "switch from DNS to DNSSec" is misleading; (c) the following sentence, "This directive is an inherent flaw of the DNS system.", is a broken sentence — presumably "This directive is *a response to* an inherent flaw". I did not repair it because the correct rewrite depends on the intended claim. The URL itself was left untouched per instructions.

Also worth noting for a refresh: this section predates the now-widespread deployment of DNS-over-HTTPS/DNS-over-TLS, which line 348 ("DNS requests are sent as unsecured UDP packets") states without qualification.

### Review question 381 vs body text — security/security.tex:336 and 381

Line 336 already states "Distributed Denial of Service is the hardest form of attack to stop", which answers review question 10 ("Which is harder to defend against: Syn-Flooding or Distributed Denial of Service?") outright. Intentional? Possibly fine, but flagging.

### "HTTPs" capitalization — security/security.tex:320

> "a higher level protocol such as HTTPs"

Should be "HTTPS". Left alone since it is a protocol identifier and outside the low-risk list.

---

## review

### review/review.tex:135 — truncated bonus question
The item ends: "Bonus: How would you make this code more robust or able to cope with?" The sentence is cut off ("cope with" what — a long `mesg`? a `malloc` failure?). The same sentence also says "val as a double val", which looks like a duplicated word but might be intentional shorthand. Both need an author who knows the intended question; rewriting could change what is being asked.

### review/review.tex:150 — two questions merged by a Markdown-conversion artifact
Line reads: "Why should you check the return value of sscanf and scanf? \#\# Q 5.2 Why is `gets' dangerous?" The literal `\#\# Q 5.2` is a leftover Markdown heading, and it welds two separate questions into one `\item`. Splitting them into two items is an editorial/structural change, so leaving it to a human.

### review/review.tex:156-159 — question/sub-part structure is broken
"What mistake did the programmer make in the following code? Is it possible to fix it?" is followed by two bare lines "i) using heap memory?" and "ii) using global (static) memory?" which LaTeX will run together into one paragraph rather than rendering as a sub-list. Needs a real `enumerate` or line breaks — a formatting decision.

### review/review.tex:197-203 — question text is split across a code listing
"When would a trivial malloc implementation" / listing / "be acceptable?" I lowercased the stray capital "Be", but the sentence still reads oddly when the listing is set as a display block. A human may prefer to reword (e.g. "When would the trivial malloc implementation shown below be acceptable?").

### review/review.tex:322-337 — two items describe one problem, and item 2 has no question
Item at 322 sets up the graph/`shortest`/`set_edge` scenario and ends at line 335 with a requirement statement but no explicit question ("For performance, multiple threads must be able to call \keyword{shortest} at the same time..."). The next `\item` (337) then asks for the reader-writer implementation of the same scenario. These probably should be one item, or item 1 needs an actual question sentence.

### review/review.tex:519 — chmod question sentence is ungrammatical
"...so that the owner can read, write, and execute permissions the group can read and everyone else has no access." The verb "can" does not fit "permissions", and there is no punctuation separating the owner clause from the group clause. I only fixed the missing spaces after the commas; the rest is a rewrite that touches what the question asks (intended answer is presumably `chmod 740`), so a human should word it.

### review/review.tex:566 — handshake named incorrectly
"What is the SYN ACK ACK-SYN handshake?" The TCP three-way handshake is SYN, SYN-ACK, ACK. As written the term is wrong/garbled. Fixing it changes the technical content of the question, so flagging rather than editing.

### review/review.tex:607-613 — multiple-choice answer may be missing/ambiguous
"Assuming a network has a 20ms One Way Transit Time... how much time would it take to establish a TCP Connection?" Options are 20/40/100/60 ms. The three-way handshake is 1.5 RTT = 60ms to complete, but a connection is often counted as usable after 40ms (client can send with the final ACK). Which option is intended needs the author.

### review/review.tex:517 — "double direction table" corrected to "double indirection table"
I treated this as a typo and fixed it, but flagging in case "direction" was deliberate shorthand. Also note the item asks "What is the minimum file size required to require a single indirection table?" — "required to require" is clumsy but I left it because rewording risks changing the question.

### review/review.tex:649 — signal that "can not be caught"
Original: "Give the name of a signal that can not be caught by a signal". I added "handler" to complete the sentence. If the intended answer is SIGKILL/SIGSTOP, the fuller phrasing "cannot be caught, blocked, or ignored" may be preferable — an author call.

### review/review.tex:513,515,585 — space before question mark
Three items have "notes.txt} ?" / "listen accept ?" with a space before the "?". Left alone as it may be a deliberate consequence of the `\keyword{}` macro spacing, but a human may want them tightened.

---

## honors

### honors/tcp.tex:3 — chapter section is an unfinished fragment
The entire file is one truncated sentence: "TCP or the transmission control protocol handles the retransmission, acknowledgement, and flow of packets. Naturally a pre-requisite to this section is" — it stops mid-clause with no terminal punctuation. An author needs to finish the sentence and write the section; I cannot invent the missing content.

### honors/honors.tex:8-9 — tcp.tex is never included
`honors.tex` only does `\input{honors/kernel.tex}` and `\input{honors/containers.tex}`. `honors/tcp.tex` exists but is orphaned, so the "TCP In Depth" section never renders. Either finish and include it, or delete the file. Human decision.

### honors/containers.tex:23-27 — three empty subsections
`\subsection{Linux Namespaces}`, `\subsection{Building a container from scratch}`, and `\subsection{Containers in the wild: Software distribution is a Snap}` have no body text at all. They will render as bare headings in the student-facing PDF.

### honors/containers.tex:2-3 — dated statistic
"around 20 billion devices connected to the internet in 2018" — an eight-year-old figure presented in the present tense ("As we enter an era..."). Needs refreshing or rephrasing as a historical reference.

### honors/kernel.tex:29 — technically questionable claim about traps
"System Calls use an instruction that can be run by a program operating in userspace that \textit{traps} to the kernel (by use of a signal) to complete the call." The parenthetical "(by use of a signal)" conflates a hardware trap/software interrupt (`syscall`/`int 0x80`) with a POSIX signal, which are unrelated mechanisms. This is exactly the kind of subtle technical claim I was told not to silently rewrite, but it reads as wrong and students in CS 341 have already learned what signals are.

### honors/kernel.tex:11-13 — Windows/Darwin sentence was structurally broken
Original text read as two fragments: "...the Windows kernel, which we won't talk about too much in this chapter." followed by a new line beginning "or \keyword{Darwin}, the UNIX-like kernel for macOS...". I joined them with a comma (minimal fix), but the result now reads as "we won't talk about Windows or Darwin", which may not be the intended meaning — the original may have lost a clause such as "Others may have used XNU or Darwin". Please confirm the intended sentence.

### honors/kernel.tex:17-19 — micro-kernel description may be inaccurate
"A micro-kernel ... provides the bare-minimum functionality that a kernel needs. This involves setting up important device drivers, the root filesystem, paging..." Putting device drivers and the root filesystem *inside* the micro-kernel contradicts the next sentence, which says drivers and filesystems live outside as separate servers. Needs an author to reconcile.

### honors/kernel.tex:69-73 — commented-out TODO outline left in source
Five commented lines ("How to add a new system call?", "What is a kernel module?", "Example kernel module.", etc.) mark unwritten material. Flagging so the chapter's incompleteness is visible.

### honors/kernel.tex:13 — inconsistent capitalization of a project name
"\keyword{zircon}" is lowercase while "\keyword{GNU HURD}" is uppercase; the Fuchsia kernel is normally written "Zircon". I did not change it because it is inside a `\keyword{}` identifier.

---

## appendix

### appendix/appendix.tex:137 — `||` described incorrectly

> "\keyword{&&} only executes a command if the previous command succeeds, and \keyword{||} always executes the next command."

`||` runs the next command only if the previous one *fails*, not "always". The example immediately below (`false || echo "Hello!"`) is consistent with the correct semantics, so the prose contradicts the example. Also "The \keyword{&&} and \keyword{||} operator are operators that execute a command sequentially" is doubly awkward. Needs an author rewrite (technical claim).

### appendix/appendix.tex:358 — garbled sentence in the Fork-FILE explanation

> "Summarizing as if two file descriptors are actively being used, the behavior is undefined."

"Summarizing as" is not grammatical, and it is unclear whether the intended meaning is "Summarizing: if two file descriptors are actively being used..." or something narrower (POSIX's condition is about *handles* to the same open file description, not any two descriptors). Because the precise POSIX claim matters, a human should decide the wording.

### appendix/appendix.tex:442 — truncated sentence

> "Also, the messages now encounter additional overhead for serializing and deserializing or at the least."

The sentence ends mid-thought ("or at the least" what?). Needs the author to supply the missing clause.

### appendix/appendix.tex:592 — "a few filesystem hardware"

> "There are a few filesystem hardware nowadays that are truly cutting edge."

Ungrammatical count/mass mismatch; likely intended "a few filesystem hardware technologies" or "a few filesystems". Word choice is the author's call, and the section then discusses StoreMI (a hardware/software caching product), so the right noun is ambiguous.

### appendix/appendix.tex:639 — stray one-word paragraph "Yes"

Section `\subsection{Implementing Software Mutex}` opens with a bare line reading `Yes` before "With a bit of searching, it is possible to find it in production...". This looks like the answer to a question that was deleted (probably "Is Peterson's algorithm ever used in practice?"). The paragraph also has an unexplained "it". A human should restore the missing question or delete the line.

### appendix/appendix.tex:762 — double negative in a code comment

> `/* Even though the other thread is woken up it cannot not return */`

"cannot not return" should almost certainly be "cannot return". It is inside an `lstlisting`, so I left it untouched per instructions.

### appendix/appendix.tex:945-953 — Sequentially Consistent example does not match its explanation

The listing stores `x` = 1 then 0, and sets `y = 10`; the prose says:

> "This is because either the store happens before the if statement in thread 2 and y == 1 or the store happens after and x does not equal 2."

`y == 1` and `x does not equal 2` do not correspond to any value in the example (the values are `y == 10`, `x` in {0,1}). Also "Will never quit" is presumably "will never abort". This is a memory-model claim, so I did not touch it.

### appendix/appendix.tex:943 — Sequential consistency definition is hard to parse

> "This model says that any change that happens, all changes before it will be synchronized between all threads."

Grammatically broken and technically imprecise (sequential consistency is about a single total order of operations consistent with program order). Needs an author rewrite.

### appendix/appendix.tex:986 — duplicated/garbled clause introducing Go

> "We'll talk about a language go that is similar to C in terms of simplicity and design, go or golang"

The language name appears three times and the sentence has no terminal punctuation. Probably intended: "We'll talk about a language similar to C in terms of simplicity and design: Go (or golang)." Left alone because it is a rewrite, not a typo fix.

### appendix/appendix.tex:1139 — "variadic" used to mean "variable"

> "when $C > 1$ we say that the running times of the process are variadic"

"Variadic" means "taking a variable number of arguments"; the intended word is almost certainly "variable" or "highly variable". Same misuse appears at line 1387 ("a variadic, pyramid summation") and line 1444 ("this is variadic in size"). Terminology change — author's call.

### appendix/appendix.tex:1166 — "Conway and Al"

> "discovered by Conway and Al \cite{conway1967theory}"

This should be "Conway et al." I left it because it sits directly next to a `\cite{}` and could conceivably be an intentional (if odd) rendering.

### appendix/appendix.tex:1126 vs 1317 — inconsistent symbol for maximum run time

Line 1126 says "Let the maximum amount of time that a process runs be equal to $S$", but line 1317 says "$T$ is the maximum amount of time a process can run for". Meanwhile $S$ is used throughout as the *service time* random variable. A student following the derivations would be confused; needs the author to pick one symbol.

### appendix/appendix.tex:1288 — broken sentence

> "Imagine a series of FCFS queues that a process needs to wait your turn."

Mixes third and second person and is missing words. Rewrite needed.

### appendix/appendix.tex:1393 — dangling "either"

> "given a distribution of jobs that has either low waiting time as described above"

"Either" has no second alternative. Likely a dropped clause.

### appendix/appendix.tex:1416-1417 — IPv4 header field sizes are wrong

> "The first octet is the version number, either 4 or 6"
> "The next octet is how long the header is."

In IPv4 the version is 4 bits and IHL is the *other* 4 bits of the same first octet — not two separate octets. The subsequent items ("The next octet is various bit flags", "The next octet and half is fragment number") are likewise off: flags are 3 bits and fragment offset is 13 bits, sharing two octets. TTL and protocol are one octet each, which is correct. This whole enumeration needs a technical pass against the actual header layout.

### appendix/appendix.tex:1461 — orphan fragment in the routing list

> "These protocols are meant to be fast and more trusting because all computers, switches, and routers are part of an ISP.
> communication between two routers."

The last line is a lowercase sentence fragment with no context — apparently a leftover from an edit. Needs the author to restore or delete.

### appendix/appendix.tex:1494 — duplicated "assuming" and unclear claim

> "assuming the probability of receiving a packet assuming each fragment is lost with an independent percentage, the probability of successfully sending a packet drops off exponentially as packet size increases"

The sentence is garbled; I could not tell which "assuming" to drop or how the independence assumption was meant to be phrased.

### appendix/appendix.tex:1522 — garbled sentence about kqueue

> "kqueue is the truest sense of underlying descriptor agnostic."

Not a grammatical sentence; probably intended "kqueue is descriptor-agnostic in the truest sense." Rewrite needed.

### appendix/appendix.tex:1512 — product name capitalization

"MacOs" should be "macOS". Left alone because it borders on an identifier/product name and the book may spell it this way elsewhere.

### appendix/appendix.tex:171-198, 1409-1413 — figures have no alt text

`\includegraphics` for `struct_clean.eps`, `struct_slop.eps`, and `ip_datagram.eps` have captions ("Six box struct", "IP Datagram divisibility") but no descriptive alternative text. The IP datagram figure in particular carries information not otherwise in the text. Accessibility decision for the author.

---

## post_mortems

### "Ghandi" misspelled throughout (section title + prose)
`post_mortems/post_mortems.tex:162,166,168,170` — The section is titled `\section{Civilization and Ghandi}` and the prose repeats "Ghandi" three times. The correct spelling is **Gandhi** (the linked URL itself says `why-gandhi-is-always-a-warmongering-jerk-in-civilization`). I did not fix it because changing a `\section{}` title alters the ToC entry and any generated HTML anchor, and I was told not to touch names. A human should decide whether to rename the section (and fix all four occurrences together) — a half-fix would leave the chapter inconsistent.

### The "Gandhi nuclear aggression" story is a widely debunked myth
`post_mortems/post_mortems.tex:168-171` — "In the original, the game kept aggressiveness as an unsigned integer. During the game, the integer could be decremented and then the problem ensued because Ghandi was already at zero. This caused him to become the most aggressive character in the game." Sid Meier has stated in his memoir (*Sid Meier's Memoir!*, 2020) that this underflow bug never existed in *Civilization I*; the story is an internet legend that post-dates the game by ~20 years. Since this is presented to students as a real post-mortem with a concrete "lessons learned", a human should decide whether to remove it, or keep it and explicitly label it as apocryphal/illustrative.

### `$0` is described as "the first parameter passed into a script"
`post_mortems/post_mortems.tex:190` — "What happens if \$0 or the first parameter passed into a script doesn't exist?" In shell, `$0` is the *name/path of the script itself*, not the first parameter (`$1`). This is a technical inaccuracy in a C/shell course, and it is right next to a code listing I must not edit, so it needs a human. Also worth checking against the actual Steam bug, which hinged on `$STEAMROOT` being empty, not on `$0`.

### AT&T 1990: "operable when they weren't" may be backwards
`post_mortems/post_mortems.tex:215` — "A series of network delays that caused some telephone switches across the country to think that other switches were operable when they weren't." The usual account of the January 1990 AT&T collapse is that a switch went down for maintenance, and the *recovery* message it sent when coming back up crashed its neighbours via a misplaced `break` in C code — i.e. switches wrongly concluded peers were *inoperable*/failing. Either wording direction is a factual claim about a real incident, so I left it. Also note this sentence is a fragment ("A series of network delays that caused...") with no main verb.

### Appnexus double-free description is hard to follow
`post_mortems/post_mortems.tex:203` — "This is fine until two threads try to delete the same object at once, adding to the list twice. After less time, one of the objects was deleted, the delete was announced to other computers." "After less time" is meaningless as written, and the causal chain from double-add to outage is not explained. A student cannot reconstruct the bug from this. Needs a rewrite by someone who knows the incident.

### Mars Pathfinder paragraph: run-on and tense-mixing
`post_mortems/post_mortems.tex:74,76` — Line 74 mixes past and present ("The finder uses a single bus...", "if an interrupt happened ... and a task is running and a task is to be scheduled"). Line 76 is a comma splice: "The pattern that caused everything to start failing was the data collection thread starts writing to the bus, the information bus thread is waiting on the data." Fixing this properly means restructuring sentences, which is beyond a low-risk copy-edit. Note the classic name for this bug — priority inversion — is never stated, which is the one term a student would want.

### "Required Sections: Intro to C/Appending" — likely wrong section name
`post_mortems/post_mortems.tex:179` — Every other section lists real chapter names ("Intro to C", "Malloc", "Processes"). "Appending" looks like a typo for "Appendix" (the Shell Shock section uses "Appendix/Shell"). I did not guess. These "Required sections" lines are also plain text, not `\ref{}` cross-references, so nothing verifies they point at chapters that exist.

### Sentence fragment in the Sony rootkit section
`post_mortems/post_mortems.tex:156` — "What websites visited, what clicks or keys typed etc." has no verb. It reads as a deliberate telegraphic aside in an informal chapter, so I left it, but a human may want "What websites are visited, what clicks or keys are typed, etc."

### Meltdown and Spectre sections are stubs with unverifiable pointers
`post_mortems/post_mortems.tex:60-66` — "There is an example of this in the background section." / "Check in the security section." These are prose pointers, not `\ref{}`s, so they cannot be checked by the build and will silently rot if chapters are renamed or reordered. Consider real `\ref{}`s, or content.

### No `\label{}` anywhere in the chapter
`post_mortems/post_mortems.tex` (whole file) — The chapter and its ~16 sections define no labels, so nothing elsewhere in the book can cross-reference an individual post-mortem. Structural, and a human's call.

### Straight quotes in the opening line
`post_mortems/post_mortems.tex:5` — `a big "why are we learning all of this"` uses straight ASCII quotes; line 41 correctly uses LaTeX `` ``cat'' ``. This renders as two right-facing quotes in the PDF. Trivially fixable but it is typography, so flagging rather than changing.

---

