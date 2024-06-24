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
dry_run = environ.get('CLEANUP_SCRIPT_DEBUG_DRY_RUN', 'false').lower() == 'true'

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

        # Delete the templates
        log(sev='info', msg='Deleting templates...')
        if dry_run:
            log(sev='warn', msg='/!!\\ Dry-run enabled, not sending deletion API requests! /!!\\')

        # Go through each template
        for template in templates:
            log(sev='info', msg=' Cleaning up template "{}"...'.format(template))
            # Go through each item per template type and delete it
            for item in templates[template]:
                log(sev='info', msg='  Deleting template "{}" with ID {}...'.format(item.name, item.id))
                # Skip deletion if dry-run is enabled
                if dry_run:
                    continue
                # Delete the template item
                deletion, deletion_error = api.delete_library_item(item_id=item.id)
                # Check if the deletion was successful
                if deletion:
                    log(sev='info', msg='   Successfully deleted template {}.'.format(item.id))
                else:
                    log(sev='warn', msg='   Error occurred while deleting template {}: {}.'
                        .format(item.id, deletion_error))

                ### TEST ONLY ###
                raise Exception('ONE TEMPLATE DELETED - TEST END')

        # We're done! Templates cleaned up.
        log(sev='info', msg='Finished cleaning up templates.')

    except Exception as e:
        # Catch any exceptions and logout of VC
        log(sev='error', msg='Error occurred: {}'.format(e))
        print(traceback.format_exc())
        exit(1)
    finally:
        api.logout()

    log(sev='info', msg='Done.')
    exit(0)
