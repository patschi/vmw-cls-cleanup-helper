#!/usr/bin/env python3
import re

from logger import log, debug
from api_vcenter import CLTemplate


def extract_by_name(template: CLTemplate) -> tuple[str, CLTemplate]:
    """
    Helper function to extract the name and date from the template name, CLTemplate class as source.
    :param template: The template object to extract the name from
    :return: A tuple containing the extracted name and the template object
    """
    # Get the name (without the unique timestamp)
    match = re.match(pattern=r"(.+?) \((\d+)\)", string=template.name)
    name = match.group(1).replace("_", " ").strip()
    log('debug', ' Extracted name found: {}'.format(name))
    # Return the name and template object
    return name, template


def merge_by_name(templates: dict) -> dict[str, list[CLTemplate]]:
    """
    Helper function to merge the extracted templates by name.
    :param templates: The list of templates to merge
    :return: The merged list of templates grouped by extracted name
    """
    log('debug', 'Merging templates by name...')
    # Extract the name and date from the template name
    extracted_templates = {}
    for template in templates:
        # Extract the name and template data
        extract = extract_by_name(templates[template])
        # Merge the extracted data with the existing list
        if extract[0] not in extracted_templates:
            extracted_templates[extract[0]] = []
        # Append the template to the list
        extracted_templates[extract[0]].append(extract[1])

    # The final data is now structured like:
    # {'name1': [CLTemplate, ...], ..., 'name2': [CLTemplate, ...]}

    log('debug', 'Merging complete: {} unique templates found, {} total templates.'
        .format(len(extracted_templates), len(templates)))
    return extracted_templates


def sort_by_creation_date(templates: dict[str, list[CLTemplate]]) -> dict[str, list[CLTemplate]]:
    """
    Helper function to sort the templates by creation date.
    :param templates: The list of templates to sort
    :return: The sorted list of templates
    """
    log('debug', 'Sorting templates by creation date...')
    # Sort the templates by creation date; newest first.
    for template in templates:
        templates[template].sort(key=lambda x: x.creation_time, reverse=True)

    return templates


def convert(templates: dict) -> dict[str, list[CLTemplate]]:
    """
    Main function to take care about data conversion. Convert the templates to a list of tuples.
    :param templates: The list of templates to convert
    :return: The converted and processed list of templates in form of a list of tuples: (name, [CLTemplate, ...])
    """
    log('debug', 'Converting template data...')
    # Extract the name and date from the template name
    data = merge_by_name(templates)
    # Sort the templates by creation date
    data = sort_by_creation_date(data)
    # Output data if debug is enabled
    if debug:
        log('debug', 'Final data:')
        for name in data:
            log('debug', ' Name: {}'.format(name))
            for template in data[name]:
                creation_date = template.creation_time.strftime('%Y-%m-%d %H:%M:%S %Z')
                log('debug', '  Template: {} / CreationTime: {}'.format(template.name, creation_date))
    # Return the final data
    return data
