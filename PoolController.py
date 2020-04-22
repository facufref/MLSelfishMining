from argparse import ArgumentParser
from flask import Flask, jsonify, request
from Pool import Pool
from GeneralSettings import host_address, blockchain_port
import requests

# Instantiate our Node
app = Flask(__name__)

# Instantiate the Pool
pool = Pool()


@app.route('/pool/register', methods=['POST'])
def register_member():
    values = request.get_json()

    address = values.get('address')
    uuid = values.get('uuid')

    if address is None or uuid is None:
        return "Error: Please supply a valid Address and UUID", 400

    pool.register_member(address, uuid)

    response = {
        'message': 'New member have been added',
        'members': list(pool.members),
    }
    return jsonify(response), 201


@app.route('/pool/unregister', methods=['POST'])
def unregister_member():
    values = request.get_json()

    node = values.get('address')
    if node is None:
        return "Error: Please supply a valid node", 400

    pool.unregister_member(node)

    response = {
        'message': 'The node has been removed',
        'members': list(pool.members),
    }
    return jsonify(response), 201


@app.route('/pool/members', methods=['GET'])
def get_members():
    response = {
        'message': 'Returning existing members',
        'members': list(pool.members)
    }
    return jsonify(response), 200


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': pool.chain,
        'length': len(pool.chain),
    }
    return jsonify(response), 200


@app.route('/pool/update_chain', methods=['POST'])
def update_chain():
    values = request.get_json()

    chain = values.get('chain')
    sender = values.get('sender')

    if chain is None:
        return "Error: Please supply a valid chain", 400

    if pool.update_chain(chain, sender):
        message = 'Chain has been updated'
    else:
        message = 'The chain was authoritative'

    response = {'message': message,
                'chain': pool.chain}

    return jsonify(response), 201


@app.route('/wallet', methods=['GET'])
def get_member_wallets():
    wallets = pool.get_all_wallets()
    response = {
        'message': 'Returning existing wallets',
        'wallets': wallets
    }
    return jsonify(response), 200


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=6001, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    #  On start, register the Pool on the blockchain
    requests.post(f'http://{host_address}{blockchain_port}/nodes/register', json={'nodes': [f"{host_address}{port}"]})

    app.run(host='0.0.0.0', port=port)
