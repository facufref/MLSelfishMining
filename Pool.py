from urllib.parse import urlparse
from uuid import uuid4
import requests


class Pool(object):
    def __init__(self):
        self.uuid = str(uuid4()).replace('-', '')
        self.members = []
        self.chain = []

    def register_member(self, address, uuid):
        """
        Add a new member to the list of members
        :param address: <str> Address of member. Eg. 'http://192.168.0.5:5000'
        :param uuid: <str> UUID of member.
        :return: None
        """

        final_address = self.parse_address(address)

        self.members.append({'uuid': uuid, 'address': final_address})

    def unregister_member(self, address):
        """
        Remove a node from the list of members
        :param address: <str> Address of node. Eg. 'http://192.168.0.5:5000'
        :return: None
        """

        final_address = self.parse_address(address)

        for member in self.members:
            if member['address'] == final_address:
                self.members.remove(member)
                return

    def update_chain(self, new_chain, sender):
        """
        This function updates Pool's chain with the new longest one,
        every member in the pool will consult it to know which is the longest one.
        :return: <bool> True if our chain was replaced, False if not
        """
        # Check if the length is longer.
        # We will trust the miners for now so no need to use "valid_chain(chain)" validation
        if len(new_chain) > len(self.chain):
            self.chain = new_chain
            print('The chain was replaced')

            # Distribute the price between everyone
            if sender is not None:
                for member in self.members:
                    if member['uuid'] == sender:
                        pass
                    else:
                        self.chain[-1]['transactions'].append({
                            'sender': sender,
                            'recipient': member['uuid'],
                            'amount': 1/len(self.members)
                        })
            return True
        return False

    def get_all_wallets(self):
        wallets = list()
        for node in self.members:
            wallet = requests.get(f'http://{node["address"]}/wallet')
            wallets.append(wallet.json()['wallets'][0])

        return wallets

    @staticmethod
    def parse_address(address):
        parsed_url = urlparse(address)
        if parsed_url.netloc:
            final_address = parsed_url.netloc
        elif parsed_url.path:
            # Accepts an URL without scheme like '192.168.0.5:5000'.
            final_address = parsed_url.path
        else:
            raise ValueError('Invalid URL')
        return final_address
