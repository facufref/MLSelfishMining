from urllib.parse import urlparse
from uuid import uuid4
import requests
import random


class SelfishPool(object):
    def __init__(self):
        self.uuid = str(uuid4()).replace('-', '')
        self.members = []
        self.private_chain = []
        self.public_chain = []
        self.last_advantage = 0
        self.delta_prev = 0
        self.private_chain_length = 0

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
        if sender is not None and len(new_chain) > len(self.private_chain):  # My pool found a block
            self.delta_prev = len(self.private_chain) - len(self.public_chain)
            self.private_chain = new_chain  # append new block to private chain
            self.distribute_reward(sender)
            self.private_chain_length = self.private_chain_length + 1
            print(f'Advantage of {len(self.private_chain) - len(self.public_chain)}')
            if self.delta_prev == 0 and self.private_chain_length == 2:
                self.public_chain = self.private_chain  # publish all of the private chain
                self.private_chain_length = 0
                print('publish all of the private chain case 1')
            return True
        elif sender is None and len(new_chain) > len(self.public_chain):  # Others found a block
            self.delta_prev = len(self.private_chain) - len(self.public_chain)
            self.public_chain = new_chain  # append new block to public chain
            print(f'Advantage of {len(self.private_chain) - len(self.public_chain)}')
            if self.delta_prev == 0:
                self.private_chain = self.public_chain
                self.fork_private_chain()
                self.private_chain_length = 1
                print('They win, so we fork')
                return True
            elif self.delta_prev == 1:  # Advantage was 1, now is 0
                self.public_chain = self.private_chain
                self.private_chain_length = 0
                print('Publish last block of the private chain')
            elif self.delta_prev == 2:  # Advantage was 2, now is 1
                self.public_chain = self.private_chain
                self.private_chain_length = 0
                print('Publish all of the private chain case 2')
            elif self.delta_prev > 2:  # Advantage was n >= 3, now is n-1 >= 2
                self.public_chain = self.private_chain[:(len(self.public_chain) + 1)]
                print('Publish first unpublished block in private block.')
            else:
                self.private_chain = self.public_chain
                self.fork_private_chain()
                self.private_chain_length = 1
                print('They win, so we fork')
        return False

    def fork_private_chain(self):
        random_member_uuid = random.choice(self.members)['uuid']
        new_transactions = [{
            'sender': "0",
            'recipient': random_member_uuid,
            'amount': 1
        }]
        self.private_chain[-1]['transactions'] = new_transactions
        self.distribute_reward(random_member_uuid)

    def get_selfish_chain(self, sender_uuid):
        if self.is_member(sender_uuid):
            return self.private_chain
        else:
            return self.public_chain

    def distribute_reward(self, sender):
        for member in self.members:
            if member['uuid'] == sender:
                pass
            else:
                self.private_chain[-1]['transactions'].append({
                    'sender': sender,
                    'recipient': member['uuid'],
                    'amount': 1 / len(self.members)
                })

    def is_member(self, uuid):
        for member in self.members:
            if member['uuid'] == uuid:
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
