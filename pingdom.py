import json
import os
import sys
import requests
import yaml

from requests import Response


class Pingdom:
    """
    This is an initial boilerplate implementation for a Pingdom API client, currently only supports adding/updating health checks
    but may get expanded as the need arises
    """
    # Define Pingdom API URL
    PINGDOM_API_URL = 'https://api.pingdom.com/api/3.1'

    def __init__(self, api_key):
        """
        Setup Pingdom API

        :type api_key: str
        :param api_key: Pingdom API key
        """
        self.__get_checks_cache__ = None
        self.__api_key__ = api_key

    def get_checks(self, cache=True) -> list:
        """
        Return list of configured checks from Pingdom

        :type cache: bool
        :param cache: If True, subsequent calls will return cached results

        :return: List of checks (refer to Pingdom API 3.1 documentation for contents)
        """
        if cache is True and self.__get_checks_cache__ is not None:
            return self.__get_checks_cache__

        response = self.__api_get__('/checks')

        if response.status_code != 200:
            raise Exception(response.content)

        response_json = json.loads(response.content)

        checks = []

        if 'checks' in response_json:
            for check_current in response_json['checks']:
                checks.append(check_current)

        self.__get_checks_cache__ = checks
        return checks

    def create_check(self, configuration) -> None:
        """
        Create new host check in Pingdom

        :type configuration: dict
        :param configuration: Configuration of the check (refer to API documentation)
        """
        response_create = self.__api_post__(
            url='/checks',
            params=configuration
        )

        if response_create.status_code != 200:
            raise Exception(response_create.content)

    def update_check(self, check_id, configuration) -> None:
        """
        Update existing host check in Pingdom

        :type check_id: int
        :param check_id: The check to update

        :type configuration: dict
        :param configuration: Configuration of the check (refer to API documentation)_
        """
        # Remove 'type' if it was supplied in the configuration (due to being lazy and copying the output from get_checks()
        if 'type' in configuration:
            del configuration['type']

        response_create = self.__api_put__(
            url='/checks/{check_id}'.format(check_id=check_id),
            params=configuration
        )

        if response_create.status_code != 200:
            raise Exception(response_create.content)

    def find_matching_checks(self, host, tags=None) -> list:
        """
        Return boolean flag indicating whether a check exists for the specified domain

        :type host: str
        :param host: The host as defined in the check

        :type tags: list or None
        :param tags: Optional list of tags that must be present

        :return: List of checks that match the hostname and tags
        """
        matches = []

        host = str(host).lower()
        checks = self.get_checks()

        found = []
        for check in checks:
            if 'host' in check:
                if check['host'] == host:
                    found.append(check)
            if 'hostname' in check:
                if check['hostname'] == host:
                    found.append(check)

        # If the host does not exist in the checks, die early
        if len(found) == 0:
            return []

        # If there is not tag filter defined, just check if the hostname exists
        if tags is None or len(tags) == 0:
            return found

        # Otherwise search for all tags requested
        for check in found:
            count_tags_found = 0
            response_detail = self.__api_get__('/checks/{id}'.format(id=check['id']))

            if response_detail.status_code != 200:
                raise Exception(response_detail.content)

            response_detail_json = json.loads(response_detail.content)
            check_detail = response_detail_json['check']

            # If there are no tags defined, get out of here
            if 'tags' not in check_detail:
                continue

            # Iterate all tags searching for the ones requested
            for tag in check_detail['tags']:
                for tag_current in tags:
                    if tag['name'] == tag_current:
                        count_tags_found += 1

            if count_tags_found == len(tags):
                matches.append(check)

        return matches

    # Internal HTTP methods

    def __api_delete__(self, url, params=None) -> Response:
        """
        Post DELETE request to Pingdom API

        :type url: str
        :param url: API endpoint

        :type params: dict
        :param params: Parameters to pass to endpoint

        :return: HTTP response
        """
        return requests.delete(
            url=self.__get_api_endpoint_url__(url),
            params=params,
            headers=self.__get_auth_header__()
        )

    def __api_get__(self, url, params=None) -> Response:
        """
        Post GET request to Pingdom API

        :type url: str
        :param url: API endpoint

        :type params: dict or None
        :param params: Parameters to pass to endpoint

        :return: HTTP response
        """
        return requests.get(
            url=self.__get_api_endpoint_url__(url),
            params=params,
            headers=self.__get_auth_header__()
        )

    def __api_post__(self, url, params=None) -> Response:
        """
        Post POST request to Pingdom API

        :type url: str
        :param url: API endpoint

        :type params: dict or None
        :param params: Parameters to pass to endpoint

        :return: HTTP response
        """
        return requests.post(
            url=self.__get_api_endpoint_url__(url),
            params=params,
            headers=self.__get_auth_header__()
        )

    def __api_put__(self, url, params=None) -> Response:
        """
        Post PUT request to Pingdom API

        :type url: str
        :param url: API endpoint

        :type params: dict or None
        :param params: Parameters to pass to endpoint

        :return: HTTP response
        """
        return requests.put(
            url=self.__get_api_endpoint_url__(url),
            params=params,
            headers=self.__get_auth_header__()
        )

    # noinspection PyMethodMayBeStatic
    def __get_api_endpoint_url__(self, url) -> str:
        """
        Return API endpoint URL

        :type url: str
        :param url: The user supplied endpoint

        :return: API endpoint URL
        """

        if str(url).lower().startswith(Pingdom.PINGDOM_API_URL.lower()):
            url = url[len(Pingdom.PINGDOM_API_URL):]

        return '{api_url}/{url}'.format(
            api_url=Pingdom.PINGDOM_API_URL,
            url=url.lstrip('/')
        )

    def __get_auth_header__(self) -> dict:
        """
        Return API authentication header

        :return: Dictionary containing Pingdom authentication header
        """
        return {'Authorization': 'Bearer {api_key}'.format(api_key=self.__api_key__)}

    @staticmethod
    def validate_configuration_yaml(configuration):
        """
        Perform some primitive validation on the configuration, throwing an exception error on failure

        :type configuration: dict
        :param configuration: The configuration as read from the YAML file
        """

        # Validate `gitops` configuration in YAML file

        if 'gitops' not in configuration:
            raise Exception('Unexpected file type: Could not locate required `gitops` tag')

        config_gitops = configuration['gitops']

        if isinstance(config_gitops, dict) is False:
            raise Exception('Configuration Error: Invalid `gitops` tag type, expected YAML object')

        for parameter in ['type', 'version']:
            if parameter not in config_gitops:
                raise Exception('Configuration Error: Could not locate required `gitops.{parameter}` tag'.format(parameter=parameter))

        gitops_type = configuration['gitops']['type']
        if gitops_type != 'pingdom-checks':
            raise Exception('Unexpected file type: The supplied file did not contain expected `gitops.type` value')

        gitops_version = str(configuration['gitops']['version'])
        if gitops_version not in ['1.0']:
            raise Exception('Unexpected file type: The file version was not recognized')

        # Validate `pingdom` configuration in YAML file

        if 'pingdom' not in configuration:
            raise Exception('Configuration Error: Could not locate required `pingdom` tag')

        config_pingdom = configuration['pingdom']

        if isinstance(config_pingdom, dict) is False:
            raise Exception('Configuration Error: Invalid `pingdom` tag type, expected YAML object')

        for parameter in ['tag', 'checks', 'teams', 'integrations']:
            if parameter not in config_pingdom:
                raise Exception('Configuration Error: Could not locate required `pingdom.{parameter}` tag'.format(parameter=parameter))

        # Validate `pingdom.teams` configuration in YAML file

        teams = {}
        if 'teams' in config_pingdom:
            if isinstance(config_pingdom['teams'], dict) is False:
                raise Exception('Configuration Error: Invalid `pingdom.teams` tag type, expected YAML object')

            # Iterate over teams and store in dictionary
            for team_key, team_id in config_pingdom['teams'].items():
                if isinstance(team_id, int) is False:
                    raise Exception('Configuration Error: Invalid `pingdom.teams` ID type, expected integer')
                teams[team_key] = team_id

        # Validate `pingdom.integrations` configuration in YAML file

        integrations = {}
        if 'integrations' in config_pingdom:
            if isinstance(config_pingdom['integrations'], dict) is False:
                raise Exception('Configuration Error: Invalid `pingdom.integrations` tag type, expected YAML object')

            # Iterate over integrations and store in dictionary
            for integration_key, integration_id in config_pingdom['integrations'].items():
                if isinstance(integration_id, int) is False:
                    raise Exception('Configuration Error: Invalid `pingdom.integrations` ID type, expected integer')
                integrations[integration_key] = integration_id

        # Validate `pingdom.checks` configuration in YAML file

        config_pingdom_checks = config_pingdom['checks']

        if isinstance(config_pingdom_checks, list) is False:
            raise Exception('Configuration Error: Invalid `pingdom.checks` tag type, expected YAML list')

        if 'default' in config_pingdom:
            if isinstance(config_pingdom['default'], dict) is False:
                raise Exception('Configuration Error: Invalid `pingdom.default` item type, expected YAML object')

        if 'default' in config_pingdom:
            default = config_pingdom['default']
        else:
            default = None

        for check in config_pingdom_checks:
            # Populate default values
            if default is not None:
                for key, value in default.items():
                    if key not in check:
                        check[key] = value

            if isinstance(config_pingdom_checks, list) is False:
                raise Exception('Configuration Error: Invalid `pingdom.checks` list item type, expected YAML list')

            # Ensure mandatory check parameters are present
            for parameter in ['name', 'host', 'type']:
                if parameter not in check:
                    raise Exception('Configuration Error: Could not locate mandatory `{parameter}` value in check'.format(parameter=parameter))
                if isinstance(check[parameter], str) is False:
                    raise Exception('Configuration Error: Invalid data type `{parameter}` in check, expected string value'.format(parameter=parameter))

            # If `teamids` were specified in the check, make sure they exist in the YAML file
            if 'teamids' in check:
                teamids = check['teamids']
                if isinstance(teamids, list) is False:
                    raise Exception('Configuration Error: Invalid data type `teamids` in check, expected YAML list'.format(parameter=parameter))

                for team_key in teamids:
                    if team_key not in teams:
                        raise Exception('Configuration Error: Unknown `teamids` name specified in check, ensure ID defined in `pingdom.teams` tag'.format(
                            parameter=parameter))

            # If `integrationids` were specified in the check, make sure they exist in the YAML file
            if 'integrationids' in check:
                integrationids = check['integrationids']
                if isinstance(integrationids, list) is False:
                    raise Exception('Configuration Error: Invalid data type `integrationids` in check, expected YAML list'.format(parameter=parameter))

                for integration_key in integrationids:
                    if integration_key not in integrations:
                        raise Exception(
                            'Configuration Error: Unknown `integrationids` name specified in check, ensure ID defined in `pingdom.integrations` tag'.format(
                                parameter=parameter))

    @staticmethod
    def process_configuration_yaml(configuration) -> None:
        """
        Process configuration file and create/update Pingdom health checks as appropriate
        Perform some primitive validation on the configuration, throwing an exception error on failure

        :type configuration: dict
        :param configuration: The configuration as read from the YAML file
        """
        tag = configuration['pingdom']['tag']
        teams = configuration['pingdom']['teams']
        integrations = configuration['pingdom']['integrations']

        error = False

        if 'default' in configuration['pingdom']:
            default = configuration['pingdom']['default']
        else:
            default = None

        for check in configuration['pingdom']['checks']:
            # Populate default values
            if default is not None:
                for key, value in default.items():
                    if key not in check:
                        check[key] = value

            host = check['host']

            # If team IDs were specified, convert them into their integer values
            tag_csv = '{tag},'.format(tag=tag)
            if 'tags' in check:
                for tag_current in check['tags']:
                    tag_csv += '{tag_current},'.format(tag_current=tag_current)
                check['tags'] = tag_csv.rstrip(',')

            # If team IDs were specified, convert them into their integer values
            if 'teamids' in check:
                team_ids_csv = ''
                for team_key in check['teamids']:
                    team_ids_csv += '{team_key},'.format(team_key=teams[team_key])
                check['teamids'] = team_ids_csv.rstrip(',')

            # If integration IDs were specified, convert them into their integer values
            if 'integrationids' in check:
                integration_ids_csv = ''
                for integration_key in check['integrationids']:
                    integration_ids_csv += '{integration_key},'.format(integration_key=integrations[integration_key])
                check['integrationids'] = integration_ids_csv.rstrip(',')

            matches = pingdom.find_matching_checks(host=host, tags=[tag])

            if len(matches) == 0:
                try:
                    # Create the new check
                    print('Creating Check: {host}'.format(host=host))
                    pingdom.create_check(configuration=check)
                except Exception as create_exception:
                    # Continue on failure but log the output
                    print('WARNING: Failed to create Pingdom health check')
                    print('{create_exception}'.format(create_exception=create_exception))
            else:
                try:
                    for check_current in matches:
                        # Update the existing check
                        print('Updating Check: {host}'.format(host=host))
                        check_id = check_current['id']
                        pingdom.update_check(check_id=check_id, configuration=check)

                except Exception as create_exception:
                    # Continue on failure but log the output
                    print('WARNING: Failed to update existing Pingdom health check')
                    print('{create_exception}'.format(create_exception=create_exception))
                    error = True

        if error is True:
            raise Exception('Update completed with one or more errors- please review logs messages')


def print_usage() -> None:
    """
    Print usage on argument errors
    """
    print('Github Actions: Pingdom Manager')
    print('Usage: python ./pingdom.py [api_key] [filename]')


if __name__ == '__main__':
    try:
        # Validate command-line arguments
        if len(sys.argv) != 3:
            print_usage()
            exit(1)

        filename = sys.argv[1]
        api_key = sys.argv[2]

        if os.path.exists(filename) is False:
            print('ERROR: Configuration file ({filename}) not found\n'.format(filename=filename))
            print_usage()
            exit(2)

        # Setup Pingdom API
        pingdom = Pingdom(api_key=api_key)

        # Load the YAML file contents from disk
        pingdom_config = open(filename, 'rt')
        configuration_yaml = yaml.full_load(pingdom_config.read())
        pingdom_config.close()

        # Validate the YAML file contents
        Pingdom.validate_configuration_yaml(configuration_yaml)

        # Load sites to be checked from YAML file
        Pingdom.process_configuration_yaml(configuration_yaml)
    except Exception as exception:
        # Dump all unhandled exceptions during execution
        print('ERROR: Unhandled exception error during YAML file processing')
        print(exception)
        exit(3)
