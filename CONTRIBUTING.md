# Introduction

Thanks for taking the time to help contribute to the coursebook. We appreciate it!
If any of the upcoming sections is confusing, feel free to open an issue, and we'll take a look at it.

Following these guidelines helps accomplish a few things
1. Use the time of other developers and writers wisely
2. Helps in reducing technical debt
3. Keeps professionalism and high quality -- your work will be read by 100s of students every semester!

What kind of contributions are we looking for
* Anything in the issues is fair game!
* Anything you think is an issue is fair game, please make an issue and have a bit of a disucssion before implementing though!
* We are looking for pictures and other visual explanatory tools that help describe our topics
* We are looking for additional topics as well. These won't be part of the core that students are required to read, but will help if we choose to either bring them in or if students are having trouble understanding without the intuition.
* Additional explanations. Sometimes even though our explanations aren't enough.

## Philosophy

We provide an open, accessible, first class systems programming textbook that will be free to use forever. Plain and simple.
We want this information to be available to everyone without cost.

* Easily understandable
* In depth when need be
* Skimmable when need be
* Error free with citations
* Highly polished `Perfection is what we expect, excellence will be tolerated`

# Ground Rules

Responsibilities
* Add yourself to `AUTHORS.md`! We want your work to be recognized :D
* Ensure each piece of code compiles on both the site and the pdf according to our travis builds
* Discuss major changes before implementing
* Be welcoming to systems experts and newbies alike
* Have a professional attitude

# Development environment

## Wiki Dev Environment

To get started with a development environment, make sure you have an up-to-date version of `python3` on your system.
We perfer to use virtualenvironments so that python packages don't conflict. To create one, make sure you have `virtualenv` installed and perform the following commands

```
$ virtualenv -p python3 env
$ source env/bin/activate
(env) $
```

Then to install python dependencies do the following

```
(env) $ python -m pip install -r requirements.txt
```

This will help you build the wiki version of the book. This is the one that gets put into the site. To build that, just run

```
(env) $ mkdir out
(env) $ python _scripts/gen_wiki.py order.yaml out
```

And the markdown will be generated!

## PDF Dev Environment

To get the latex/pdf environment set up, it is a bit easier.
Make sure you have `texlive-full` or the equivalent installed on your machine.

```
$ sudo apt install texlive-full
```

Then to make the whole pdf it is

```
$ make main.pdf
```

To make any chapter it is

```
$ make introc/introc.pdf
```

For those of you unfamiliar to latex, feel free to peruse one of the many online resources. For a scenic tour, I recommend <https://learnxinyminutes.com/docs/latex/>

### Optional Build dependecies

If you'd like the project to automatically recompile as you make changes, run `./rebuilder.sh` instead. You need inotify tools.

* inotify-tools (`sudo apt install inotify-tools` on recent debian/ubuntu distros)

By default, `./rebuilder.sh` will create a new file in `/tmp/` and will re-use it every time it is ran for logging purposes. If a command line argument is specified, `./rebuilder.sh` will treat the argument as a path and will use that as its logging file instead.

## Figure Alt Text

Every content figure must have non-empty `alt={...}` text on its `\includegraphics` command.
The CI check verifies that alt text is present, but it cannot verify that the description matches the figure.
Any PR that changes an `alt=` value or a figure must include a rendered list of the changed alt texts next to their figures so reviewers can check their accuracy.

# Your First Contribution

To start contributing, feel free to take an issue or find a problem, file an issue and start working on it.
For those of you who have never contributed to open source before, here are a few links <http://makeapullrequest.com/> and <http://www.firsttimersonly.com/>
If a maintainer asks you to "rebase" your PR, they're saying that a lot of code has changed, and that you need to update your branch so it's easier to merge.

# Getting started

Want to contribute? Afraid of latex or python? Don't be!

If you want to contribute, all you need to do is
1. Fork
2. Make the changes by
    1. Going to the appropriate chapter
    2. Make changes either online or on the command line
    3. Make a PR
3. The PR will be cleared up and on build, a new version of the couresbook will be released and deployed!

If you want to actually contribute to the code, you'll need `texlive-full` and `python3`

```
sudo apt install texlive-full
python3 -V
```

Install all of the requirements in the requirements.txt file at the top of the repository.
We recommend doing this in a virtualenvironment as to not mess up other packages

```
virtualenv -p python3.5 env
source env/bin/activate
pip install -r requirements.txt
```

To generate a wiki version, it is a simple as

