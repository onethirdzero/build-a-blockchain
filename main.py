# Based on https://hackernoon.com/learn-blockchains-by-building-one-117428612f46

import hashlib
import json

from time import time
from uuid import uuid4

from flask import Flask, jsonify, request


class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []

        # Creates the genesis block.
        self.new_block(previous_hash=1, proof=100)

    def new_block(self, proof, previous_hash):
        """
        Creates a new Block.

        :param proof: <int> The proof given by the Proof of Work algorithm
        :param previous_hash: (Optional) <str> Hash of the previous Block
        :return: <dict> New Block
        """

        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1])
        }

        # Reset the current list of transactions.
        self.current_transactions = []

        # Add append this Block to the chain.
        self.chain.append(block)

        return block

    def new_transaction(self, sender, recipient, amount):
        """
        Creates a new transaction that goes into the next Block.

        :param sender: <str> Address of the Sender
        :param recipient: <str> Address of the Recipient
        :param amount: <int> Amount sent
        :return: <int> The index of the block that will hold this transaction
        """

        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount
        })

        return self.last_block['index'] + 1

    @property
    def last_block(self):
        return self.chain[-1]

    @staticmethod
    def hash(block):
        """
        Creates a SHA-256 hash of a Block.

        :param block: <dict> Block
        :return: <str> Hash of the Block
        """

        # The dictionary needs to be sorted, otherwise the hashes will be inconsistent
        encoded_block_string = json.dumps(block, sort_keys=True).encode()

        # Create a hash object, then generate a hash for it.
        return hashlib.sha256(encoded_block_string).hexdigest()

    def proof_of_work(self, last_proof):
        """
        A simple Proof of Work algorithm:
          - Find a number p' such that hash(pp') contains 4 leading zeroes, where p is the previous p'
          - p is the previous proof, and p' is the new proof

          :param last_proof: <int>
          :return: <int> The new proof
        """

        proof = 0

        while self.valid_proof(last_proof, proof) is False:
            proof += 1

        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        """
        Validates the proof - ie. does hash(last_proof, proof) contain 4 leading zeroes?

        :param last_proof: <int>
        :param proof: <int>
        :return: <bool> True if correct, False otherwise
        """

        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == '0000'

# Instantiate our Node.
app = Flask(__name__)

# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')

# Instantiate Blockchain.
blockchain = Blockchain()

@app.route('/mine', methods=['GET'])
def mine():
    return 'New Block mined'

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    request_body = request.get_json(force=True)

    print(request_body)

    # Check that required fields are present.
    required = ['sender', 'recipient', 'amount']
    if not all(k in request_body for k in required):
        return 'Missing values', 400

    index = blockchain.new_transaction(
        request_body['sender'],
        request_body['recipient'],
        request_body['amount']
    )

    response = {
        'message': f'Transaction will be added to Block {index}'
    }

    return jsonify(response), 201

@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }

    return jsonify(response), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
