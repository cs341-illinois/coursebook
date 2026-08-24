#!/bin/bash

set -o errexit

# Install packages that we need for python. Python3.6 is already installed
pip install -r requirements.txt

if test $BUILD_FOCUS = "WIKI" || test $BUILD_FOCUS = "EPUB"
then
    # Install pandoc from source because Ubuntu is high outdated
    pushd ~
    wget https://github.com/jgm/pandoc/releases/download/2.7/pandoc-2.7-1-amd64.deb
    sudo dpkg -i pandoc-2.7-1-amd64.deb
    popd
fi;

if test $BUILD_FOCUS = "PDF"
then
    # texlive-full drags in 455 packages / 4.0 GB -- every language pack,
    # ConTeXt, Metapost, the lot -- and is the reason this job takes ~9
    # minutes. The book needs 68 packages / 768 MB, listed below.
    #
    # Which package provides what (checked with apt-file on Ubuntu 24.04):
    #   latex-base        book.cls fontenc geometry graphicx color hyperref
    #                     natbib fancyhdr longtable grfext epstopdf-base
    #   latex-recommended microtype listings xcolor setspace float chapterbib
    #   latex-extra       mdframed mfirstuc comment framed glossaries titlesec
    #                     tocloft wrapfig changepage csquotes epigraph fncychap
    #   pictures          pgffor
    #   fonts-recommended Charter type1 (bchr8a.pfb), Latin Modern
    #   fonts-extra       mathdesign / mdbch. 614 MB of the 768 MB, so
    #                     most of the remaining install time, but it is
    #                     the only place mathdesign lives and it sets the
    #                     book's body font. Dropping it changes every page.
    #   luatex            lualatex, which the Makefile builds with
    #   font-utils        epstopdf, for the 47 .eps drawings
    #   latexmk           every build in the Makefile goes through latexmk
    #   ghostscript       epstopdf's backend
    sudo apt-get update -qq
    sudo apt-get install -y --no-install-recommends \
        texlive-latex-base \
        texlive-latex-recommended \
        texlive-latex-extra \
        texlive-fonts-recommended \
        texlive-fonts-extra \
        texlive-pictures \
        texlive-luatex \
        texlive-font-utils \
        latexmk \
        ghostscript
fi;
