from urllib.parse import urlparse

import requests


class Blockchain(object):
    def __init__(self):
        self.nodes = set()

    def register_node(self, address):
        """
        Add a new node to the list of nodes
        :param address: <str> Address of node. Eg. 'http://192.168.0.5:5000'
        :return: None
        """

        parsed_url = urlparse(address)
        if parsed_url.netloc:
            self.nodes.add(parsed_url.netloc)
        elif parsed_url.path:
            # Accepts an URL without scheme like '192.168.0.5:5000'.
            self.nodes.add(parsed_url.path)
        else:
            raise ValueError('Invalid URL')

    def unregister_node(self, address):
        """
        Remove a node from the list of nodes
        :param address: <str> Address of node. Eg. 'http://192.168.0.5:5000'
        :return: None
        """

        parsed_url = urlparse(address)
        if parsed_url.netloc:
            self.nodes.remove(parsed_url.netloc)
        elif parsed_url.path:
            # Accepts an URL without scheme like '192.168.0.5:5000'.
            self.nodes.remove(parsed_url.path)
        else:
            raise ValueError('Invalid URL')

    def get_all_wallets(self):
        wallets = list()
        for node in self.nodes:
            response = requests.get(f'http://{node}/wallet')
            for wallet in response.json()['wallets']:
                wallets.append(wallet)

        return wallets
