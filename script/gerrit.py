import logging
import requests
from requests.auth import HTTPDigestAuth
import json
import re
from pprint import pformat

log = logging.getLogger()

class GerritAPI:
    '''Interacts with the NeCTAR Gerrit'''

    def __init__(self, gerrit_url, project_name, username, password):
        '''Get auth and project information'''
        self.gerrit_url = gerrit_url
        self.project_name = project_name
        self.username = username
        self.password = password
        self.auth = HTTPDigestAuth(self.username, self.password)
        self.headers = {'Content-type': 'application/json; charset=UTF-8'}

    def create_change(self, change_subject):
        '''
        Creates a new change and returns the Change ID and ID so that it
        can be used in HTTPS push and verification checks
        '''
        url = "{gerrit_url}/a/changes/".format(gerrit_url=self.gerrit_url)
        log.debug('URL: {}'.format(url))
        change_info = {
            "project": self.project_name,
            "subject": change_subject,
            "branch": "master",
            "status": "DRAFT"
        }
        log.debug(pformat(change_info))
        reply = requests.post(
            url,
            auth=self.auth,
            headers=self.headers,
            data=json.dumps(change_info)
        )
        if reply.status_code == 201:
            log.debug('Status OK. Got the following {}'.format(reply.text))
            # Fix stupid response error.. grrr
            json_response = json.loads(re.sub(r'\)]}\'', '', reply.text))
            log.debug(pformat(json_response))
            return(json_response['change_id'], json_response['id'])
        else:
            log.debug('Bad response!! {}'.format(reply.status_code))
            return(None, None)

    def self_approve_change(self, long_change_id):
        '''+2 review and submit the change'''
        # First, get information on the change, mainly the revision,
        # So that we can approve
        url = "{gerrit_url}/a/changes/{change_id}".format(
            gerrit_url=self.gerrit_url,
            change_id=long_change_id
        )
        params = {
            'o': 'CURRENT_REVISION'
        }
        reply = requests.get(
            url,
            auth=self.auth,
            headers=self.headers,
            params=params
        )
        # Fix stupid response header.. grrr
        info = json.loads(re.sub(r'\)]}\'', '', reply.text))

        # Save the current revision to allow review and submission
        current_revision = info['current_revision']

        # Self approve
        review_url = '{gerrit_url}/a/changes/{change_id}/'\
        'revisions/{revision_id}/review'.format(
            gerrit_url=self.gerrit_url,
            change_id=long_change_id,
            revision_id=current_revision
        )

        log.debug('Review Url: {}'.format(review_url))
        params = {
            'labels': {
                'Code-Review': '+2'
            }
        }

        reply = requests.post(
            review_url,
            auth=self.auth,
            headers=self.headers,
            data=json.dumps(params)
        )

        # Fix stupid response header.. grrr
        info = json.loads(re.sub(r'\)]}\'', '', reply.text))
        log.debug(pformat(info))

        # Now we submit
        submit_url = '{gerrit_url}/a/changes/{change_id}/submit'.format(
            gerrit_url=self.gerrit_url,
            change_id=long_change_id,
        )

        params = {
            'wait_for_merge': True
        }

        reply = requests.post(
            submit_url,
            auth=self.auth,
            headers=self.headers,
            data=json.dumps(params)
        )

        log.debug(reply.status_code)
        log.debug(reply.headers)

        # Fix stupid response header.. grrr
        info = json.loads(re.sub(r'\)]}\'', '', reply.text))
        log.debug(pformat(info))

    def verified(self, long_change_id):
        '''Check a change using the API to see if it has been verified'''

        # URL for detail API
        url = "{gerrit_url}/a/changes/{long_change_id}/detail".format(
            gerrit_url=self.gerrit_url,
            long_change_id=long_change_id
        )

        log.debug('URL: {}'.format(url))
        # Send request
        reply = requests.get(
            url,
            auth=self.auth,
        )

        if reply.status_code == requests.codes.ok:
            log.debug('Status OK\nGot the following {}'.format(reply.text))
            # Fix stupid response header.. grrr
            info = json.loads(re.sub(r'\)]}\'', '', reply.text))
            log.debug(pformat(info))

            # Check the Verified label if it exists
            # Need to check each layer as they may not exist.
            labels = info.get('labels')
            verified_total =  0
            if labels:
                verified_list = labels.get('Verified')
                if verified_list:
                    all_verifications = verified_list.get('all')
                    if all_verifications:
                        for v in all_verifications:
                            verified_total += v['value']

            # If total >= 1 we are verified
            if verified_total >= 1:
                return(True)
            else:
                return(False)

        else:
            log.debug('Bad response!! {}'.format(reply.status_code))
            return(False)