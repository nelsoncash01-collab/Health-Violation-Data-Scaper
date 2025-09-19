#!/usr/bin/env python3
"""
Minimal test version of app for debugging Render deployment
"""

from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def health_check():
    return jsonify({
        "status": "ok",
        "message": "Minimal test app is running",
        "version": "1.0"
    })

@app.route('/api/test')
def test_endpoint():
    return jsonify({
        "success": True,
        "message": "Test endpoint working",
        "data": {"test": "value"}
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)