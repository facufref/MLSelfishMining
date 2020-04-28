import hashlib
import json
import requests
import threading
import random
import time
from uuid import uuid4
from sklearn.externals import joblib
from SelfishMiningDataManager import get_time_rate
from GeneralSettings import *


class SelfishMiningDetector(object):
    def __init__(self, interval=1):
        self.interval = interval
        self.uuid = str(uuid4()).replace('-', '')
        self.node = None
        self.chain = []

        # The miner starts to detect and mines forever
        thread = threading.Thread(target=self.detect_forever(), args=())
        thread.daemon = True
        thread.start()

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
            # print(f'{last_block}')
            # print(f'{block}')
            # print("\n-----------\n")
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

    def update_chain(self):
        best_chain = None
        max_length = 0
        neighbours = []

        response = requests.get(f'http://{host_address}{blockchain_port}/nodes/get')
        if response.status_code == 200:
            neighbours = response.json()['nodes']

        # Shuffle the list so we consult them in random order
        random.shuffle(neighbours)

        # Grab and verify the chains from all the nodes in our network
        for node in neighbours:
            if node == self.node:
                continue

            response = requests.get(f'http://{node}/chain', params={'uuid': self.uuid})

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                # Check if the length is longer and the chain is valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    best_chain = chain

        self.chain = best_chain

    def is_selfish(self):
        # First verify that our chain is up to date
        self.update_chain()

        if len(self.chain) < chunk_size + 1:
            return f'Waiting to have {chunk_size + 1} nodes to predict.'

        sample_chain = self.chain[-(chunk_size + 1):]
        rates = get_time_rate(sample_chain)
        rates.append(iterations_to_consult)
        rates.append(complexity)
        rates.append(6)  # TODO: calculate nodes automatically
        filename = f'Models/gradientBoosting.joblib.pkl'
        clf = joblib.load(filename)
        result = clf.get_predictions([rates])
        return f'The prediction is {result[0]}'

    def detect_forever(self):
        while True:
            print(self.is_selfish())
            time.sleep(10)


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
        guess = f'{last_proof}{proof}{last_hash}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:complexity] == "0" * complexity
