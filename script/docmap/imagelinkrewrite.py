from markdown.preprocessors import Preprocessor
import markdown.inlinepatterns as ilp
from markdown.inlinepatterns import ImagePattern, handleAttributes
from markdown.extensions import Extension
import markdown
from markdown import util, odict
from pprint import pprint
import re
try:  # pragma: no cover
    from urllib.parse import urlparse, urlunparse, quote
except ImportError:  # pragma: no cover
    from urlparse import urlparse, urlunparse
try:  # pragma: no cover
    from html import entities
except ImportError:  # pragma: no cover
    import htmlentitydefs as entities

NOBRACKET = ilp.NOBRACKET
BRK = ilp.BRK
IMAGE_LINK_RE = ilp.IMAGE_LINK_RE

class RewriteImagePattern(ImagePattern):
    '''Replace image links with references to GITHUB'''

    def __init__(self, pattern, directory_url, markdown_instance):
        """ Replaces matches with some text. """
        self.directory_url = directory_url
        super(RewriteImagePattern, self).__init__(pattern, markdown_instance)

    def handleMatch(self, m):
        el = util.etree.Element("img")
        src_parts = m.group(9).split()
        if src_parts:
            src = src_parts[0]
            if src[0] == "<" and src[-1] == ">":
                src = src[1:-1]
            # Now we parse relative directories and make them into
            # full links
            relative_link_re = re.compile(
                '''
                ^images/.*$|
                ^image/.*$
                ''',
                re.VERBOSE
            )
            if relative_link_re.match(src):
                # Test replacement for image files
                src = '{}/{}?raw=true'.format(
                    self.directory_url,
                    src
                )

            el.set('src', self.sanitize_url(self.unescape(src)))
        else:
            el.set('src', "")
        if len(src_parts) > 1:
            el.set('title', dequote(self.unescape(" ".join(src_parts[1:]))))

        if self.markdown.enable_attributes:
            truealt = handleAttributes(m.group(2), el)
        else:
            truealt = m.group(2)

        el.set('alt', self.unescape(truealt))
        return el

class ImageReferencePreprocessor(Preprocessor):
    """ Rewrite Image references to point to github """

    def __init__(self, directory_url, markdown_instance):
        """ Replaces matches with some text. """
        self.directory_url = directory_url
        super(ImageReferencePreprocessor, self).__init__(markdown_instance)

    def run(self, lines):
        relative_link_re = re.compile(
            '''
            ^images/.*$|
            ^image/.*$
            ''',
            re.VERBOSE
        )

        # Loop through references, munge image links
        for k in self.markdown.references.keys():
            if relative_link_re.match(self.markdown.references[k][0]):
                # Replace with path to file in GitHub
                self.markdown.references[k] = (
                    '{}/{}?raw=true'.format(
                        self.directory_url,
                        self.markdown.references[k][0]
                    ),
                    self.markdown.references[k][1]
                )

        # Doesn't do anything to text
        return lines

class ImageLinkRewriteExtension(Extension):
    """ Rewrite image links to point to github """
    def __init__(self, **kwargs):
        self.config = {
            'base_github_url' : [
                'https://github.com/NeCTAR-RC/nectarcloud-tier0doco/blob/master',
                'URL for GitHub master branch'
            ],
            'image_file_path' : ['', 'Path to image (URL escaped)']
        }
        super(ImageLinkRewriteExtension, self).__init__(**kwargs)

    def extendMarkdown(self, md, md_globals):
        ''' Replace inbuilt image parsers with our own '''

        directory_url = '{}/{}'.format(
            self.getConfig('base_github_url'),
            self.getConfig('image_file_path')
        )
        md.inlinePatterns['image_link'] = RewriteImagePattern(
            IMAGE_LINK_RE,
            directory_url,
            md
        )
        md.preprocessors.add(
            'munge_image_urls',
            ImageReferencePreprocessor(directory_url, md),
            '>reference'
        )

def makeExtension(*args, **kwargs):
    return ImageLinkRewriteExtension(*args, **kwargs)

