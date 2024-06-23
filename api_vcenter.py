#!/usr/bin/env python3
from datetime import datetime
from logger import log
import requests
import urllib3.exceptions
from dataclasses import dataclass


# Template Object
@dataclass
class CLTemplate:
    """
    Dataclass to hold metadata for a Content Library item.
    """
    id: str = None  # '91408a54-3932-4797-959f-5235b4d7cc90'
    creation_time: datetime = None  # datetime('2024-05-26T00:43:52.651Z')
    last_modified_time: datetime = None  # datetime('2024-05-26T00:44:14.630Z')
    description: str = None  # 'Ubuntu 24.04 Template [...]'
    type: str = None  # 'vm-template'
    version: str = None  # '1'
    content_version: str = None  # '2'
    library_id: str = None  # '02c04568-0e25-45a1-b23a-39d912b86e58'
    size: int = None  # 6027768102
    cached: bool = None  # True
    name: str = None  # 'Ubuntu_24.04-Template (202405260033)'
    security_compliance: bool = None  # True
    metadata_version: str = None  # '1'


# vCenter API Class
class VCAPI:
    """Class to interact with the vCenter API."""

    def __init__(self, hostname: str, username: str, password: str):
        """Class initialization. Sets up the vCenter API connection."""
        self.hostname = hostname
        self.username = username
        self.password = password
        self.session_id = None
        self.insecure_ssl = False

    # General functions
    def allow_insecure_ssl(self, insecure: bool) -> None:
        """
        Allow insecure SSL connections to the vCenter API (self-signed certificates)
        :param insecure: The flag to allow insecure SSL connections
        :return: None
        """
        self.insecure_ssl = insecure
        if insecure:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # Generic API functions
    def get(self, req_url: str, payload: dict = None) -> dict or None:
        """
        Generic GET function to contact the vCenter API.
        :param req_url: The API endpoint to contact
        :param payload: The payload to send
        :return: The JSON response from the API
        """
        req_url = 'https://{}/api/{}'.format(self.hostname, req_url)
        log('debug', '- Contacting API {1} with payload {0}...'.format(payload, req_url))
        resp = requests.get(req_url, verify=(not self.insecure_ssl), params=payload,
                            headers={'vmware-api-session-id': self.session_id})
        if resp.status_code != 200:
            log('error', 'Error! API responded with: {}'.format(resp.status_code))
            return None
        return resp.json()

    def post(self, req_url: str, payload: dict = None) -> dict or None:
        """
        Generic POST function to contact the vCenter API.
        :param req_url: The API endpoint to contact
        :param payload: The payload to send
        :return: The JSON response from the API
        """
        headers = {
            'content-type': 'application/json',
            'vmware-api-session-id': self.session_id
        }
        req_url = 'https://{}/api/{}'.format(self.hostname, req_url)
        log('debug', '- Contacting API {1} with payload {0}...'.format(payload, req_url))
        resp = requests.post(req_url, verify=(not self.insecure_ssl), json=payload, headers=headers)
        if resp.status_code != 200:
            log('error', 'Error! API responded with: {}'.format(resp.status_code))
            return
        return resp.json()

    # Login/Logout
    def login(self) -> bool:
        """
        Authenticate to the vCenter API.
        :return: True if the login was successful, False otherwise
        """
        log('info', 'Authenticating to vCenter as {}...'.format(self.username))
        api_url = 'https://{}/api/session'.format(self.hostname)
        resp = requests.post(api_url, auth=(self.username, self.password), verify=(not self.insecure_ssl))
        if resp.status_code != 201:
            log('error', 'Error occurred. API response: [{}] {}'.format(resp.status_code, resp.text))
            return False

        log('debug', ' Authenticated to vCenter.')
        self.session_id = resp.json()
        return True

    def logout(self) -> bool:
        """
        Logout from the vCenter API.
        :return: True if the logout was successful, False otherwise
        """
        log('info', 'Logging out from vCenter...')

        api_url = 'https://{}/api/session'.format(self.hostname)
        log('debug', '- Contacting API: {}'.format(api_url))
        resp = requests.delete(api_url, verify=(not self.insecure_ssl),
                               headers={'vmware-api-session-id': self.session_id})
        if resp.status_code != 204:
            log('error', 'Error occurred. API response: [{}] {}'.format(resp.status_code, resp.text))
            return False

        log('debug', ' Logged out from vCenter.')
        return True

    # Content Library-specific functions for vCenter
    def get_library_id(self, name: str) -> str or None:
        """
        Get the ID of a Content Library by its name.
        :param name: The name of the Content Library
        :return: The ID of the Content Library
        """
        library_id = self.post('content/library?action=find', {'name': name, 'type': 'LOCAL'})
        if len(library_id) != 1:
            log('error', 'Error! Found {} Content Libraries with the name {}. Must be unambiguously. Exiting...'
                .format(len(library_id), name))
            return None
        # We have only one match, so easy to pick the right one
        return library_id[0]

    def get_library_items(self, library_id: str) -> dict or None:
        """
        Get all items in a Content Library.
        :param library_id: The ID of the Content Library
        :return: The list of items in the Content Library
        """
        log('debug', 'Retrieving items in Content Library with ID {}...'.format(library_id))
        return self.get('content/library/item', payload={'library_id': library_id})

    def get_library_item_metadata(self, item_id: str) -> dict or None:
        """
        Get metadata for a Content Library item. Like creation time, etc.
        :param item_id: The ID of the Content
        :return: The metadata for the Content Library item as dict
        """
        log('debug', 'Retrieving metadata for Content Library item {}...'.format(item_id))
        return self.get('content/library/item/{}'.format(item_id))

    def delete_library_item(self, item_id: str) -> bool:
        """
        Delete a Content Library item.
        :param item_id: The ID of the Content Library item
        :return: True if the deletion was successful, False otherwise
        """
        log('debug', 'Deleting Content Library item {}...'.format(item_id))
        return self.post('content/library/item/{}/action/delete'.format(item_id), {})

    def get_cls_templates(self, library: str) -> dict or None:
        """
        The main cleanup function. This function will go through the Content Library and delete all outdated items.
        :return: The list of Content Library items as dict
        """
        # Get Content Library ID and check if we only have one identical match
        clid = self.get_library_id(library)
        if clid is None:
            log('error', 'Error! Error occurred while retrieving Content Library ID.')
            return

        log('info', 'Content Library ID for "{}" is: {}'.format(library, clid))

        # Get all items in the Content Library
        log('info', 'Retrieving items in Content Library with ID {}...'.format(clid))
        cl_items = self.get_library_items(clid)

        # Check if we have any items in the Content Library
        if cl_items is None:
            log('error', 'Error! Error occurred while retrieving Content Library items.')
            return

        if len(cl_items) == 0:
            log('error', 'No items found in Content Library.')
            return

        # Go through the items and get metadata for each
        cls_templates = {}
        for item in cl_items:
            log('debug', ' Library-Item: {}'.format(item))

            metadata = self.get_library_item_metadata(item)
            if metadata is None:
                log('warning', 'Error! Could not retrieve metadata for item {}. Skipping...'.format(item))
                continue

            # Convert some metadata to datetime objects
            metadata['creation_time'] = datetime.fromisoformat(metadata['creation_time'].replace('Z', '+00:00'))
            metadata['last_modified_time'] = datetime.fromisoformat(
                metadata['last_modified_time'].replace('Z', '+00:00'))

            # Create a CLTemplate object from the metadata
            metadata = CLTemplate(**metadata)
            cls_templates[item] = metadata
            log('debug', '  Name: {} / CreationTime: {}'.format(metadata.name, metadata.creation_time))

        return cls_templates


# Wrapper function to create an instance of the VCAPI class
def create(api_host, api_user, api_pass):
    return VCAPI(api_host, api_user, api_pass)
