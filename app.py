from flask import Flask, request, jsonify
from flask_cors import CORS
import hashlib
import time
import json

app = Flask(__name__)
CORS(app)

# --- BLOCKCHAIN LOGIC ---
class Blockchain:
    def __init__(self):
        self.chain = []
        self.pending_transactions = []
        # Genesis Block (Pahila Block)
        self.create_block(previous_hash='0', proof=100)

    def create_block(self, proof, previous_hash):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time.time(),
            'transactions': self.pending_transactions,
            'proof': proof,
            'previous_hash': previous_hash
        }
        self.pending_transactions = []
        self.chain.append(block)
        return block

    def last_block(self):
        return self.chain[-1]

    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()

    def add_transaction(self, voter_phone, candidate_id):
        self.pending_transactions.append({
            'voter_phone': voter_phone,
            'candidate_id': candidate_id
        })

    def has_voted(self, voter_phone):
        # Purna chain scan kara ki ya mobile number ne aadhi vote kelay ka
        for block in self.chain:
            for tx in block['transactions']:
                if tx.get('voter_phone') == voter_phone:
                    return True
        return False

blockchain = Blockchain()

# --- DATA STORAGE ---
voters = {} # Format: {username: {"password": p, "phone": ph}}
candidates = []

@app.route('/register_voter', methods=['POST'])
def register():
    data = request.json
    u, p, ph = data.get('username'), data.get('password'), data.get('phone')
    if u in voters:
        return jsonify({"error": "User exists"}), 400
    voters[u] = {"password": p, "phone": ph}
    return jsonify({"message": "Registered Successfully"}), 201

@app.route('/login_voter', methods=['POST'])
def login():
    data = request.json
    u, p = data.get('username'), data.get('password')
    user = voters.get(u)
    if user and user['password'] == p:
        return jsonify({"message": "Login success", "phone": user['phone']}), 200
    return jsonify({"error": "Invalid credentials"}), 401

@app.route('/register_candidate', methods=['POST'])
def add_candidate():
    data = request.json
    candidates.append({
        'id': len(candidates) + 1,
        'name': data.get('name'),
        'party': data.get('party'),
        'logo': data.get('logo'),
        'votes': 0
    })
    return jsonify({"message": "Candidate added"}), 201

@app.route('/get_data', methods=['GET'])
def get_data():
    return jsonify({
        "candidates": candidates,
        "chain_length": len(blockchain.chain),
        "hashes": [blockchain.hash(b) for b in blockchain.chain]
    })

@app.route('/send_otp', methods=['POST'])
def otp():

    mobile = request.form['mobile']

    otp = send_otp(mobile)

    session['otp'] = otp

    return "OTP Sent"

@app.route('/cast_vote', methods=['POST'])
def cast_vote():
    data = request.json
    phone = data.get('phone')
    c_id = data.get('id')

    # BLOCKCHAIN VALIDATION (One Voter One Vote)
    if blockchain.has_voted(phone):
        return jsonify({"error": "Already Voted! "}), 403

    blockchain.add_transaction(phone, c_id)
    prev_hash = blockchain.hash(blockchain.last_block())
    blockchain.create_block(proof=123, previous_hash=prev_hash)

    for c in candidates:
        if c['id'] == c_id:
            c['votes'] += 1
            break
    return jsonify({"message": "Vote secured in Blockchain"}), 200

import os # ही ओळ सर्वात वर नसेल तर ॲड करा

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)