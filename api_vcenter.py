#!/usr/bin/env python3
from dataclasses import dataclass
from datetime import datetime

import requests
import urllib3.exceptions

from logger import log


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
        """
        Class initialization. Sets up object for the vCenter API connection.
        :param hostname: The hostname of the vCenter server
        :param username: The username to authenticate
        :param password: The password to authenticate
        """
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
            log(sev='warn', msg='Insecure SSL connections are allowed. Self-signed certificates will be accepted.')
            urllib3.disable_warnings(category=urllib3.exceptions.InsecureRequestWarning)

    # Generic API functions
    def get(self, path: str, payload: dict = None) -> (bool, int, dict or str):
        """
        Generic GET function to contact the vCenter API.
        :param path: The API endpoint to contact
        :param payload: The payload to send
        :return: The JSON response from the API
        """
        url = 'https://{}/api/{}'.format(self.hostname, path)
        log(sev='debug', msg='- Contacting API via GET {1} with payload {0}...'.format(payload, url))
        resp = requests.get(url=url, verify=(not self.insecure_ssl), params=payload,
                            headers={'vmware-api-session-id': self.session_id})

        if not resp.ok:
            log(sev='error', msg='Error! API responded with: {}, content: {}'.format(resp.status_code, resp.text))
            return False, resp.status_code, resp.text

        # Check if we have a JSON response from GET request
        json = "<unknown>"
        if resp.text:
            json = resp.json()
        return True, resp.status_code, json

    def post(self, path: str, payload: dict = None) -> (bool, int, dict or str):
        """
        Generic POST function to contact the vCenter API.
        :param path: The API endpoint to contact
        :param payload: The payload to send
        :return: The JSON response from the API
        """
        headers = {
            'content-type': 'application/json',
            'vmware-api-session-id': self.session_id
        }
        url = 'https://{}/api/{}'.format(self.hostname, path)
        log(sev='debug', msg='- Contacting API {1} via POST with payload {0}...'.format(payload, url))
        resp = requests.post(url=url, verify=(not self.insecure_ssl), json=payload, headers=headers)

        if not resp.ok:
            log(sev='error', msg='Error! API responded with: {}, content: {}'.format(resp.status_code, resp.text))
            return False, resp.status_code, resp.text

        # Check if we have a JSON response from POST request
        json = "<unknown>"
        if resp.text:
            json = resp.json()
        return True, resp.status_code, json

    def delete(self, path: str, payload: dict = None) -> (bool, int, dict or str):
        """
        Generic DELETE function to contact the vCenter API for purpose of deleting stuff.
        :param path: The API endpoint to contact
        :param payload: The payload to send
        :return: The JSON response from the API
        """
        headers = {
            'content-type': 'application/json',
            'vmware-api-session-id': self.session_id
        }
        url = 'https://{}/api/{}'.format(self.hostname, path)
        log(sev='debug', msg='- Contacting API {1} via DELETE with payload {0}...'.format(payload, url))
        resp = requests.delete(url=url, verify=(not self.insecure_ssl), json=payload, headers=headers)
        if not resp.ok:
            log(sev='error', msg='Error! API responded with: {}, content: {}'.format(resp.status_code, resp.text))
            return False, resp.status_code, resp.text

        # Check if we have a JSON response from POST request
        json = "<unknown>"
        if resp.text:
            json = resp.json()
        return True, resp.status_code, json

    # Login/Logout
    def login(self) -> bool:
        """
        Authenticate to the vCenter API.
        :return: True if the login was successful, False otherwise
        """
        log(sev='info', msg='Authenticating to vCenter as {}...'.format(self.username))
        api_url = 'https://{}/api/session'.format(self.hostname)
        resp = requests.post(url=api_url, auth=(self.username, self.password), verify=(not self.insecure_ssl))
        if resp.status_code != 201:
            log(sev='error', msg='Error occurred. API response: [{}] {}'
                .format(resp.status_code, resp.text))
            return False

        log(sev='debug', msg=' Authenticated to vCenter.')
        self.session_id = resp.json()
        return True

    def logout(self) -> bool:
        """
        Logout from the vCenter API.
        :return: True if the logout was successful, False otherwise
        """
        log(sev='info', msg='Logging out from vCenter...')

        api_url = 'https://{}/api/session'.format(self.hostname)
        log(sev='debug', msg='- Contacting API: {}'.format(api_url))
        resp = requests.delete(url=api_url, verify=(not self.insecure_ssl),
                               headers={'vmware-api-session-id': self.session_id})
        if resp.status_code != 204:
            log(sev='error', msg='Error occurred. API response: [{}] {}'
                .format(resp.status_code, resp.text))
            return False

        log(sev='debug', msg=' Logged out from vCenter.')
        return True

    # Content Library-specific functions for vCenter
    def get_library_id(self, name: str) -> str or None:
        """
        Get the ID of a Content Library by its name.
        :param name: The name of the Content Library
        :return: The ID of the Content Library
        """
        success, _, library_id = self.post(path='content/library?action=find', payload={'name': name, 'type': 'LOCAL'})
        if not success:
            return None
        if len(library_id) != 1:
            log(sev='error', msg='Error! Found {} Content Libraries with the name {}. Must be unambiguously. Exiting...'
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
        log(sev='debug', msg='Retrieving items in Content Library with ID {}...'.format(library_id))
        success, _, output = self.get(path='content/library/item', payload={'library_id': library_id})
        if not success:
            return None
        return output

    def get_library_item_metadata(self, item_id: str) -> dict or None:
        """
        Get metadata for a Content Library item. Like creation time, etc.
        :param item_id: The ID of the Content
        :return: The metadata for the Content Library item as dict
        """
        log(sev='debug', msg='Retrieving metadata for Content Library item {}...'.format(item_id))
        success, _, output = self.get(path='content/library/item/{}'.format(item_id))
        if not success:
            return None
        return output

    def delete_library_item(self, item_id: str) -> (bool, str or None):
        """
        Delete a Content Library item.
        :param item_id: The ID of the Content Library item
        :return: True if the deletion was successful, int otherwise
        """
        log(sev='debug', msg='Deleting Content Library item {}...'.format(item_id))
        success, status_code, output = self.delete(path='content/library/item/{}'.format(item_id), payload={})
        if status_code != 204:
            return False, output
        return True, None

    def get_cls_templates(self, library: str) -> dict or None:
        """
        The main cleanup function. This function will go through the Content Library and delete all outdated items.
        :param library: The name of the Content Library
        :return: The list of Content Library items as dict
        """
        # Get Content Library ID and check if we only have one identical match
        clid = self.get_library_id(name=library)
        if clid is None:
            log(sev='error', msg='Error! Error occurred while retrieving Content Library ID.')
            return

        log(sev='info', msg='Content Library ID for "{}" is: {}'.format(library, clid))

        # Get all items in the Content Library
        log(sev='info', msg='Retrieving items in Content Library with ID {}...'.format(clid))
        cl_items = self.get_library_items(library_id=clid)

        # Check if we have any items in the Content Library
        if cl_items is None:
            log(sev='error', msg='Error! Error occurred while retrieving Content Library items.')
            return

        items_found = len(cl_items)
        log(sev='debug', msg='Found {} items in Content Library.'.format(items_found))
        if items_found == 0:
            return {}

        # Go through the items and get metadata for each
        cls_templates = {}
        for item in cl_items:
            log(sev='debug', msg=' Library-Item: {}'.format(item))

            metadata = self.get_library_item_metadata(item_id=item)
            if metadata is None:
                log(sev='warning', msg='Error! Could not retrieve metadata for item {}. Skipping...'.format(item))
                continue

            # Convert some metadata to datetime objects
            metadata['creation_time'] = datetime.fromisoformat(metadata['creation_time'].replace('Z', '+00:00'))
            metadata['last_modified_time'] = datetime.fromisoformat(
                metadata['last_modified_time'].replace('Z', '+00:00'))

            # Create a CLTemplate object from the metadata
            metadata = CLTemplate(**metadata)
            cls_templates[item] = metadata
            log(sev='debug', msg='  Name: {} / CreationTime: {}'
                .format(metadata.name, metadata.creation_time))

        return cls_templates


# Wrapper
def create(api_host, api_user, api_pass) -> VCAPI or None:
    """
    Wrapper function to create an instance of the VCAPI class.
    :param api_host: The hostname of the vCenter server
    :param api_user: The username to authenticate
    :param api_pass: The password to authenticate
    :return: An instance of the VCAPI class
    """
    # Check if all required parameters are set
    if not api_host or not api_user or not api_pass:
        log(sev='error', msg='Missing required parameters for vCenter API! Cannot proceed.')
        return None
    return VCAPI(hostname=api_host, username=api_user, password=api_pass)
