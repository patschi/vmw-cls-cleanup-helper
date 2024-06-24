#!/usr/bin/env python3
import traceback
from os import environ

from logger import log, debug
import api_vcenter
import cldata

# Version
VERSION = [0, 3, 0]

# Settings
api_host = environ.get('PKR_VAR_vsphere_endpoint')
api_user = environ.get('PKR_VAR_vsphere_username')
api_pass = environ.get('PKR_VAR_vsphere_password')

content_library = environ.get('PKR_VAR_vsphere_content_library')

if '__main__' == __name__:
    log('info', 'Starting vmw-cls-cleanup {}...'.format('.'.join(map(str, VERSION))))

    # Create an instance of the vCenter API
    api = api_vcenter.create(api_host=api_host, api_user=api_user, api_pass=api_pass)
    api.allow_insecure_ssl(insecure=True)
    try:
        login = api.login()
        if not login:
            log('error', 'Failed to login to vCenter. Exiting...')
            exit(1)

        # Get all templates
        templates = api.get_cls_templates(library=content_library)
        if templates is None:
            log('error', 'Error occurred while retrieving Content Library templates.')

        # Use templates_data to convert the templates further
        data = cldata.convert(templates=templates)
        # Output all templates if debug is enabled
        if debug:
            log('debug', 'Final data:')
            cldata.print_list(templates=data)

        # Output the templates to be deleted, if debug is enabled
        data = cldata.templates_to_delete(templates=data, keep=1)
        if debug:
            log('debug', 'Final data for templates to be deleted:')
            cldata.print_list(templates=data)

    except Exception as e:
        # Catch any exceptions and logout of VC
        log('error', 'Error occurred: {}'.format(e))
        print(traceback.format_exc())
        exit(1)
    finally:
        api.logout()

    log('info', 'Done.')
    exit(0)
