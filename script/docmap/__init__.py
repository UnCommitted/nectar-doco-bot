"""
    docmap
    ~~~~~~

    Map documentation ID between various systems
"""

import logging
import re
import os
import yaml
import copy
from hashlib import sha1
from markdown import markdown

log = logging.getLogger()

class DocumentMapError(Exception):
    '''Custom exception for Document Map issues'''
    pass

class DocumentMap:
    '''
    Provides an interface to the current documentation ID map between
    various systems
    '''

    # Define a regular expression to use to parse out internal Document IDs
    docid_check = re.compile(
        '''
        ^(.*{sep})*                 # Ignore directory path
        [^{sep2}]+--DOCID\d+(\.[Mm][Dd])?$  # DOCID Delimiter for quick check
        '''.format(sep=os.sep,sep2=os.sep),
        re.VERBOSE
    )

    # Only parse out title
    title_re = re.compile(
        '''
        ^(.*{sep})*                 # Ignore directory path
        (?P<title>.*?)              # Parse out the title
        (?P<extension>\.[Mm][Dd])?$ # Get the extension (case is important)
        '''.format(sep=os.sep),
        re.VERBOSE
    )

    # Parse out title AND docid
    docid_re = re.compile(
        '''
        ^(.*{sep})*    # Ignore directory path
        (?P<title>.*)  # Parse out the title
        --DOCID        # DOCID delimiter
        (?P<docid>\d+) # Parse out internal DOCID if it exists
        (\.[Mm][Dd])?$ # Ignore .md file extension
        '''.format(sep=os.sep),
        re.VERBOSE
    )

    # Parse parent and document DOCIDs
    parentid_re = re.compile(
        '''
        ^.*                   # Ignore up to DOCID
        --DOCID               # DOCID delimiter
        (?P<parent_docid>\d+) # Parse out parent DOCID
        .*
        --DOCID               # DOCID delimiter
        (?P<docid>\d+)        # Parse out item DOCID
        .*
        ''',
        re.VERBOSE
    )

    def __init__(self, mapping_dir, article_dir):
        '''
        mapping_dir is a path to directory with the following files:
            articles.yaml
            folders.yaml
            categories.yaml
            counters.yaml

        Articles YAML
        ---
        # Articles
        1:
            title: Title
            freshdesk:
                <info from freshdesk api>


        Folders YAML
        ---
        # Folders
        1:
            title: Title
            freshdesk:
                <info from freshdesk api>

        Categories YAML
        ---
        # Categories
        1:
            title: blah
            freshdesk:
                <info from freshdesk api>

        Counters YAML
        ---
        # Counters
        # current_max counters for IDS
        category: 1
        folder: 1
        article: 1

        article_dir is the full path to the directory containing articles.
        '''
        self.mapping_dir = mapping_dir
        self.article_dir = article_dir
        self.articles = None
        self.orig_articles = None
        self.folders = None
        self.orig_folders = None
        self.categories = None
        self.orig_categories = None
        self.counters = None
        self.require_change = False

        # Create tracking arrays for creations, deletions, updates
        self.category_creations = {}
        self.article_creations = {}
        self.folder_creations = {}

        self.category_deletions = {}
        self.article_deletions = {}
        self.folder_deletions = {}

        self.category_updates = {}
        self.article_updates = {}
        self.folder_updates = {}

        # Parse in the mapping data in.
        self.load_mappings()

    def load_mappings(self):
        '''Load all mapping.yaml files'''
        for mapping in ['articles', 'folders', 'categories', 'counters']:
            with open('%s/%s.yaml' % (self.mapping_dir, mapping), 'r') as f:
                content = yaml.load(f)

            if content is None:
                content = {}

            self._save_origin(mapping, content)

    def _save_origin(self, mapping, content):
        # Create an original version to compare against
        if mapping == 'articles':
            self.articles = content
            self.orig_articles = copy.deepcopy(self.articles)
        elif mapping == 'folders':
            self.folders = content
            self.orig_folders = self.folders.copy()
        elif mapping == 'categories':
            self.categories = content
            self.orig_categories = self.categories.copy()
        elif mapping == 'counters':
            self.counters = content

    def save_articles(self):
        '''Save articles into articles.yaml'''
        with open('{}/articles.yaml'.format(self.mapping_dir), 'w') as f:
            f.write(yaml.dump(self.articles))

    def save_folders(self):
        '''Save folders into folders.yaml'''
        with open('{}/folders.yaml'.format(self.mapping_dir), 'w') as f:
            f.write(yaml.dump(self.folders))

    def purge_deleted_records(self):
        '''
        Purge deleted categories, folders and articles from the data
        structure.

        NOTE: ONLY RUN THIS AFTER ALL EXTERNAL ACTIONS HAVE BEEN TAKEN
        FOR THE DELETIONS
        '''
        for i in self.article_deletions.keys():
            del(self.articles[i])

        for i in self.folder_deletions.keys():
            del(self.folders[i])

        for i in self.category_deletions.keys():
            del(self.categories[i])

    def save_categories(self):
        '''Save categories into categories.yaml'''
        with open('{}/categories.yaml'.format(self.mapping_dir), 'w') as f:
            f.write(yaml.dump(self.categories))

    def save_counters(self):
        '''Save counters into counters.yaml'''
        with open('{}/counters.yaml'.format(self.mapping_dir), 'w') as f:
            f.write(yaml.dump(self.counters))

    def update_articles(self):
        '''
        Updates articles, folders and categories
        '''

        # Find all characters that are not the os dir separator
        base_depth = self.article_dir.count(os.sep)

        # Loop through articles directory to find categories, folders and
        # articles.
        for cat in os.walk(self.article_dir, topdown=False):
            cat_string = str(cat[0])

            # Don't worry about the top level directory
            if cat_string == self.article_dir:
                continue

            # Check if the category already has an ID
            current_depth = cat_string.count(os.sep) - base_depth
            matches = self.docid_check.search(cat_string)
            if matches:
                # We have an ID, parse out title and ID
                parsed_name = self.docid_re.search(cat_string)

                if current_depth == 1:
                    # Check the DOCID exists
                    category_info = self.categories.get(int(parsed_name.group('docid')))
                    if category_info:
                        # Change the title if there is a discrepancy
                        if category_info['title'] != parsed_name.group('title'):
                            category_info['title'] = parsed_name.group('title')
                            # NOTE = Any consumer should change title to new 'title'
                            category_info['action'] = {'action': 'TITLE_CHANGE'}
                    else:
                        # Unknown DOCID - add it in
                        self.categories[parsed_name.group('docid')] = {
                            'title': parsed_name.group('title'),
                            'action': {'action': 'TITLE_CHANGE'}
                        }

                elif current_depth == 2:
                    # Folder

                    # Check the DOCID exists
                    folder_info = self.folders.get(int(parsed_name.group('docid')))
                    if folder_info:
                        # Change the title if there is a discrepancy
                        if folder_info['title'] != parsed_name.group('title'):
                            folder_info['title'] = parsed_name.group('title')
                            # NOTE = Any consumer should change title to new 'title'
                            folder_info['action'] = {'action': 'TITLE_CHANGE'}
                    else:
                        # Unknown DOCID - add it in
                        self.folders[int(parsed_name.group('docid'))] = {
                            'title': parsed_name.group('title'),
                            'action': {'action': 'TITLE_CHANGE'}
                        }

                    # Now, get the files in this folder, and check their names
                    for listing in os.walk(cat_string, topdown=False):
                        directory = cat_string
                        articles = listing[2]

                        for article in articles:
                            got_id = self.docid_check.search(article)
                            if got_id:
                                # We have an ID, parse out title and ID

                                article_info = self.docid_re.search(article)

                                # Check the DOCID exists
                                article_dict = self.articles.get(
                                    int(article_info.group('docid'))
                                )
                                if article_dict:
                                    # Change the title if there is a discrepancy
                                    if article_dict['title'] != article_info.group('title'):
                                        article_dict['title'] = article_info.group('title')
                                        # NOTE = Any consumer should change title to new 'title'
                                        article_dict['action'] = {'action': 'TITLE_CHANGE'}
                                else:
                                    # Unknown DOCID - add it in
                                    self.articles[int(parsed_name.group('docid'))] = {
                                        'title': article_info.group('title'),
                                        'action': {'action': 'TITLE_CHANGE'}
                                    }

                            else:
                                # No ID, need a new one
                                # Flag that we need to update

                                article_info = self.title_re.search(article)

                                # Ignore any files that aren'd Markdown
                                if article_info.group('extension'):
                                    # Update the latest article ID
                                    self.counters['article'] += 1

                                    # Flag renaming Category
                                    old_name = '{dir}{sep}{title}{extension}'.format(
                                        dir=directory,
                                        sep=os.sep,
                                        title=article_info.group('title'),
                                        extension=article_info.group('extension')
                                    )

                                    new_name = '{dir}{sep}{title}--DOCID{docid}{extension}'.format(
                                        dir=directory,
                                        sep=os.sep,
                                        title=article_info.group('title'),
                                        docid=self.counters['article'],
                                        extension=article_info.group('extension')
                                    )

                                    # Add information about this article
                                    self.articles[self.counters['article']] = {
                                        'title': article_info.group('title'),
                                        'action': {
                                            'action': 'CREATE',
                                            'from': old_name,
                                            'to': new_name
                                        }
                                    }

            else:
                # No ID, just a title
                # XXX Debugging

                # Get the current relative depth
                # 1 = Category
                # 2 = Folder

                parsed_name = self.title_re.search(cat_string)
                if current_depth == 1:
                    # Category

                    # Flag that we need to update
                    # Update the latest cat ID
                    self.counters['category'] += 1

                    # Flag renaming Category
                    new_name = '{oldname}--DOCID{docid}'.format(
                        oldname=cat_string,
                        docid=self.counters['category']
                    )

                    # Add information about this category
                    self.categories[self.counters['category']] = {
                        'title': parsed_name.group('title'),
                        'action': {
                            'action': 'CREATE',
                            'from': cat_string,
                            'to': new_name
                        }
                    }

                elif current_depth == 2:
                    # Folder

                    # Flag that we need to update
                    # Update the latest folder ID
                    self.counters['folder'] += 1

                    # Flag renaming Category
                    new_name = '{oldname}--DOCID{docid}'.format(
                        oldname=cat_string,
                        docid=self.counters['folder']
                    )

                    # Add information about this folder
                    self.folders[self.counters['folder']] = {
                        'title': parsed_name.group('title'),
                        'action': {
                            'action': 'CREATE',
                            'from': cat_string,
                            'to': new_name
                        }
                    }

                    # Now, get the files in this folder, and check their names
                    for listing in os.walk(cat_string, topdown=False):
                        directory = cat_string
                        articles = listing[2]

                        for article in articles:
                            got_id = self.docid_check.search(article)
                            if got_id:
                                # We have an ID, parse out title and ID
                                article_info = self.docid_re.search(article)

                                # Check the DOCID exists
                                article_dict = self.articles.get(
                                    int(article_info.group('docid'))
                                )
                                if article_dict:
                                    # Change the title if there is a discrepancy
                                    if article_dict['title'] != article_info.group('title'):
                                        article_dict['title'] = article_info.group('title')
                                        # NOTE = Any consumer should change title to new 'title'
                                        article_dict['action'] = {'action': 'TITLE_CHANGE'}
                                else:
                                    # Unknown DOCID - add it in
                                    self.articles[article_info.group('docid')] = {
                                        'title': article_info.group('title'),
                                        'action': {'action': 'TITLE_CHANGE'}
                                    }
                            else:
                                # No ID, need a new one
                                # Flag that we need to update

                                article_info = self.title_re.search(article)

                                if article_info.group('extension'):
                                    # Update the latest article ID
                                    self.counters['article'] += 1
                                    # Flag renaming Article
                                    oldname = '{dir}{sep}{title}'.format(
                                        dir=directory,
                                        sep=os.sep,
                                        title=article_info.group('title')
                                    )

                                    article_name =\
                                        '{oldname}--DOCID{docid}{extension}'\
                                        .format(
                                            oldname=oldname,
                                            docid=self.counters['article'],
                                            extension=article_info.group('extension')
                                        )

                                    # Add information about this article
                                    self.articles[self.counters['article']] = {
                                        'title': article_info.group('title'),
                                        'action': {
                                            'action': 'CREATE',
                                            'from': '{name}{extension}'.format(
                                                name=oldname,
                                                extension=article_info.group('extension')
                                            ),
                                            'to': article_name
                                        }
                                    }

                else:
                    # Too deep, ignore
                    pass

        # We now have all the information required to rename files and folders

        # Start with articles
        for aid, article in self.articles.items():
            # Check if there is an action
            action = article.get('action')
            if action:
                # Need to create a branch
                self.require_change = True
                # If it is a new file, we need to rename it with the new
                # DOCID
                if action['action'] == 'CREATE':
                    os.rename(
                        action['from'],
                        action['to']
                    )
                    self.article_creations[aid] = True
                    self.require_change = True
                elif action['action'] == 'TITLE_CHANGE':
                    self.article_updates[aid] = True
                    self.require_change = True

        # Delete the actions
        for i in self.article_creations:
            del(self.articles[i]['action'])
        for i in self.article_updates:
            del(self.articles[i]['action'])

        # Then to folders
        for fid, folder in self.folders.items():
            # Check if there is an action
            action = folder.get('action')
            if action:
                # Need to create a branch
                self.require_change = True
                # If it is a new file, we need to rename it with the new
                # DOCID
                if action['action'] == 'CREATE':
                    os.rename(
                        action['from'],
                        action['to']
                    )
                    self.folder_creations[fid] = True
                    self.require_change = True
                if action['action'] == 'TITLE_CHANGE':
                    self.folder_updates[fid] = True
                    self.require_change = True

        # Delete the actions
        for i in self.folder_creations:
            del(self.folders[i]['action'])
        for i in self.folder_updates:
            del(self.folders[i]['action'])

        # Finally Categories
        category_creations = []
        for cid, category in self.categories.items():
            # Check if there is an action
            action = category.get('action')
            if action:
                # Need to create a branch
                self.require_change = True

                # If it is a new file, we need to rename it with the new
                # DOCID
                if action['action'] == 'CREATE':
                    os.rename(
                        action['from'],
                        action['to']
                    )
                    self.category_creations[cid] = True
                if action['action'] == 'TITLE_CHANGE':
                    self.category_updates[cid] = True

        # Delete the actions
        for i in self.category_creations:
            del(self.categories[i]['action'])
        for i in self.category_updates:
            del(self.categories[i]['action'])

        # Now that all IDS have been assigned, we can map parent IDS properly
        for cat in os.walk(self.article_dir, topdown=False):
            cat_string = str(cat[0])

            # Don't worry about the top level directory
            if cat_string == self.article_dir:
                continue

            # Check if the category already has an ID
            current_depth = cat_string.count(os.sep) - base_depth
            if current_depth == 1:
                # Categories don't have parents, but we need to record that
                # we found it for deletions.
                matches = self.docid_re.search(cat_string)
                self.categories[int(matches.group('docid'))]['found'] = True
            elif current_depth == 2:
                # Folder
                matches = self.parentid_re.search(cat_string)

                # Set the folder parent
                folder_info = self.folders.get(int(matches.group('docid')))
                folder_info['parent'] = int(matches.group('parent_docid'))
                folder_info['found'] = True

                # Now, get the files in this folder, and check their names
                for listing in os.walk(cat_string, topdown=False):
                    directory = cat_string
                    articles = listing[2]

                    for article in articles:
                        article_info = self.docid_re.search(article)

                        # Only process if it is actually an article
                        # COULD be a .gitignore file/other file that
                        # we don't handle
                        if article_info:
                            # Add the parent folder...
                            tmp_article = self.articles[int(article_info.group('docid'))]
                            tmp_article['parent'] = int(matches.group('docid'))
                            tmp_article['found'] = True

                            # Add a sha1sum of the file
                            with open(
                                '{directory}{sep}{name}'.format(
                                    directory=cat_string,
                                    sep=os.sep,
                                    name=article
                                ),
                                'r'
                            ) as f:
                                temp=f.read()
                                tmp_article['sha1'] =\
                                    sha1(temp.encode('utf-8')).hexdigest()
                                tmp_article['html'] =\
                                    markdown(temp, output_format='html5')

        # Find the deleted and updated items

        # Categories
        for cid, cat in self.categories.items():
            if cat.get('found'):
                del(cat['found'])
                if not cid in self.category_creations:
                    # Check for updates
                    if cat['title'] != self.orig_categories[cid]['title']:
                        self.category_updates[cid] = True
                        self.require_change = True
            else:
                self.category_deletions[cid] = True
                self.require_change = True

        # Folders
        for fid, folder in self.folders.items():
            if folder.get('found'):
                del(folder['found'])
                if not fid in self.folder_creations:
                    # Check title and parent change
                    if\
                    folder['title'] != self.orig_folders[fid]['title']\
                    or\
                    folder['parent'] != self.orig_folders[fid]['parent']:
                        self.folder_updates[fid] = True
                        self.require_change = True
            else:
                # Deletion
                self.folder_deletions[fid] = True
                self.require_change = True

        # Articles
        for aid, article in self.articles.items():
            if article.get('found'):
                del(article['found'])
                if not aid in self.article_creations:
                    log.debug('Got to here.... 1')
                    # Check for updates to content, title and parent
                    if\
                    article['sha1'] != self.orig_articles[int(aid)]['sha1']\
                    or\
                    article['title'] != self.orig_articles[int(aid)]['title']\
                    or\
                    article['parent'] != self.orig_articles[int(aid)]['parent']:
                        log.debug('Got to here.... 2')
                        self.article_updates[aid] = True
                        self.require_change = True
                else:
                    log.debug('Got to here.... 3')
            else:
                self.article_deletions[aid] = True
                self.require_change = True

