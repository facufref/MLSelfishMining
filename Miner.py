import hashlib
import json
import requests
import threading
import random
from time import time
from uuid import uuid4
from urllib.parse import urlparse
from GeneralSettings import host_address, blockchain_port


class Miner(object):
    def __init__(self, interval=1):
        self.interval = interval
        self.uuid = str(uuid4()).replace('-', '')
        self.pool = None
        self.chain = []
        self.current_transactions = []

        # Create the genesis block
        self.chain.append(self.new_block(previous_hash=1, proof=100))

        # The miner starts to mine and mines forever
        thread = threading.Thread(target=self.mine_forever, args=())
        thread.daemon = True
        thread.start()

    def new_block(self, proof, previous_hash=None):
        """
        Create a new Block in the Blockchain
        :param proof: <int> The proof given by the Proof of Work algorithm
        :param previous_hash: (Optional) <str> Hash of previous Block
        :return: <dict> New Block
        """

        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1])
        }

        # Reset the current list of transactions
        self.current_transactions = []

        return block

    def new_transaction(self, sender, recipient, amount):
        """
        Creates a new transaction to go into the next mined Block
        :param sender: <str> Address of the Sender
        :param recipient: <str> Address of the Recipient
        :param amount: <int> Amount
        :return: <int> The index of the Block that will hold this transaction
        """
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount
        })

        return self.last_block['index'] + 1

    def proof_of_work(self, last_block):
        """
        Simple Proof of Work Algorithm:
         - Find a number p' such that hash(pp') contains leading 4 zeroes
         - Where p is the previous proof, and p' is the new proof

        :param last_block: <dict> last Block
        :return: <int>
        """
        last_proof = last_block['proof']
        last_hash = self.hash(last_block)
        proof = 0
        count = 0

        while self.valid_proof(last_proof, proof, last_hash) is False:
            if count > 10**7:  # After a fixed amount of iterations, go see if anyone else already has the solution.
                return -1
            proof = random.randint(0, 10**10)  # The idea is to have a range big enough, but it will depend on complexity
            count += 1

        return proof

    def valid_chain(self, chain):
        """
        Determine if a given blockchain is valid
        :param chain: <list> A blockchain
        :return: <bool> True if valid, False if not
        """
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print("\n-----------\n")
            # Check that the hash of the block is correct
            last_block_hash = self.hash(last_block)
            if block['previous_hash'] != self.hash(last_block):
                return False

            # Check that the Proof of Work is correct
            if not self.valid_proof(last_block['proof'], block['proof'], last_block_hash):
                return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self):
        """
        This is our Consensus Algorithm, it resolves conflicts
        by replacing our chain with the longest one in the network.
        :return: <bool> True if our chain was replaced, False if not
        """
        neighbours = []
        response = requests.get(f'http://{host_address}{blockchain_port}/nodes/get')
        if response.status_code == 200:
            neighbours = response.json()['nodes']

        new_chain = None
        better_node = None

        # We're only looking for chains longer than ours
        max_length = len(self.chain)

        # Grab and verify the chains from all the nodes in our network
        for node in neighbours:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                # Check if the length is longer and the chain is valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain
                    better_node = node

        # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            self.chain = new_chain
            print('The chain was replaced')

            if self.pool is not None and better_node != self.pool:
                # Alert the pool that there is a better chain around
                if self.pool is not None:
                    requests.post(f'http://{self.pool}/pool/update_chain', json={'sender': None, 'chain': new_chain})
            return True
        return False

    def mine(self):
        # First verify that our chain is up to date
        self.resolve_conflicts()
        # We run the proof of work algorithm to get the next proof...
        last_block = self.last_block
        proof = self.proof_of_work(last_block)

        if proof == -1:
            return 'Unable to find the block, check with the network for updates and try again'

        # We must receive a reward for finding the proof.
        # The sender is "0" to signify that this node has mined a new coin.
        self.new_transaction(
            sender="0",
            recipient=self.uuid,
            amount=1
        )

        # Forge the new Block by adding it to the chain
        previous_hash = self.hash(last_block)
        block = self.new_block(proof, previous_hash)
        self.chain.append(block)

        # Alert the pool about the new node so it distributes the reward
        if self.pool is not None:
            response = requests.post(f'http://{self.pool}/pool/update_chain', json={'sender': self.uuid, 'chain': self.chain})
            self.chain = response.json()['chain']

        return block

    def mine_forever(self):
        while True:
            print(self.mine())

    def calculate_wallet(self):
        total = 0
        for block in self.chain:
            for transaction in block['transactions']:
                if transaction['recipient'] == self.uuid:
                    total += transaction['amount']
                elif transaction['sender'] == self.uuid:
                    total -= transaction['amount']

        return total

    def register_pool(self, address):
        parsed_url = urlparse(address)
        if parsed_url.netloc:
            self.pool = parsed_url.netloc
        elif parsed_url.path:
            # Accepts an URL without scheme like '192.168.0.5:5000'.
            self.pool = parsed_url.path
        else:
            raise ValueError('Invalid URL')

    def unregister_pool(self):
        self.pool = None


    @property
    def last_block(self):
        return self.chain[-1]

    @staticmethod
    def hash(block):
        """
        Creates a SHA-256 hash of a Block
        :param block: <dict> Block
        :return: <str>
        """

        # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @staticmethod
    def valid_proof(last_proof, proof, last_hash):
        """
        Validates the Proof
        :param last_proof: <int> Previous Proof
        :param proof: <int> Current Proof
        :param last_hash: <str> The hash of the Previous Block
        :return: <bool> True if correct, False if not.
        """
        complexity = 6
        guess = f'{last_proof}{proof}{last_hash}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:complexity] == "0" * complexity
