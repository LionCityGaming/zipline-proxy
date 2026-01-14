from flask import Flask, jsonify
import requests
import os
import logging
import time

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Zipline configuration from environment variables
ZIPLINE_URL = os.environ.get('ZIPLINE_URL', 'http://zipline:3000')
ZIPLINE_USERNAME = os.environ.get('ZIPLINE_USERNAME')
ZIPLINE_PASSWORD = os.environ.get('ZIPLINE_PASSWORD')
CACHE_TIMEOUT = int(os.environ.get('CACHE_TIMEOUT', 300))  # 5 minutes default

# Session cache
_session_cache = {
    'cookies': None,
    'last_login': 0,
    'stats': None,
    'last_fetch': 0
}

def login_to_zipline():
    """Login to Zipline and get session cookies"""
    try:
        response = requests.post(
            f'{ZIPLINE_URL}/api/auth/login',
            json={
                'username': ZIPLINE_USERNAME,
                'password': ZIPLINE_PASSWORD
            },
            timeout=10
        )
        response.raise_for_status()

        _session_cache['cookies'] = response.cookies
        _session_cache['last_login'] = time.time()

        logger.info("Successfully logged in to Zipline")
        return response.cookies
    except requests.exceptions.RequestException as e:
        logger.error(f"Error logging in to Zipline: {e}")
        raise

def get_zipline_stats():
    """Fetch statistics from Zipline API"""
    # Check cache first
    now = time.time()
    if (_session_cache['stats'] and
        now - _session_cache['last_fetch'] < CACHE_TIMEOUT):
        logger.info("Returning cached stats")
        return _session_cache['stats']

    # Get session cookies (login if needed)
    cookies = _session_cache['cookies']
    if not cookies or now - _session_cache['last_login'] > 3600:  # Re-login every hour
        cookies = login_to_zipline()

    try:
        response = requests.get(
            f'{ZIPLINE_URL}/api/user/stats',
            cookies=cookies,
            timeout=10
        )

        # If unauthorized, try logging in again
        if response.status_code == 401:
            logger.info("Session expired, logging in again")
            cookies = login_to_zipline()
            response = requests.get(
                f'{ZIPLINE_URL}/api/user/stats',
                cookies=cookies,
                timeout=10
            )

        response.raise_for_status()
        data = response.json()

        # Parse Zipline stats response
        # Expected format: {"filesUploaded": 219, "storageUsed": 210716487, ...}
        files = data.get('filesUploaded', 0)
        storage_bytes = data.get('storageUsed', 0)
        storage_gb = storage_bytes / (1024 ** 3)  # Convert bytes to GB

        result = {
            'files': files,
            'storage_gb': round(storage_gb, 2)
        }

        # Update cache
        _session_cache['stats'] = result
        _session_cache['last_fetch'] = now

        logger.info(f"Fetched stats: {result}")
        return result

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching Zipline stats: {e}")
        raise

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return 'OK', 200

@app.route('/stats', methods=['GET'])
def stats():
    """Get Zipline statistics"""
    try:
        if not ZIPLINE_USERNAME or not ZIPLINE_PASSWORD:
            return jsonify({
                'error': 'ZIPLINE_USERNAME and ZIPLINE_PASSWORD environment variables are required'
            }), 500

        stats_data = get_zipline_stats()
        return jsonify(stats_data), 200
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching Zipline stats: {e}")
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
