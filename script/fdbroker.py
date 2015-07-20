#!/usr/bin/env python3
'''
This is a broker to allow the tier0documentation to be uploaded to
Freshdesk solutions area.

The Github is in markdown, Freshdesk is in HTML.

The process is as follows:

1. Receive webhook from github on master push (flask)
2. Rebase current master from github master (git)
3. Use Freshdesk API to get the current documentation (request)
4. Import .json files from local configuration and compare against the
   downloaded version (json)
5. Push new files/updates into Freshdesk. (request)
6. Refresh Freshdesk data (request)
7. If there were additions, download with the new document ID
8. If there were deletions, delete from FD
9. Any new changes will be pushed into gerrit and self approved (request)

Configuration file is in yaml format, and is GPG encrypted.

TODO: Add configuration file options
'''

import time
import io
import os
import re
import argparse
import yaml
import gpgme
from datetime import datetime

from flask import Flask, request, abort
import subprocess
import threading
from hashlib import sha1
import hmac

import logging

from docmap.freshdesk import FreshDeskDocumentMap
from gerrit import GerritAPI


LOG_NAME = '%s.log' % os.path.splitext(os.path.basename(__file__))[0]
logging.basicConfig(filename=LOG_NAME, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger()

class ExpandHomeAction(argparse.Action):
    '''Expand ~ to user's home path when parsing the path in a command line argument'''
    def __call__(self, parser, namespace, value, option_string):
        setattr(namespace, self.dest, os.path.expanduser(value))

class ConfigError(Exception):
    '''Custom exception for configuration issues'''
    pass

def read_config(repopath, confname):
    '''
    Decrypts and parses the configuration for this fdbot
    '''
    # Decrypt config and pass back
    encryptedtext = open(
        "{}/script/configs/{}.yaml.asc".format(
            repopath,
            confname
        ),
        'rb'
    )

    decryptedtext = io.BytesIO()

    decryptor = gpgme.Context()
    decryptor.decrypt(encryptedtext, decryptedtext)
    encryptedtext.close()
    decryptedtext.seek(0)

    # Parse in the yaml configuration
    config = yaml.load(decryptedtext)
    decryptedtext.close()
    return config

def parse_args():
    parser = argparse.ArgumentParser(
        description='Start a Freshdesk bot.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    # Path of working repository
    parser.add_argument(
        '--repopath',
        default=os.path.expanduser('~/nectarcloud-tier0doco'),
        help='Path to Tier0 Doco repository clone',
        action=ExpandHomeAction
    )

    # Hubot config file name
    parser.add_argument(
        '-c',
        '--confname',
        default='fdbot',
        help='Base name of configuration file. '
            'Script will look for CONFIGNAME.yaml.asc under script/configs of REPOPATH'
    )

    # articles path relative to repo base
    parser.add_argument(
        '-ap',
        '--articlepath',
        default='articles',
        help='articles path relative to repopath'
    )

    parser.add_argument(
        '-l',
        '--loglevel',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Log level'
    )

    args = parser.parse_args()
    log.setLevel(args.loglevel)

    # Check the repo directory exists
    if not os.path.isdir(args.repopath):
        raise ConfigError(
            '--repopath: Repository {} does not exist'.format(args.repopath)
        )

    # Check that the configuration file exists
    configfile = "{}/script/configs/{}.yaml.asc"\
        .format(
            args.repopath,
            args.confname
        )

    if not os.path.isfile(configfile):
        raise ConfigError(
            '-c: Configuration file {} does not exist\n'.
            format(configfile)
        )

    return args

def configure_flask_server(args, config_dict):
    """Set up flask server"""
    endpoint = Flask(__name__)

    @endpoint.route('/', methods=['POST'])
    def receive_push_notification():
        """Receive message from GitHub"""

        if not 'X-Hub-Signature' in request.headers:
            abort(400)

        data = request.get_json()
        if data is None or not 'ref' in data:
            abort(400)

        # Generate token digenst for comparison
        temp_digest = 'sha1={}'.format(
            hmac.new(
                config_dict['flask_config']['auth_token'].encode('utf-8'),
                request.data,
                sha1
            ).hexdigest()
        )

        if request.headers['X-Hub-Signature'] != temp_digest:
            abort(401)

        if data['ref'] != 'refs/heads/master':
            abort(406)

        # Spawn a thread to process the request, and return OK immediately
        t = threading.Thread(target=process_update, args=(args,config_dict))
        t.start()

        return 'OK'

    # Return our endpoint
    return endpoint

def process_update(args, config):

        # Rebase the current branch
        subprocess.call(['git', 'checkout', 'master'])
        subprocess.call(['git', 'pull', '--rebase'])

        # Parse in the document mappings
        mapping_dir = '{}/mappings'.format(args.repopath)

        # Article directory
        article_dir = '{}/{}'.format(
            args.repopath,
            args.articlepath
        )

        if not os.path.exists(article_dir):
            os.makedirs(article_dir)

        # Documentation map between directory/files and
        # Categories/Folders/Articles
        docmap = FreshDeskDocumentMap(
            mapping_dir,
            article_dir,
            config['freshdesk_config']['api_url'],
            config['freshdesk_config']['api_token']
        )

        # Set up gerrit interface
        gerrit = GerritAPI(
            config['gerrit_config']['gerrit_url'],
            config['gerrit_config']['project_name'],
            config['gerrit_config']['web_username'],
            config['gerrit_config']['web_password']
        )

        # Reparse the filesystem
        docmap.update_articles()

        # Push the changes into Freshdesk
        docmap.synchronize_freshdesk()

        # Write out the updated information
        docmap.save_categories()
        docmap.save_folders()
        docmap.save_articles()
        docmap.save_counters()

        # Check if we need to make a new change
        log.debug('Checking if we need a change: {}'.format(docmap.require_change))
        if docmap.require_change:
            # Assumes we are in the repo directory
            # Create a branch
            change_title = 'brokerupdate-{}'.format(
                datetime.now().strftime('%Y-%m-%d-%H:%M:%S')
            )

            # Create a branch
            subprocess.call([
                'git',
                'checkout',
                '-b',
                change_title
            ])

            # Get a new change ID through the REST API
            change_id, long_id = gerrit.create_change(change_title)
            log.info('Change ID: {}'.format(change_id))
            log.info('Long ID: {}'.format(long_id))

            # Add all changes to be sent
            subprocess.call([
                'git',
                'add',
                '--all',
                args.repopath
            ])
            subprocess.call([
                'git',
                'commit',
                '-m',
                '{change_title}\n\nChange-Id: {change_id}'.format(
                    change_title=change_title,
                    change_id=change_id
                ),
                args.repopath
            ])

            # Push change to gerrit
            push_url = re.sub(
                'https://',
                'https://{username}:{password}@'.format(
                    username=config['gerrit_config']['web_username'],
                    password=config['gerrit_config']['web_password']
                ),
                config['gerrit_config']['gerrit_url']
            )
            subprocess.call([
                'git',
                'push',
                push_url + '/' + config['gerrit_config']['project_name'],
                'HEAD:refs/for/master'
            ])

            # Wait for verified state
            verfied = False

            while not gerrit.verified(long_id):
                # Wait for jenkins...
                time.sleep(5)

            # Self approve
            gerrit.self_approve_change(long_id)


if __name__ == '__main__':

    # Get arguments from the command line
    try:
        args = parse_args()
    except Exception as e:
        print('\nPlease provide correct argument:')
        print(e)
        exit(1)

    log.info("Starting the Freshdesk bot")

    # Decrypt and read configuration
    config = read_config(args.repopath, args.confname)

    # Change into the repo directory
    os.chdir(args.repopath)

    # Configure the endpoint
    endpoint = configure_flask_server(args, config)
    endpoint.run(config['flask_config']['listen_address'])


# vim: set shiftwidth=4 softtabstop=4 textwidth=0 wrapmargin=0 syntax=python: