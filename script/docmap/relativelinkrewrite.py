from markdown.preprocessors import Preprocessor
import markdown.inlinepatterns as ilp
from markdown.inlinepatterns import ImagePattern, handleAttributes
from markdown.extensions import Extension
import markdown
from markdown import util, odict
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

class RewriteLinkPattern(LinkPattern):
    '''Replaces relative links with FD ID references'''

    def __init__(
        self,
        pattern,
        fd_solutions_base_url,
        article_mapping_dict ,
        markdown_instance
    ):
        """ Replaces matches with some text. """
        self.directory_url = directory_url
        self.fd_solutions_base_url = fd_solutions_base_url
        self.article_mapping_dict = article_mapping_dict
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

class RewriteReferencePattern(ReferencePattern):
    """ Rewrite URL's to point to FD solution """

    def __init__(self, directory_url, markdown_instance):
        """ Replaces matches with some text. """
        self.directory_url = directory_url
        super(ReferencePattern, self).__init__(markdown_instance)

    def run(self, lines):
        relative_link_re = re.compile(
            '''
            .*--DOCID\d+\.[mM][dD]$     # Parse out Markdown references
                                        # that have DOCID's
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

class ReferenceLinkRewriteExtension(Extension):
    """ Rewrite doc links to use FD solution ids """
    def __init__(self, **kwargs):
        self.config = {
            'fd_solutions_base_url' : [
                'https://support.nectar.org.au/support/solutions/articles/',
                'Base URL for the Nectar FD solutions area'
            ],
            'article_mapping_dict' : [{}, 'Dict containing the article mappings\nShould b e a deep copy...']
        }
        super(ReferenceLinkRewriteExtension, self).__init__(**kwargs)

    def extendMarkdown(self, md, md_globals):
        ''' Replace inbuilt image parsers with our own '''

        fd_solutions_base_url = self.getConfig('fd_solutions_base_url')
        article_mapping_dict = self.getConfig('article_mapping_dict')
        md.inlinePatterns['internal_doco_link'] = RewriteLinkPattern(
            IMAGE_LINK_RE,
            fd_solutions_base_url,
            article_mapping_dict,
            md
        )
        md.inlinePatterns['internal_doco_reference'] = RewriteImagePattern(
            IMAGE_LINK_RE,
            fd_solutions_base_url,
            article_mapping_dict,
            md
        )

def makeExtension(*args, **kwargs):
    return ImageLinkRewriteExtension(*args, **kwargs)

