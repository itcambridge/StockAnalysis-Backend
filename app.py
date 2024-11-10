from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
import os
import time
import random
import json
import requests
from openai import OpenAI
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
from firebase_admin import auth

# Load environment variables
load_dotenv()

# Create Flask app
app = Flask(__name__)

# Initialize Firebase
try:
    firebase_config = json.loads(os.getenv('FIREBASE_CONFIG'))
    # Fix private key formatting
    if isinstance(firebase_config, dict):
        private_key = firebase_config.get('private_key')
        if private_key:
            private_key = private_key.replace('\\n', '\n')
            firebase_config['private_key'] = private_key

    if not firebase_admin._apps:
        cred = credentials.Certificate(firebase_config)
        firebase_admin.initialize_app(cred)
        print("Firebase initialized successfully")
    else:
        print("Firebase already initialized")
except Exception as e:
    print(f"Firebase initialization error: {str(e)}")

# Setup CORS
CORS(app, resources={r"/*": {"origins": [
    "https://replit.com",
    "https://*.repl.co",
    "https://*.replit.dev",
    "http://172.236.2.126",
    "http://localhost:3001"
]}},
supports_credentials=True,
allow_headers=["Content-Type", "Authorization", "Accept"],
methods=["GET", "POST", "OPTIONS"])

# Routes
@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "status": "running",
        "message": "Backend is up and running"
    })

@app.route('/test', methods=['GET'])
def test():
    return jsonify({
        "message": "CORS test successful",
        "environment": {
            "OPENAI_API_KEY": "Present" if os.getenv("OPENAI_API_KEY") else "Missing",
            "ALPHA_VANTAGE_API_KEY": "Present" if os.getenv("ALPHA_VANTAGE_API_KEY") else "Missing",
            "FIREBASE_CONFIG": "Present" if os.getenv("FIREBASE_CONFIG") else "Missing"
        }
    })

@app.route('/test/firebase', methods=['GET'])
def test_firebase():
    try:
        db = firestore.client()
        collections = [col.id for col in db.collections()]
        return jsonify({
            "message": "Firebase connection successful",
            "project_id": firebase_admin.get_app().project_id,
            "collections": collections
        })
    except Exception as e:
        return jsonify({
            "error": "Firebase connection failed",
            "message": str(e),
            "type": str(type(e))
        }), 500

@app.route('/test/openai', methods=['GET'])
def test_openai():
    try:
        client = OpenAI()
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello!"}],
            max_tokens=10
        )
        return jsonify({
            "message": "OpenAI connection successful",
            "response": response.choices[0].message.content
        })
    except Exception as e:
        return jsonify({
            "error": "OpenAI connection failed",
            "message": str(e)
        }), 500

@app.route('/api/interest-rates', methods=['GET'])
def get_interest_rates():
    try:
        data = {
            'fedFundsRate': 5.33,
            'tenYearYield': 4.25,
            'twoYearYield': 4.89,
            'defaultRate': 2.1
        }
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": "Failed to get interest rates"}), 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)