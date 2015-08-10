import logging
import requests
import json

from . import DocumentMap

log = logging.getLogger()

class FreshDesk:
    def __init__(self, api_url, api_token):
        '''Get the basic information'''
        self.api_url = api_url

        # Set up the requests auth tuple
        self.api_token = api_token
        self.auth = (self.api_token, 'X')
        self.headers = {'Content-type': 'application/json'}

    def log_action(self, source, action, reply):
        '''Log result of an action done to a source'''
        if reply.status_code in [200, 201]:
            log.info('%s on %s was successful' % (action, source))
        else:
            log.error('%s on %s failed' % (action, source))
            log.error('Status code: %s' % reply.status_code)
            log.error('Headers: %s' % reply.headers)

    def get_solution_categories(self):
        '''Get all current categories'''
        # FIXME: never called?
        r = requests.get(
            '{}/solution/categories.json'.format(self.api_url),
            auth=self.auth
        )
        return r.json()

    def get_solutions_in_folder(self, folder):
        '''
        Get solutions in folder

        NOTE: Folder is currently a folder json
        '''
        r = requests.get(
            '{}/solution/categories/{}/folders/{}.json'\
            .format(
                self.api_url,
                folder.get('category_id'),
                folder.get('id')
            ),
            auth=self.auth
        )
        return r.json()

    def create_category(self, category):
        '''Create a new category in freshdesk'''
        payload = {
            'solution_category': {
                'name': category['title'],
                'description': category['title']
            }
        }
        reply = requests.post(
            '{}/solution/categories.json'.format(self.api_url),
            data=json.dumps(payload),
            headers=self.headers,
            auth=self.auth
        )

        self.log_action('category %s' % category['title'], 'Creation', reply)
        if reply.status_code == 201: return reply.json()

    def update_category(self, category):
        '''Update category in freshdesk'''

        payload = {
            'solution_category': {
                'name': category['title'],
            }
        }

        url = '{url}'\
        '/solution/categories/{cat_id}.json'.format(
            url=self.api_url,
            cat_id=category['freshdesk']['fd_attributes']['category']['id'],
        )

        reply = requests.put(
            url,
            headers=self.headers,
            auth=self.auth,
            data=json.dumps(payload)
        )

        self.log_action('category %s' % category['title'], 'Update', reply)
        if reply.status_code == 200: return reply.json()

    def delete_category(self, category):
        '''Remove category from freshdesk'''
        url = '{url}'\
        '/solution/categories/{cat_id}.json'\
        .format(
            url=self.api_url,
            cat_id=category['freshdesk']['fd_attributes']['category']['id']
        )

        # Use the delete API
        reply = requests.delete(
            url,
            headers=self.headers,
            auth=self.auth
        )

        self.log_action('category %s' % category['title'], 'Deletion', reply)

    def create_folder(self, folder, freshdesk_cid):
        '''Create a new folder in freshdesk'''
        payload = {
            "solution_folder": {
                "name": folder['title'],
                "visibility": 1,
                "description": folder['title']
            }
        }
        reply = requests.post(
            '{}/solution/categories/{}/folders.json'.format(
                self.api_url,
                freshdesk_cid
            ),
            data=json.dumps(payload),
            headers=self.headers,
            auth=self.auth
        )

        self.log_action('folder %s' % folder['title'], 'Creation', reply)
        if reply.status_code == 201: return reply.json()

    def update_folder(self, folder):
        '''Update folder in freshdesk'''

        payload = {
            'solution_article': {
                'name': folder['title'],
                'description': folder['title'],
                'visibility': 1
            }
        }

        url = '{url}'\
        '/solution/categories/{cat_id}'\
        '/folders/{folder_id}.json'.format(
            url=self.api_url,
            cat_id=folder['freshdesk']['fd_attributes']['folder']['category_id'],
            folder_id=folder['freshdesk']['fd_attributes']['folder']['id'],
        )

        reply = requests.put(
            url,
            headers=self.headers,
            auth=self.auth,
            data=json.dumps(payload)
        )

        self.log_action('folder %s' % folder['title'], 'Update', reply)
        if reply.status_code == 200: return reply.json()

    def delete_folder(self, folder):
        '''Remove folder from freshdesk'''
        url = '{url}'\
        '/solution/categories/{cat_id}'\
        '/folders/{folder_id}.json'\
        .format(
            url=self.api_url,
            cat_id=folder['freshdesk']['fd_attributes']['folder']['category_id'],
            folder_id=folder['freshdesk']['fd_attributes']['folder']['id']
        )

        # Use the delete API
        reply = requests.delete(
            url,
            headers=self.headers,
            auth=self.auth
        )

        self.log_action('folder %s' % folder['title'], 'Deletion', reply)

    def create_article(self, article, freshdesk_cid, freshdesk_fid):
        '''Create a new article in freshdesk'''
        payload = {
            'solution_article': {
                'title': article['title'],
                'status': 2,
                'art_type': 1,
                'folder_id': freshdesk_fid,
                'description': article['html']
            },
            'tags': {}
        }
        url = '{url}'\
        '/solution/categories/{cat_id}'\
        '/folders/{folder_id}'\
        '/articles.json'.format(
            url=self.api_url,
            cat_id=freshdesk_cid,
            folder_id=freshdesk_fid
        )

        reply = requests.post(
            url,
            data=json.dumps(payload),
            headers=self.headers,
            auth=self.auth
        )

        self.log_action('Article %s' % article['title'], 'Creation', reply)
        if reply.status_code == 201: return reply.json()

    def update_article(self, article):
        '''Update article in freshdesk'''

        payload = {
            'solution_article': {
                'title': article['title'],
                'description': article['html']
            }
        }

        url = '{url}'\
        '/solution/categories/{cat_id}'\
        '/folders/{folder_id}'\
        '/articles/{article_id}.json'.format(
            url=self.api_url,
            cat_id=article['freshdesk']['fd_attributes']['article']['folder']['parent_id'],
            folder_id=article['freshdesk']['fd_attributes']['article']['folder']['id'],
            article_id=article['freshdesk']['fd_attributes']['article']['id']
        )

        reply = requests.put(
            url,
            headers=self.headers,
            auth=self.auth,
            data=json.dumps(payload)
        )

        self.log_action('Article %s' % article['title'], 'Update', reply)
        if reply.status_code == 200: return reply.json()

    def delete_article(self, article):
        '''Remove article from freshdesk'''
        url = '{url}'\
        '/solution/categories/{cat_id}'\
        '/folders/{folder_id}'\
        '/articles/{article_id}.json'.format(
            url=self.api_url,
            cat_id=article['freshdesk']['fd_attributes']['article']['folder']['parent_id'],
            folder_id=article['freshdesk']['fd_attributes']['article']['folder']['id'],
            article_id=article['freshdesk']['fd_attributes']['article']['id']
        )

        reply = requests.delete(
            url,
            headers=self.headers,
            auth=self.auth
        )

        self.log_action('Article %s' % article['title'], 'Deletion', reply)

