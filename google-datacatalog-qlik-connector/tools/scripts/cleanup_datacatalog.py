#!/usr/bin/python
#
# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import re

from google.cloud import datacatalog

__DEFAULT_DATACATALOG_LOCATION_ID = 'us'

__datacatalog = datacatalog.DataCatalogClient()


def __delete_entries_and_groups(project_ids):
    entry_name_pattern = '(?P<entry_group_name>.+?)/entries/(.+?)'

    query = 'system=qlik'

    scope = datacatalog.SearchCatalogRequest.Scope()
    scope.include_project_ids.extend(project_ids)

    request = datacatalog.SearchCatalogRequest()
    request.scope = scope
    request.query = query
    request.page_size = 1000

    # TODO Replace "search entries" by "list entries by group"
    #  when/if it becomes available.
    search_results = [
        result for result in __datacatalog.search_catalog(request)
    ]

    entry_group_names = []
    for result in search_results:
        try:
            __datacatalog.delete_entry(name=result.relative_resource_name)
            print('Entry deleted: {}'.format(result.relative_resource_name))
            entry_group_name = re.match(
                pattern=entry_name_pattern,
                string=result.relative_resource_name).group('entry_group_name')
            entry_group_names.append(entry_group_name)
        except Exception as e:
            print('Exception deleting Entry')
            print(e)

    # Delete any pre-existing Entry Groups.
    for entry_group_name in set(entry_group_names):
        try:
            __datacatalog.delete_entry_group(name=entry_group_name)
            print('--> Entry Group deleted: {}'.format(entry_group_name))
        except Exception as e:
            print('Exception deleting Entry Group')
            print(e)


def __delete_tag_templates(project_id, location_id):
    query = 'type=TAG_TEMPLATE name:\"Qlik Custom Property\"'

    scope = datacatalog.SearchCatalogRequest.Scope()
    scope.include_project_ids.append(project_id)

    request = datacatalog.SearchCatalogRequest()
    request.scope = scope
    request.query = query
    request.page_size = 1000

    search_results = [
        result for result in __datacatalog.search_catalog(request)
    ]

    # Add the dynamic Tag Template names
    template_names = [
        result.relative_resource_name for result in search_results
    ]

    # Add the static Tag Template names
    template_names.append(
        datacatalog.DataCatalogClient.tag_template_path(
            project_id, location_id, 'qlik_app_metadata'))
    template_names.append(
        datacatalog.DataCatalogClient.tag_template_path(
            project_id, location_id,
            'qlik_custom_property_definition_metadata'))
    template_names.append(
        datacatalog.DataCatalogClient.tag_template_path(
            project_id, location_id, 'qlik_dimension_metadata'))
    template_names.append(
        datacatalog.DataCatalogClient.tag_template_path(
            project_id, location_id, 'qlik_measure_metadata'))
    template_names.append(
        datacatalog.DataCatalogClient.tag_template_path(
            project_id, location_id, 'qlik_visualization_metadata'))
    template_names.append(
        datacatalog.DataCatalogClient.tag_template_path(
            project_id, location_id, 'qlik_sheet_metadata'))
    template_names.append(
        datacatalog.DataCatalogClient.tag_template_path(
            project_id, location_id, 'qlik_stream_metadata'))

    for name in template_names:
        __delete_tag_template(name)


def __delete_tag_template(name):
    try:
        __datacatalog.delete_tag_template(name=name, force=True)
        print('--> Tag Template deleted: {}'.format(name))
    except Exception as e:
        print('Exception deleting Tag Template')
        print(e)


def __parse_args():
    parser = argparse.ArgumentParser(
        description='Command line utility to remove all Qlik-related'
        ' metadata from Google Data Catalog')

    parser.add_argument('--datacatalog-project-ids',
                        help='List of Google Cloud project IDs split by comma.'
                        ' At least one must be provided.',
                        required=True)
    parser.add_argument(
        '--datacatalog-location-id',
        help='Google Cloud region where your Data Catalog metadata resides.',
        default=__DEFAULT_DATACATALOG_LOCATION_ID)

    return parser.parse_args()


if __name__ == "__main__":
    args = __parse_args()

    # Split multiple values separated by comma.
    datacatalog_project_ids = \
        [item for item in args.datacatalog_project_ids.split(',')]

    __delete_entries_and_groups(datacatalog_project_ids)
    for datacatalog_project_id in datacatalog_project_ids:
        __delete_tag_templates(datacatalog_project_id,
                               args.datacatalog_location_id)
