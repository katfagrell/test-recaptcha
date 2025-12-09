# app.py (Cloud Run Python Flask Application)
import requests
import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS # Used to handle all CORS headers automatically

# --- Flask Initialization ---
app = Flask(__name__)
# 1. Initialize CORS on the app instance
# This ensures Access-Control-Allow-Origin headers are automatically added to ALL responses.
CORS(app) 

# The verification URL for Google reCAPTCHA
VERIFY_URL = 'https://www.google.com/recaptcha/api/siteverify'
# Get SECRET KEY securely from environment variable
RECAPTCHA_SECRET_KEY = os.environ.get('RECAPTCHA_SECRET_KEY')
# --- End Setup ---

# 2. Define the route decorator for POST requests
@app.route('/verify-recaptcha', methods=['POST'])
def verify_recaptcha():
    """
    Handles the asynchronous POST request from the client and verifies the reCAPTCHA token.
    """
    
    # Flask-CORS handles the OPTIONS preflight request automatically,
    # so we can remove the manual check: 'if request.method == "OPTIONS":'

    # 3. Check server configuration first (Secret Key)
    if not RECAPTCHA_SECRET_KEY:
        # Flask returns the JSON and status code directly
        return jsonify({'success': False, 'message': 'Server misconfigured (Secret Key missing)'}), 500

    try:
        # 4. Get the data sent from the client's fetch call
        request_json = request.get_json(silent=True)
        
        if not request_json:
            return jsonify({'success': False, 'message': 'Invalid request format'}), 400
            
        userResponseToken = request_json.get('g-recaptcha-response')

        if not userResponseToken:
            return jsonify({'success': False, 'message': 'reCAPTCHA token is missing.'}), 400

        # 5. Prepare and send the server-to-server POST request to Google
        verification_data = {
            'secret': RECAPTCHA_SECRET_KEY,
            'response': userResponseToken
        }
        
        google_response = requests.post(VERIFY_URL, data=verification_data)
        
        # 6. Check the verification result
        verification_result = google_response.json()

        if verification_result.get('success'):
            # ✅ SUCCESS
            return jsonify({'success': True, 'message': 'Form submitted and verified!'}), 200
        else:
            # ❌ FAILURE
            return jsonify({
                'success': False, 
                'message': 'reCAPTCHA challenge failed. Please try again.',
                'errors': verification_result.get('error-codes')
            }), 403

    except Exception as e:
        app.logger.error(f"Error during verification: {e}")
        return jsonify({'success': False, 'message': 'Verification service error.'}), 500

# --- Gunicorn Entry Point (Required by Cloud Run) ---
if __name__ == '__main__':
    # Cloud Run injects the PORT environment variable.
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)