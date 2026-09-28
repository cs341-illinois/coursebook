#!/usr/bin/env python3

"""
Pandoc filter to change each relative URL to absolute
"""

from panflute import run_filter, Image
import os.path

from alt_text import image_alt_text, set_image_alt_text

def replace_suffix(content, suffix_old, suffix_new):
    ret = content
    if content.endswith(suffix_old):
        ret = content[:-len(suffix_old)] + suffix_new
    return ret

def doc_filter(elem, doc):
    if type(elem) == Image:
        set_image_alt_text(elem, image_alt_text(elem))

        # Otherwise link to the raw user link instead of relative
        # That way the wiki and the site will have valid links automagically
        new_url = replace_suffix(elem.url, '.eps', '.png')
        if not os.path.isfile(new_url):
            raise ValueError('{} Not found'.format(new_url))
        elem.url = new_url
        return elem


def main(doc=None):
    return run_filter(doc_filter, doc=doc)

if __name__ == "__main__":
    main()
