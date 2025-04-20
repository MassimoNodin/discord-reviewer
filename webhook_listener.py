import hmac
import hashlib
import subprocess
import os
import logging
from flask import Flask, request, abort

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration ---
# Get the absolute path of the script's directory
APP_DIR = os.path.dirname(os.path.abspath(__file__))
# Path to the secrets file (assuming it's in the same directory)
SECRETS_FILE = os.path.join(APP_DIR, 'secrets.txt')
# Expected Git branch for updates
GIT_BRANCH = 'refs/heads/main' # Or 'refs/heads/master' depending on your default branch
# Name of the main bot service to restart
BOT_SERVICE_NAME = 'reviewer.service' # Ensure this matches your actual service name
# --- End Configuration ---

app = Flask(__name__)

def load_webhook_secret():
    """Loads the webhook secret from secrets.txt"""
    try:
        with open(SECRETS_FILE, 'r') as f:
            for line in f:
                if line.startswith('WEBHOOK_SECRET='):
                    return line.strip().split('=', 1)[1]
    except FileNotFoundError:
        logging.error(f"Secrets file not found at {SECRETS_FILE}")
    except Exception as e:
        logging.error(f"Error reading secrets file: {e}")
    return None

WEBHOOK_SECRET = load_webhook_secret()
if not WEBHOOK_SECRET:
    logging.error("WEBHOOK_SECRET not found in secrets.txt. Webhook verification will fail.")
    # You might want to exit or handle this more gracefully depending on requirements
    # exit(1) # Uncomment to force exit if secret is missing

def verify_signature(payload_body, secret_token, signature_header):
    """Verify that the payload was sent from GitHub by validating SHA256 signature."""
    if not signature_header:
        logging.warning("X-Hub-Signature-256 header is missing!")
        return False
    if not secret_token:
        logging.error("Webhook secret is not configured.")
        return False

    hash_object = hmac.new(secret_token.encode('utf-8'), msg=payload_body, digestmod=hashlib.sha256)
    expected_signature = "sha256=" + hash_object.hexdigest()
    if not hmac.compare_digest(expected_signature, signature_header):
        logging.warning("Request signature mismatch!")
        return False
    return True

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handles incoming GitHub webhook requests."""
    logging.info("Webhook received.")

    # Get signature from header
    signature = request.headers.get('X-Hub-Signature-256')
    # Get event type
    event = request.headers.get('X-GitHub-Event')
    # Get payload
    data = request.get_data()

    # Verify signature
    if not verify_signature(data, WEBHOOK_SECRET, signature):
        abort(403) # Forbidden

    # Check if it's a push event
    if event == 'push':
        payload = request.get_json()
        # Check if the push was to the configured branch
        if payload.get('ref') == GIT_BRANCH:
            logging.info(f"Push event received for branch {GIT_BRANCH}. Triggering update and restart.")
            try:
                # 1. Pull latest changes
                logging.info("Running git pull...")
                git_pull_cmd = ['/usr/bin/git', 'pull']
                pull_result = subprocess.run(git_pull_cmd, cwd=APP_DIR, capture_output=True, text=True, check=True)
                logging.info(f"Git pull successful:\n{pull_result.stdout}")

                # 2. Restart the bot service using systemctl
                # IMPORTANT: Requires passwordless sudo for this specific command!
                logging.info(f"Restarting service: {BOT_SERVICE_NAME}...")
                restart_cmd = ['/usr/bin/sudo', '/usr/bin/systemctl', 'restart', BOT_SERVICE_NAME]
                restart_result = subprocess.run(restart_cmd, capture_output=True, text=True, check=True)
                logging.info(f"Service restart command executed. Output:\n{restart_result.stdout or '<no output>'}")
                if restart_result.stderr:
                     logging.warning(f"Service restart command stderr:\n{restart_result.stderr}")

            except subprocess.CalledProcessError as e:
                logging.error(f"Command failed: {' '.join(e.cmd)}\nStderr:\n{e.stderr}\nStdout:\n{e.stdout}")
            except FileNotFoundError as e:
                 logging.error(f"Command not found: {e}. Ensure git and systemctl paths are correct and user has permissions.")
            except Exception as e:
                logging.error(f"An error occurred during update/restart: {e}")
        else:
            logging.info(f"Push event received for branch {payload.get('ref')}, ignoring.")

    elif event == 'ping':
        logging.info("GitHub ping event received.")
    else:
        logging.info(f"Received unhandled event type: {event}")

    return 'OK', 200

if __name__ == '__main__':
    # Make sure to run this with a production server like gunicorn behind Nginx
    # For development/testing: app.run(host='0.0.0.0', port=5000)
    # For production with gunicorn: gunicorn --bind 127.0.0.1:5000 webhook_listener:app
    # The systemd service will handle running gunicorn.
    logging.info("Starting Flask webhook listener.")
    # This basic run is okay if systemd manages it, but gunicorn is preferred.
    # The systemd file will be updated to use gunicorn.
    app.run(host='127.0.0.1', port=5000) # Listen only locally, Nginx handles external access
