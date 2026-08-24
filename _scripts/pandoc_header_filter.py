#!/usr/bin/env python3

"""
Pandoc filter to grab the different header levels as yaml to stderr
"""

from panflute import run_filter, Str, Header, MetaMap, Image, Link
import sys
import atexit
import yaml
import os
import os.path
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
import dateutil.parser
import datetime
import requests

link_cache_days = 30

# Per-request timeout for the link check. Without this a host that
# blackholes connections stalls the build for minutes.
link_timeout_seconds = 15

# Metadata gleaned from the file
meta = dict(
    name="",
    bib_file="",
    subsections=[],
)

# Max header level
max_level = 2

# Cache of all the links
cache_file = os.environ['LINK_CACHE_FILE_NAME']
if not os.path.isfile(cache_file):
    link_cache = dict()
else:
    with open(cache_file, 'r') as f:
        link_cache = yaml.load(f, Loader=Loader)

default_image_alt = 'image'

class NoAltTagException(Exception):
    pass

class BadLinkException(Exception):
    pass

def exit_handler():
    """
    Loads a metadata file in the environment variable
    Opens and reads the file whether or not it exists.
    Then it overwrites the file with the extra metadata
    from the current tex file
    """
    meta_file_name = os.environ['META_FILE_NAME']
    with open(meta_file_name, 'r') as f:
        new_meta = yaml.load(f, Loader=Loader)
    if new_meta is None:
        new_meta = [meta]
    else:
        new_meta += [meta]

    out = yaml.dump(new_meta, Dumper=Dumper)
    with open(meta_file_name, 'w') as f:
        f.write(out)

    with open(cache_file, 'w+') as f:
        f.write(yaml.dump(link_cache, Dumper=Dumper))

def deserialize(x):
    """
    Takes a panflute element x and returns
    a basic stringified version of that element
    """

    if type(x) == Str:
        return x.text
    return ' '

def is_valid_cache_info(link_info):
    if link_info is None:
        return False
    date = dateutil.parser.parse(link_info)
    time_between = datetime.datetime.now() - date
    return time_between.days <= link_cache_days

def output_yaml(elem, doc):
    """
    This function performs a walk along a document and outputs to
    stderr a yaml file that has metadata about the name and the
    subsections of the chapter. Elem is a pandoc valid element
    doc is usually going to be None

    This also validates all images and links within a cache
    """
    if type(elem) == Image:
        # Get the number of chars for the alt tag
        alt_name = ''.join(map(deserialize, elem._content.list))
        alt_length = len(elem._content)
        # No alt means no compile
        # Accessibility by default
        if alt_length == 0 or alt_name.lower() == default_image_alt:
            raise NoAltTagException(elem.url)


    if type(elem) == Header and elem.level <= max_level:
        # Format what the title is going to look like
        name = ''.join(map(deserialize, elem.content.list))
        if elem.level == max_level:
            meta['subsections'].append(name)
        elif elem.level == 1:
            # If we are displaying a chapter, include a special entry for it
            meta['name'] = name
    if isinstance(elem, MetaMap):
        dictionary_map = elem._content
        if 'bibliography' in dictionary_map:
            bib_file = deserialize(dictionary_map['bibliography'][0].content[0])
            meta['bib_file'] = bib_file

    if isinstance(elem, Link):
        url = elem.url
        link_info = link_cache.get(url)

        # Ignore internal links for the time being
        # There are a lot of edge cases
        if not url.startswith('#') and not is_valid_cache_info(link_info):
            if not (url.startswith('http://') or url.startswith('https://')):
                raise BadLinkException(url)

            print('Requesting url "{}"'.format(url), file=sys.stderr)
            # Ping the image. A link we cannot reach is reported but is not
            # fatal: the build machine's connectivity is not a property of
            # the book. GitHub runners have no IPv6 route, for example, so
            # any host with an AAAA record (www.gnu.org) raises
            # "[Errno 101] Network is unreachable" even though it is fine.
            try:
                head = requests.head(url, timeout=link_timeout_seconds)
            except requests.exceptions.RequestException as e:
                print('WARNING: could not reach "{}": {}'.format(url, e),
                      file=sys.stderr)
                return elem

            if not (200 <= head.status_code <= 299):
                print('WARNING: url "{}" returned status {}'.format(
                    url, head.status_code), file=sys.stderr)

            # Otherwise reset the cache
            link_cache[url] = datetime.datetime.now().isoformat()

    return elem

def main(doc=None):
    atexit.register(exit_handler)
    return run_filter(output_yaml, doc=doc)

if __name__ == "__main__":
    main()
