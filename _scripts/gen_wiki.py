#!/usr/bin/env python3

"""
Converts all the listed tex files to markdown counterparts and generates a directory page
"""

import argparse

import glob
import os
import yaml
import argparse
import subprocess
from jinja2 import Template
import tempfile
import logging
import sys
from multiprocessing import Pool
import multiprocessing

help_text="""
Generates a valid github wiki given a chapter ordering and output folder
"""

logging.basicConfig(
    format="%(asctime)s %(levelname)s: %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger()


# Configuration variables

filter_template = "_scripts/pandoc_header_filter.py"
# prelude file absolute location
prelude_file = 'prelude.tex'
# Compatibility with github
github_shim = 'github_redefinitions.tex'
# Weird glyph that appears regex
# Do all ops in the /tmp directory
tmp_dir = '/tmp/'
# Cache file directory
cache_file_dir = os.path.join(os.path.expanduser('~'), 'cache')
os.makedirs(cache_file_dir, exist_ok=True)

cache_file_name = os.path.join(cache_file_dir, 'link_cache.json')

class ConvertableTexFile(object):
    """
    Represents all the data needed to convert a tex file into
    its markdown counterpart
    """

    def __init__(self, bare_name, tex_name, meta, outdir):
        self.tex_path = tex_name
        self.pdf_path = os.path.basename(os.path.splitext(tex_name)[0]) + '.pdf'
        self.meta = meta
        self.bare_name = bare_name
        self.bare_title = self.bare_name.title()
        self.md_name = self.bare_title + '.md'
        self.md_path = outdir + '/' + self.md_name

# What will show up on the home page
jinja_templ = """
# Coursebook

<p align="center">
    <img src="https://raw.githubusercontent.com/illinois-cs241/coursebook/master/_images/duck-alpha-cropped.png" alt="Coursebook logo" width="50%" class="emoji"/>
</p>

This coursebook is being built by students and faculty from the University of Illinois. It is based on a crowd-source authoring wikibook experiment by Lawrence Angrave from CS @ Illinois, but is now its own .tex based project. Its source code is located at [the Github link](https://github.com/illinois-cs241/coursebook) which you can find a pdf version of the book as well.

This book is an introduction to programming in C, and system programming (processes, threads, synchronization, networking and more!). We assume you've already had some programming experience, in an earlier computer science course. If you have any typos to report or content to request, feel free to file an issue at the link above. Happy Reading!

<h3 id="one-big-pdf" class="title-text"><a href="https://github.com/illinois-cs241/coursebook/tree/pdf_deploy/main.pdf?raw=true" alt="PDF Version" class="wiki-link">One Big PDF<img src="https://raw.githubusercontent.com/illinois-cs241/coursebook/master/_images/pdf_icon.png" alt="PDF file icon" style="margin-left: 10px;" width="auto" height="50px"> </a></h3>

<h3 id="one-big-epub" class="title-text"><a href="https://github.com/illinois-cs241/coursebook/tree/epub_deploy/main.epub?raw=true" alt="Epub Versions" class="wiki-link">One Big EPUB<img src="https://raw.githubusercontent.com/illinois-cs241/coursebook/master/_images/epub_icon.png" alt="EPUB file icon" style="margin-left: 10px;" width="auto" height="50px"> </a></h3>


{% for chapter in chapters %}
## {{loop.index}}. [{{chapter.meta['name']}}](./{{chapter.bare_title}}) [<img src="https://raw.githubusercontent.com/illinois-cs241/coursebook/master/_images/pdf_icon.png" alt="PDF file icon" width="auto" height="50px" />](https://github.com/illinois-cs241/coursebook/blob/pdf_deploy/{{chapter.pdf_path}}) {% for section_name in (chapter.meta['subsections'] or []) %}
{{loop.index}}. [{{section_name}}](./{{chapter.bare_title}}#{{section_name.lower().replace(' ', '-')}}){% endfor %}
{% endfor %}
"""

sidebar_templ = """
{% for chapter in chapters %}
{{loop.index}}. [{{chapter.meta['name']}}](./{{chapter.bare_title}}){% endfor %}
"""

def gen_home_page(files_meta, out_file):
    """
    Generates the home page given metadata and output file

    :param files_meta List[ConvertableTexFiles]: Convertable tex file metadata in order
    :param out_file str: Output home directory file
    """

    tmpl = Template(jinja_templ)
    rendered = tmpl.render(chapters=files_meta)
    logger.info("Making {}".format(out_file))
    with open(out_file, "w") as f:
        f.write(rendered)

def gen_sidebar(files_meta, out_file):
    """
    Generates the sidebar

    :param files_meta List[ConvertableTexFiles]: Convertable tex file metadata in order
    :param out_file str: Output home directory file
    """

    tmpl = Template(sidebar_templ)
    rendered = tmpl.render(chapters=files_meta)
    logger.info("Making {}".format(out_file))
    with open(out_file, "w") as f:
        f.write(rendered)


def generate_tex_meta(order, outdir, meta_file_name, chapter=None):
    """
    Generates a list of ConvertableTexFile objects given an order file
    an output directory, and a temporary meta file name

    :param order: List[str] Order of the chapters without the .tex extension
    :param outdir: str The output directory, must be created
    :param meta_file_name: str The metadata file, must be able to be written to
    :param chatper: str Optional chapter to include
    """

    # Set the environment variables so all the subprocess calls know
    # Where to output the data
    os.environ['META_FILE_NAME'] = meta_file_name

    os.environ['LINK_CACHE_FILE_NAME'] = cache_file_name
    # Order file does not have suffixes
    logger.info("Generating Metadata at {}".format(meta_file_name))

    out_tex_names = []
    order_converted = []

    for path in order:
        tex_name = path + '.tex'
        if chapter is not None:
            if not tex_name.endswith(chapter + '.tex'):
                continue

        logger.info("Adding {}".format(tex_name))
        # Performa  walk with pandoc along the tree, outputting meta to a file
        command = ['pandoc',
                    '--filter',
                    filter_template,
                    '-s',
                    '--quiet',
                    tex_name,
                    '-o',
                    '-B',
                    prelude_file,
                    '-B',
                    github_shim,
                    '/dev/null']
        subprocess.check_call(command)
        order_converted.append(path)
        out_tex_names.append(tex_name)

    # Load that file back up
    with open(meta_file_name, 'r') as f:
        metadata = yaml.load(f, Loader=yaml.Loader)

    # Convert that meta to our datastructures so we aren't referencing magic keys
    ret = []
    for i in range(len(order_converted)):
        bare_name = os.path.basename(order_converted[i])
        tex_name = out_tex_names[i]
        meta = metadata[i]
        to_append = ConvertableTexFile(bare_name, tex_name, meta, outdir)
        ret.append(to_append)
    return ret

def convert_latex_to_md(files_m):
    """
    Converts a particular latex file to markdown

    :param files_m ConvertableTexFiles: Metadata for a current file
    """

    tex_path = files_m.tex_path
    # Createa  named temp file to not get raced by the file system
    with tempfile.NamedTemporaryFile(mode='wb', prefix=tmp_dir) as fp:
        tex_tmp_path = fp.name

        # Create a standalone document, all the tex chapters are chapters
        # So they need a prelude, compatibility later put in
        # pandoc can handle the fact there is no \begin{document}
        # so long as all the other libs are there
        cat_command = ['cat', prelude_file, github_shim, tex_path]
        subprocess.check_call(cat_command, stdout=fp)

        # Time to tdo the actual converting
        md_path = files_m.md_path
        command = ['pandoc',
                    '--toc', #generate Table of Contents
                    '--standalone', # Should be a standalone document
                    '-f', # Input format
                    'latex',
                    '-t', # Output format
                    'gfm+raw_html+autolink_bare_uris-tex_math_dollars',
                    # Github Flavored Markdown + Add raw HTML + link any bare HTTPS;//
                    # + get mathjax to display correctly
                    '-s', # Create a standalone wiki page not a fragment
                    '--citeproc', # Keep citeproc before the custom filters.
                    # Otherwise our filter can't process citations
                    '--filter',
                    '_scripts/pandoc_wiki_filter.py', # Give it to our filter
                    '-M', # Add some metadata
                    'link-citations=true', # Put in html links for citations
                    tex_tmp_path, # Convert our standalone document
                    '-o',
                    md_path] # Output to this file

        # If there is a bibliography file (not every chapter needs one)
        # Run pandoc with that to generate citations
        maybe_bib = files_m.meta['bib_file']
        if maybe_bib != '':
            command += ['--bibliography', maybe_bib]
        logger.info(' '.join(command))
        subprocess.check_call(command)


def main(args):
    """
    Converts tex files into their markdown versions
    """

    order_file = args.order_file
    outdir = args.outdir
    chapter = args.chapter

    with open(order_file, 'r') as order_f:
        order = yaml.load(order_f, Loader=yaml.Loader)

    logger.info("Creating Metadata")
    with tempfile.NamedTemporaryFile(mode='r', prefix=tmp_dir) as fp:
        meta_file_name = fp.name
        files_meta = generate_tex_meta(order, outdir, meta_file_name, chapter=args.chapter)

    if args.chapter is not None:
        files_meta = list(filter(lambda f: chapter.lower() == f.bare_name.lower(), files_meta))
        if len(files_meta) == 0:
            raise ValueError("No Chapter Found")

    # 1. Convert files in the order
    num_cores_usable = max(multiprocessing.cpu_count()-1, 1)
    logger.info("Converting files to markdown using {} cores".format(num_cores_usable))

    # Use a pool to speed things up somewhat
    # We are running with tempfiles so we won't
    # Get raced by the filesystem
    with Pool(num_cores_usable) as p:
        p.map(convert_latex_to_md, files_meta)

    if args.chapter is None:
        # 3. Generate Home Page
        home_file = os.path.join(outdir, 'Home.md')
        sidebar_file = os.path.join(outdir, '_Sidebar.md')
        gen_home_page(files_meta, home_file)
        gen_sidebar(files_meta, sidebar_file)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(help_text)
    parser.add_argument('order_file')
    parser.add_argument('outdir')
    parser.add_argument('-c', '--chapter', type=str, help='Optional output chapter')
    args = parser.parse_args()
    main(args)
