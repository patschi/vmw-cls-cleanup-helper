#!/usr/bin/env python3
import traceback
from os import environ

import api_vcenter
import cldata
from logger import log, debug

# Version
VERSION = [0, 3, 1]

# Settings
api_host = environ.get('PKR_VAR_vsphere_endpoint')
api_user = environ.get('PKR_VAR_vsphere_username')
api_pass = environ.get('PKR_VAR_vsphere_password')

content_library = environ.get('PKR_VAR_vsphere_content_library')

if '__main__' == __name__:
    log(sev='info', msg='Starting vmw-cls-cleanup {}...'.format('.'.join(map(str, VERSION))))

    # Create an instance of the vCenter API
    api = api_vcenter.create(api_host=api_host, api_user=api_user, api_pass=api_pass)
    api.allow_insecure_ssl(insecure=True)
    try:
        login = api.login()
        if not login:
            log(sev='error', msg='Failed to login to vCenter. Exiting...')
            exit(1)

        # Get all templates
        templates = api.get_cls_templates(library=content_library)
        if templates is None:
            log(sev='error', msg='Error occurred while retrieving Content Library templates.')

        # Use templates_data to convert the templates further
        templates = cldata.convert(templates=templates)
        # Output all templates if debug is enabled
        if debug:
            log(sev='debug', msg='Final data:')
            cldata.print_list(templates=templates)

        # Output the templates to be deleted, if debug is enabled
        templates = cldata.templates_to_delete(templates=templates, keep=1)
        if debug:
            log(sev='debug', msg='Final data for templates to be deleted:')
            cldata.print_list(templates=templates)

    except Exception as e:
        # Catch any exceptions and logout of VC
        log(sev='error', msg='Error occurred: {}'.format(e))
        print(traceback.format_exc())
        exit(1)
    finally:
        api.logout()

    log(sev='info', msg='Done.')
    exit(0)
