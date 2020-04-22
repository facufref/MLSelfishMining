from argparse import ArgumentParser
from flask import Flask, jsonify, request
from Miner import Miner
import requests
from GeneralSettings import host_address, blockchain_port

# Instantiate our Node
app = Flask(__name__)

# Instantiate the Miner
miner = Miner()


@app.route('/mine', methods=['GET'])
def mine():
    result = miner.mine()

    if type(result) is str:
        return jsonify({
            'message': result
        }), 200

    response = {
        'message': "New Block Forged",
        'index': result['index'],
        'transactions': result['transactions'],
        'proof': result['proof'],
        'previous_hash': result['previous_hash'],
        'timestamp': result['timestamp']
    }

    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400

    # Create a new Transaction
    index = miner.new_transaction(values['sender'], values['recipient'], values['amount'])

    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': miner.chain,
        'length': len(miner.chain),
    }
    return jsonify(response), 200


@app.route('/wallet', methods=['GET'])
def calculate_wallet():
    total = miner.calculate_wallet()
    wallet = {
        'node': f"{host_address}{port}",
        'uuid': miner.uuid,
        'pool': miner.pool,
        'total': total
    }
    response = {
        'message': 'Returning existing wallets',
        'wallets': [wallet]
    }
    return jsonify(response), 200


@app.route('/nodes/register_pool', methods=['POST'])
def register_pool():
    values = request.get_json()

    pool = values.get('address')
    if pool is None:
        return "Error: Please supply a valid pool", 400

    requests.post(f'http://{pool}/pool/register', json={'address': f"{host_address}{port}", 'uuid': miner.uuid})
    requests.post(f'http://{host_address}{blockchain_port}/nodes/unregister', json={'address': f"{host_address}{port}"})
    miner.register_pool(pool)

    response = {
        'message': 'Node registered as part of a pool',
        'pool': pool,
    }
    return jsonify(response), 201


@app.route('/nodes/unregister_pool', methods=['GET'])
def unregister_pool():

    if miner.pool is None:
        return "Error: Miner is not registered to any pool", 400

    requests.post(f'http://{miner.pool}/pool/unregister', json={'address': f"{host_address}{port}"})
    requests.post(f'http://{host_address}{blockchain_port}/nodes/register', json={'nodes': [f"{host_address}{port}"]})
    miner.unregister_pool()

    response = {
        'message': 'Node unregistered from the pool'
    }
    return jsonify(response), 200


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5001, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    #  On start, register the Miner on the blockchain
    requests.post(f'http://{host_address}{blockchain_port}/nodes/register', json={'nodes': [f"{host_address}{port}"]})

    app.run(host='0.0.0.0', port=port)
