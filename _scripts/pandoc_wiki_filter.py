#!/usr/bin/env python3

"""Convert Pandoc figures to accessible Markdown for the GitHub wiki."""

import os.path

import panflute as pf

from alt_text import image_alt_text, inlines_from_alt


base_raw_url = 'https://raw.githubusercontent.com/illinois-cs241/coursebook/master/'
eps_ext = '.eps'


def replace_suffix(content, suffix_old, suffix_new):
    if content.endswith(suffix_old):
        return content[:-len(suffix_old)] + suffix_new
    return content


def _wiki_image(image):
    alt = image_alt_text(image)
    url = replace_suffix(image.url, eps_ext, '.png')
    if url.startswith(base_raw_url):
        url = url[len(base_raw_url):]
    if not os.path.isfile(url):
        raise ValueError('{} Not found'.format(url))
    return pf.Image(
        *inlines_from_alt(alt),
        url=base_raw_url + url,
        title=image.title,
        identifier=image.identifier,
        classes=list(image.classes),
        attributes=dict(image.attributes),
    )


def doc_filter(elem, doc):
    if isinstance(elem, pf.Figure):
        images = []
        for block in elem.content:
            if isinstance(block, pf.Image):
                images.append(block)
            elif isinstance(block, (pf.Para, pf.Plain)):
                if any(not isinstance(child, pf.Image) for child in block.content):
                    raise ValueError('Unsupported content inside figure')
                images.extend(block.content)
            else:
                raise ValueError('Unsupported block inside figure')

        if not images:
            return None

        markdown_images = []
        for image in images:
            if markdown_images:
                markdown_images.append(pf.Space())
            markdown_images.append(_wiki_image(image))

        result = [pf.Para(*markdown_images)]
        caption = []
        if elem.caption is not None:
            for block in elem.caption.content:
                if isinstance(block, (pf.Para, pf.Plain)):
                    caption.extend(block.content)
                else:
                    caption.extend(inlines_from_alt(pf.stringify(block)))
        if caption:
            result.append(pf.Para(*caption))
        return result

    if isinstance(elem, pf.Image):
        return _wiki_image(elem)

    if isinstance(elem, pf.Math):
        return pf.RawInline("$$ {} $$".format(elem.text))

    if isinstance(elem, pf.Link):
        # Raw HTML keeps links unambiguous in GitHub's wiki Markdown parser.
        title = str(elem.title) or elem.url
        return pf.RawInline('<a href="{}">{}</a>'.format(elem.url, title))


def main(doc=None):
    return pf.run_filter(doc_filter, doc=doc)


if __name__ == "__main__":
    main()