class FreshDeskDocumentMap(DocumentMap):
    '''Adds FreshDesk document mapping functionality to DocumentMap'''

    def __init__(self, mapping_dir, article_dir, api_url, api_token):
        '''Initialize as per super, then add FreshDesk Mappings'''
        super().__init__(mapping_dir, article_dir)
        self.fdapi = FreshDesk(api_url, api_token)

    def synchronize_freshdesk(self):
        '''Push all changes up to freshdesk'''
        # Add Any known IDS in categories, folders or articles that are
        # already known, but aren't uploaded to FD yet

        # Categories
        for i,j in self.categories.items():
            if not j.get('freshdesk'):
                self.category_creations[i] = True

        # Folders
        for i,j in self.folders.items():
            if not j.get('freshdesk'):
                self.folder_creations[i] = True

        # Articles
        for i,j in self.articles.items():
            if not j.get('freshdesk'):
                self.article_creations[i] = True

        # Category Creations and Updates
        for cid in self.category_updates.keys():
            # Update Category in Freshdesk
            # If we don't already have a freshdesk key here, it is actually a
            # NEW FD category (i.e. previous push didn't work...)
            if self.categories[cid].get('freshdesk'):
                self.categories[cid]['freshdesk'] = {
                    'fd_attributes': self.fdapi.update_category(
                        self.categories[cid]
                    )
                }
                if self.categories[cid]['freshdesk']['fd_attributes'] == None:
                    # We have an error, delete freshdesk key
                    del(self.categories[cid]['freshdesk'])
                else:
                    self.require_change = True
            else:
                self.category_creations[cid] = True

        for cid in self.category_creations.keys():
            # Create a new Category in Freshdesk
            self.categories[cid]['freshdesk'] = {
                'fd_attributes': self.fdapi.create_category(self.categories[cid])
            }

            if self.categories[cid]['freshdesk']['fd_attributes'] == None:
                # We have an error, delete freshdesk key
                del(self.categories[cid]['freshdesk'])
            else:
                self.require_change = True

        # Folder Creations and Updates
        for fid in self.folder_updates.keys():
            try:
                fd_cat_id = self.categories[int(self.folders[fid]['parent'])]['freshdesk']['fd_attributes']['category']['id']
            except KeyError:
                # This just means the parent category isn't in FD yet
                continue
            except TypeError:
                continue

            # If we don't already have a freshdesk key here, it is actually a
            # NEW FD folder (i.e. previous push didn't work...)
            if self.folders[fid].get('freshdesk'):
                self.folders[fid]['freshdesk'] = {
                    'fd_attributes': self.fdapi.update_folder(self.folders[fid])
                }
                if self.folders[fid]['freshdesk']['fd_attributes'] == None:
                    # We have an error, delete freshdesk key
                    del(self.folders[fid]['freshdesk'])
                else:
                    self.require_change = True
            else:
                self.folder_creations[fid] = True


        for fid in self.folder_creations.keys():
            try:
                fd_cat_id = self.categories[int(self.folders[fid]['parent'])]['freshdesk']['fd_attributes']['category']['id']
            except KeyError:
                # This just means the parent category isn't in FD yet
                continue
            except TypeError:
                continue

            self.folders[fid]['freshdesk'] = {
                'fd_attributes': self.fdapi.create_folder(
                    self.folders[fid],
                    fd_cat_id
                )
            }
            if self.folders[fid]['freshdesk']['fd_attributes'] == None:
                # We have an error, delete freshdesk key
                del(self.folders[fid]['freshdesk'])
            else:
                self.require_change = True

        # Article Creations, Updates and Deletions
        for aid in self.article_updates.keys():
            # Update Article in Freshdesk
            # If we don't already have a freshdesk key here, it is actually a
            # NEW FD article (i.e. previous push didn't work...)
            if self.articles[aid].get('freshdesk'):
                self.articles[aid]['freshdesk'] = {
                    'fd_attributes': self.fdapi.update_article(self.articles[aid])
                }

                if self.articles[aid]['freshdesk']['fd_attributes'] == None:
                    # We have an error, delete freshdesk key
                    del(self.articles[aid]['freshdesk'])
                else:
                    self.require_change = True
            else:
                self.article_creations[aid] = True

        for aid in self.article_creations.keys():
            try:
                fd_folder_id = self.folders[int(self.articles[aid]['parent'])]['freshdesk']['fd_attributes']['folder']['id']
                fd_cat_id = self.folders[int(self.articles[aid]['parent'])]['freshdesk']['fd_attributes']['folder']['category_id']
            # except TypeError:
            #     continue
            except KeyError:
                continue

            self.articles[aid]['freshdesk'] = {
                'fd_attributes': self.fdapi.create_article(
                    self.articles[aid],
                    fd_cat_id,
                    fd_folder_id
                )
            }

            if self.articles[aid]['freshdesk']['fd_attributes'] == None:
                # We have an error, delete freshdesk key
                del(self.articles[aid]['freshdesk'])
            else:
                self.require_change = True

        for aid in self.article_deletions.keys():
            try:
                fd_folder_id = self.folders[self.articles[aid]['parent']]['freshdesk']['fd_attributes']['folder']['id']
                fd_cat_id = self.folders[self.articles[aid]['parent']]['freshdesk']['fd_attributes']['folder']['category_id']
            except TypeError:
                continue
            except KeyError:
                continue

            self.fdapi.delete_article(self.articles[aid])
            self.require_change = True

        # Folder Deletions
        for fid in self.folder_deletions.keys():
            # Delete folder in Freshdesk
            self.fdapi.delete_folder(self.folders[fid])
            self.require_change = True

        # Category Deletions
        for cid in self.category_deletions.keys():
            # Delete Category in Freshdesk
            self.fdapi.delete_category(self.categories[cid])
            self.require_change = True

        # Purge the deleted items from our data structure
        self.purge_deleted_records()
