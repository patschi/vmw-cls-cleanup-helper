#!/usr/bin/env python3
from datetime import datetime
from os import environ

import requests
import tzlocal
import urllib3.exceptions

# Settings
debug = False
api_host = environ.get('PKR_VAR_vsphere_endpoint')
api_user = environ.get('PKR_VAR_vsphere_username')
api_pass = environ.get('PKR_VAR_vsphere_password')
content_library = environ.get('PKR_VAR_vsphere_content_library')


# Basic logging function
def log(severity, msg):
    timezone = tzlocal.get_localzone()
    date = datetime.now(tz=timezone).strftime('%Y-%m-%d %H:%M:%S %z')
    severity = severity.upper()
    print('[{0}] [{1: <5s}] {2}'.format(date, severity, msg))


# vCenter API
class VCAPI:
    def __init__(self, hostname, username, password):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.session_id = None
        self.insecure_ssl = False

    # General functions
    def allow_insecure_ssl(self, insecure):
        self.insecure_ssl = insecure
        if insecure:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # Login/Logout
    def login(self):
        log('info', 'Authenticating to vCenter as {}...'.format(self.username))
        api_url = 'https://{}/api/session'.format(self.hostname)
        resp = requests.post(api_url, auth=(self.username, self.password), verify=(not self.insecure_ssl))
        if resp.status_code != 201:
            log('error', 'Error occurred. API response: [{}] {}'.format(resp.status_code, resp.text))
            return

        log('info', ' Authenticated to vCenter.')
        self.session_id = resp.json()
        return True

    def logout(self):
        log('info', 'Logging out from vCenter...')

        api_url = 'https://{}/api/session'.format(self.hostname)
        if debug:
            log('debug', '- Contacting API: {}'.format(api_url))
        resp = requests.delete(api_url, verify=(not self.insecure_ssl),
                               headers={'vmware-api-session-id': self.session_id})
        if resp.status_code != 204:
            log('error', 'Error occurred. API response: [{}] {}'.format(resp.status_code, resp.text))
            return

        log('info', ' Logged out from vCenter.')
        return True

    # Generic API functions
    def get(self, req_url, payload=None):
        req_url = 'https://{}/api/{}'.format(api_host, req_url)
        if debug:
            log('debug', '- Contacting API {1} with payload {0}...'.format(payload, req_url))
        resp = requests.get(req_url, verify=(not self.insecure_ssl), params=payload,
                            headers={'vmware-api-session-id': self.session_id})
        if resp.status_code != 200:
            log('error', 'Error! API responded with: {}'.format(resp.status_code))
            return
        return resp.json()

    def post(self, req_url, payload):
        headers = {
            'content-type': 'application/json',
            'vmware-api-session-id': self.session_id
        }
        req_url = 'https://{}/api/{}'.format(api_host, req_url)
        if debug:
            log('debug', '- Contacting API {1} with payload {0}...'.format(payload, req_url))
        resp = requests.post(req_url, verify=(not self.insecure_ssl), json=payload, headers=headers)
        if resp.status_code != 200:
            log('error', 'Error! API responded with: {}'.format(resp.status_code))
            return
        return resp.json()

    # vCenter-specific functions
    def get_library_id(self, name):
        library_id = self.post('content/library?action=find', {'name': name, 'type': 'LOCAL'})
        if len(library_id) != 1:
            log('error', 'Error! Found {} Content Libraries with the name {}. Must be unambiguously. Exiting...'
                .format(len(library_id), name))
            exit(1)
        # We have only one match, so easy to pick the right one
        return library_id[0]

    def get_library_items(self, library_id):
        if debug:
            log('debug', 'Retrieving items in Content Library with ID {}...'.format(library_id))
        return self.get('content/library/item', payload={'library_id': library_id})

    def get_library_metadata(self, item_id):
        if debug:
            log('debug', 'Retrieving metadata for Content Library item {}...'.format(item_id))
        return self.get('content/library/item/{}'.format(item_id))


# MAIN CODE

def do_cleanup():
    # Get Content Library ID and check if we only have one identical match
    log('info', 'Searching for Content Library with name "{}"...'.format(content_library))
    clid = api.get_library_id(content_library)

    # Get all items in the Content Library
    log('info', 'Retrieving items in Content Library with ID {}...'.format(clid))
    cl_items = api.get_library_items(clid)

    # Go through the items and get metadata for each
    templates = {}
    for item in cl_items:
        log('info', ' Library-Item: {}'.format(item))

        metadata = api.get_library_metadata(item)
        if metadata is None:
            log('error', 'Error! Could not retrieve metadata for item {}. Skipping...'.format(item))
            continue

        templates[item] = metadata
        log('info', '   Name: {}'.format(metadata['name']))
        log('info', '   CreationTime: {}'.format(metadata['creation_time']))


if __name__ == '__main__':
    log('info', 'Starting...')

    # Create an instance of the vCenter API
    api = VCAPI(api_host, api_user, api_pass)
    api.allow_insecure_ssl(True)
    api.login()

    # Start cleanup
    try:
        do_cleanup()
    except Exception as e:
        # Catch any exceptions and logout of VC
        log('error', 'Error occurred: {}'.format(e))
    finally:
        api.logout()

    log('info', 'Done.')
    exit(0)
