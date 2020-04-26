from argparse import ArgumentParser
from flask import Flask, jsonify, request
from SelfishMiningDetector import SelfishMiningDetector
import requests
from GeneralSettings import host_address, blockchain_port

# Instantiate our Node
app = Flask(__name__)

# Instantiate the Miner
detector = SelfishMiningDetector()


@app.route('/detect', methods=['GET'])
def detect():
    message = detector.is_selfish()

    response = {
        'message': message
    }

    return jsonify(response), 200


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=7001, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port
    detector.node = f"{host_address}{port}"
    app.run(host='0.0.0.0', port=port)
