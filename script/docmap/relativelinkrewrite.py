from markdown.preprocessors import Preprocessor
import os
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
        self.fd_solutions_base_url = fd_solutions_base_url
        self.article_mapping_dict = article_mapping_dict
        self.docid_re = re.compile(
            '''
            # Ignore directory path and filename
            ^(.*{sep})*.*

            # Parse out the article DOCID
            --DOCID
            (?P<docid>\d+)$
            '''.format(sep=os.sep),
            re.VERBOSE
        )
        super(RewriteLinkPattern, self).__init__(pattern, markdown_instance)

    def handleMatch(self, m):
        el = util.etree.Element("img")
        src_parts = m.group(9).split()
        if src_parts:
            src = src_parts[0]
            if src[0] == "<" and src[-1] == ">":
                src = src[1:-1]
            # Now we parse relative directories and make them into
            # full links

            # Look up the DOCID in our dict and formulate the FreshDesk URL
            docid = self.docid_re.search(src)
            print('Got the following source: {}'.format(src))
            if docid:
                # We have a docid, get the freshdesk info from our data
                article_info =\
                self.article_mapping_dict[
                    int(docid.group('docid'))
                ].get('freshdesk')
                if article_info:
                    # Article already in freshdesk need to alter link
                    fdid = article_info['fd_attributes']['article']['id']
                    print('DOC {} has FD ID {}'.format(
                        int(docid.group('docid')),
                        fdid
                    ))
                    # Set new URL
                    src = '{solutions_url}{fdid}'.format(
                        solutions_url=self.fd_solutions_base_url,
                        fdid=fdid
                    )
            else:
                # Didn't get a docid, ignoring
                print('Did not get a docid from {}'.format(src))

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

    def __init__(
        self,
        pattern,
        fd_solutions_base_url,
        article_mapping_dict ,
        markdown_instance
    ):
        """ Replaces matches with some text. """
        self.fd_solutions_base_url = fd_solutions_base_url
        self.article_mapping_dict = article_mapping_dict
        self.docid_re = re.compile(
            '''
            # Ignore directory path and filename
            ^(.*{sep})*.*

            # Parse out the article DOCID
            --DOCID
            (?P<docid>\d+)$
            '''.format(sep=os.sep),
            re.VERBOSE
        )
        super(RewriteReferencePattern, self).__init__(markdown_instance)

    def handleMatch(self, m):
        try:
            id = m.group(9).lower()
        except IndexError:
            id = None
        if not id:
            # if we got something like "[Google][]" or "[Goggle]"
            # we'll use "google" as the id
            id = m.group(2).lower()

        # Clean up linebreaks in id
        id = self.NEWLINE_CLEANUP_RE.sub(' ', id)
        if id not in self.markdown.references:  # ignore undefined refs
            return None
        href, title = self.markdown.references[id]

        # Look up the DOCID in our dict and formulate the FreshDesk URL
        docid = self.docid_re.search(href)
        print('Got the following source: {}'.format(href))
        if docid:
            # We have a docid, get the freshdesk info from our data
            article_info =\
            self.article_mapping_dict[
                int(docid.group('docid'))
            ].get('freshdesk')
            if article_info:
                # Article already in freshdesk need to alter link
                fdid = article_info['fd_attributes']['article']['id']
                print('DOC {} has FD ID {}'.format(
                    int(docid.group('docid')),
                    fdid
                ))
                # Set new URL
                href = '{solutions_url}{fdid}'.format(
                    solutions_url=self.fd_solutions_base_url,
                    fdid=fdid
                )
        else:
            # Didn't get a docid, ignoring
            print('Did not get a docid from {}'.format(href))

        text = m.group(2)
        return self.makeTag(href, title, text)

class ReferenceLinkRewriteExtension(Extension):
    """ Rewrite doc links to use FD solution ids """
    def __init__(self, **kwargs):
        self.config = {
            'fd_solutions_base_url' : [
                'https://support.nectar.org.au/support/solutions/articles/',
                'Base URL for the Nectar FD solutions area'
            ],
            'article_mapping_dict' : [
                {},
                'Dict containing the article mappings\nShould be a deep copy...'
            ]
        }
        super(ReferenceLinkRewriteExtension, self).__init__(**kwargs)

    def extendMarkdown(self, md, md_globals):
        ''' Replace inbuilt image parsers with our own '''

        fd_solutions_base_url = self.getConfig('fd_solutions_base_url')
        article_mapping_dict = self.getConfig('article_mapping_dict')

        # Replace the current default patterns with our own
        # creations
        md.inlinePatterns['link'] = RewriteLinkPattern(
            IMAGE_LINK_RE,
            fd_solutions_base_url,
            article_mapping_dict,
            md
        )
        md.inlinePatterns['reference'] = RewriteReferencePattern(
            IMAGE_LINK_RE,
            fd_solutions_base_url,
            article_mapping_dict,
            md
        )

def makeExtension(*args, **kwargs):
    return ImageLinkRewriteExtension(*args, **kwargs)

