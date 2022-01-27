#!/usr/bin/env python3

"""Prometheus exporter for Wekan."""

# Imports
import os
import sys
import time
from datetime import datetime, timezone, timedelta
import signal
from prometheus_client import start_http_server, Gauge, REGISTRY, PROCESS_COLLECTOR, PLATFORM_COLLECTOR
import requests


class WekanConnector():
    """
    WekanConnector.
    Class to interacte with Wekan API.
    """

    def __init__(self, url, user, password):
        """
        Initialize a wekan connector object.
        :param url: Wekan base API URL
        :param user: Admin user to connect to Wekan API
        :param password: Admin password
        """
        self.user = user
        self.password = password

        if url.endswith('/'):
            self.api_url = url[:-1]
        else:
            self.api_url = url

        self._login()

    def _login(self):
        """
        Login via the API to a Wekan instance.
        """
        login = requests.post(
            self.api_url + '/users/login',
            data={
                "username": self.user,
                "password": self.password
            })

        if login.status_code != 200:
            raise Exception('Unable to login to {} : {}'.format(self.api_url, login.reason))

        data = login.json()
        self.token = data['token']
        self.token_expiration_date = datetime.strptime(
            data['tokenExpires'],
            "%Y-%m-%dT%H:%M:%S.%fZ"
        ).replace(tzinfo=timezone.utc)

    def collect_metrics(self):
        """
        Collect metrics from Wekan API
        """
        # Get current date
        now = datetime.now(tz=timezone.utc)
        # Check if token if still valid for 1h
        if now >= (self.token_expiration_date - timedelta(hours=1)):
            self._login()

        # Prepare headers and result
        headers = {'Authorization': 'Bearer ' + self.token}
        data = {}

        # Get users metrics
        users = requests.get(self.api_url + '/api/users', headers=headers).json()
        # Users are a list, a JSON is generated if the request fails
        # But the request itself will always send a HTTP 200, even if it fails...
        if isinstance(users, dict) and users.get('statusCode', 200) != 200:
            raise Exception('Unable to get users : {}'.format(users['reason']))
        data['users_total'] = len(users)

        # Get boards metrics
        boards_count = requests.get(self.api_url + '/api/boards_count', headers=headers).json()
        # Same here, errors return HTTP 200 with a JSON...
        if isinstance(boards_count, dict) and boards_count.get('statusCode', 200) != 200:
            raise Exception('Unable to get boards count : {}'.format(boards_count['reason']))
        data['public_boards_count'] = boards_count['public']
        data['private_boards_count'] = boards_count['private']

        return data


# Define an exit function
def exit_handler(sig, frame):
    """
    Exit script properly
    """
    print('Terminating...')
    sys.exit(0)


def main():
    """Main function"""
    # Number of seconds between 2 metrics collection
    collect_interval = int(os.getenv('EXPORTER_COLLECT_INTERVAL', "60"))
    # Port for metrics server
    exporter_port = 8000
    # Get instance name for metrics tag
    instance_name = os.getenv('INSTANCE_NAME')
    if instance_name is None:
        print("INSTANCE_NAME must be set.")
        return None
    # Get API URL
    api_url = os.getenv("API_URL", "https://kanban.yourdomain.com")
    # Get API credentials
    api_user = os.getenv("EXPORTER_API_USER", "admin")
    api_password = os.getenv("EXPORTER_API_PASSWORD")
    if api_password is None:
        print("EXPORTER_API_PASSWORD must be set.")
        return None

    # Connect to Wekan API
    api_conn = WekanConnector(api_url, api_user, api_password)

    # Remove unwanted Prometheus metrics
    [REGISTRY.unregister(c) for c in [
        PROCESS_COLLECTOR,
        PLATFORM_COLLECTOR,
        REGISTRY._names_to_collectors['python_gc_objects_collected_total']
    ]]

    # Start Prometheus exporter server
    start_http_server(exporter_port)

    # Register metrics
    users_gauge = Gauge(
        'wekan_users_total',
        'Number of accounts on the instance',
        ['instance_name']
    )
    boards_gauge = Gauge(
        'wekan_boards_total',
        'Number of boards on the instance',
        ['instance_name', 'type']
    )

    # Loop forever
    while True:
        # Get metrics
        metrics = api_conn.collect_metrics()

        # Update metrics
        users_gauge.labels(instance_name=instance_name).set(metrics['users_total'])
        boards_gauge.labels(instance_name=instance_name, type="private").set(metrics['private_boards_count'])
        boards_gauge.labels(instance_name=instance_name, type="public").set(metrics['public_boards_count'])

        # Wait before next metrics collection
        time.sleep(collect_interval)


if __name__ == '__main__':
    # Catch SIGINT and SIGTERM signals
    signal.signal(signal.SIGINT, exit_handler)
    signal.signal(signal.SIGTERM, exit_handler)
    main()