```
mkdir out
python3 _scripts/gen_wiki.py order.yaml out
```

To generate the pdf it is as simple as

```
make
```

If you find a security vulnerability, do NOT open an issue. Email angrave@illinois.edu instead.


# Writing Style

To make sure the book has a consistent tone among authors, we'll use the general writing style

* `we` are the authors or the general we. Anything that is a recommendation or a fact should start with this.
    * We recommend that you don't use `signal`
    * Don't fork after creating threads, we don't know the state of mutexes.
* `you` is the reader or the programmer. If we tell someone to do this or do that, make sure to use `you`.
    * You should be careful using `gets`
* `program/process` refers to a written program that is running. Don't use you here.
    * The process sends a signal to the other process
* Try to keep it generally formal. Asking rhetorical questions is okay.
* Avoid using i.e.
* Spell out numbers unless they are used in calculation, numbers never start sentences.
* Use the SI KiB KB system.
* Label code figures instead of saying `the following figure`
* There is no general rule for sections/subsections. Try to avoid using subsubsections.
* Use `\keyword` to highlight a common executable program, system or library call, or man page entry.
* Opt for citations rather than links because they allow for smoother reading.
* Break each sentence into its own line.
* Don't use 'I' ever
* Only use 'you' to refer to things that a _human_ can do. A human can read the man page or change code, but a human cannot access a memory location.
* Aim for resolute rather than pedantic language
* Avoid negative language
    * "This function does not work"
    * "This function fails"
* Avoid using filler words the following is a shortlist
    * "really"
    * "just"
    * "very"
    * "basically"
* Avoid using ellipses when not in a quote or a mathematical argument. It is otherwise viewed as informal.
    * Let S = {1, 2, ...}
    * "He was right ... she couldn't have it all"
* Pronouns should refer to the non-object noun of the previous sentence or clause unless completely unambiguous, but makes for confusing prose.
    * She and I were walking on the sidewalk. We thought it was a nice day.
    * She and I were walking on the sidewalk. It was hard and rocky.
* Introduce Abbreviations before using them
    * Hyper Text Markup Language (HTML) is ... HTML is the backbone of the web.
* Use plural antecedents to avoid gendering unless needed
    * "Programmers love readable code. They edit that code quickly."
    * "The banker keeps track of the number of resources. She makes a list of resources"

# Code Style

* Opt for small snippets of code and explainations around them. We want people who are learning to craft their own functions.
* Two spaces is an indent.
* The type of bracket style is the following
```c
if (1) {

} else if (2) {

} else {

}
```

* Opt for magic numbers defined in the text than code that compiles through.
* No headers unless they are the topic of conversation (like talking about preprocessors)
* Don't every say "NULL Byte" correct terminology is "NUL Byte"

# Structure

Since our wiki is used for the markdown version of the textbook for easy perusing, our high-level documentation is located here.

- All files in the `order.yaml` file are a chapter in the coursebook
  a chapter is a tex file with bib files and optional images
- `github_redefinitions.tex` - Various redefinitions so that pandoc can convert latex files to markdown. These are just pasted before each of the chapter files
- `glossary.tex` - Various glossary files
- `latexmkrc` - Configuration file for latexmk. Currently, it only deals with glossary generation.
- `LICENSE` - Licenses all the code in the book
- `main.tex` - The top level tex files that compiles all the other files
- `Makefile` Tried and true makefile for buildings. We don't need ya fancy build systems
- `order.yaml` This file controls the ordering of the chapter. Changing this and typing make will cause `order.tex` to be reformatted.
- `prelude.tex` contains all of the includes and definitions before the start of the document in main. This is a different file solely so that we can accurately convert each chapter with pandoc. More in the `_scripts/gen_wiki.py`
- `rebuilder.sh` Efficiently autobuilds the files for maximum productivity
- `requirements.txt` python requirements if you are building the `wiki` version of the coursebook
- `_scripts` This folder contains various scripts to do different things like generate the wiki, spellcheck etc.

The wiki version is built by travis using one of the scripts and is pushed to this site's wiki.
It also generates a site build on our github pages site to build an HTML version free of access.

The PDF version is also built by travis which generates a full book pdf and chapter by chapter pdf.

# Versioning

To version the repo you should use <term><year>-num . The term-year combo are simple way of denoting that this is the version of the book for the current semester. `num` is simply an incrementer for bug fixes, or material that was already covered in lecture and just needs to be added to the book. No `num` release will introduce no material that was not introduced in lecture or is not extra.
