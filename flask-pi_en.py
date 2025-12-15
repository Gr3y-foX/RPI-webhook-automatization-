from flask import Flask, request
import subprocess
import hmac
import hashlib
import os

app = Flask(__name__)

# IMPORTANT: Replace with your own values!

WEBHOOK_SECRET = "your_github_secret"

REPO_PATH = "/home/main/repo" # Your path

def verify_signature(payload, signature):

    """Verifies the signature from GitHub for security"""

    if not signature:

        print("вљ пёЏ Missing X-Hub-Signature-256 header")

        return False

    try:

        sha_name, signature = signature.split('=')

        if sha_name != 'sha256':

            print(f"Unsupported signature algorithm: {sha_name}")

            return False

    except ValueError:

        print(f"Invalid signature format: {signature}")

        return False

    if WEBHOOK_SECRET == "your_github_secret":

        print("WARNING: WEBHOOK_SECRET not set! Set the real secret from GitHub!")

    # Still verify, but with default value the signature won't pass

    mac = hmac.new(WEBHOOK_SECRET.encode(), msg=payload, digestmod=hashlib.sha256)

    return hmac.compare_digest(mac.hexdigest(), signature)

@app.route('/webhook', methods=['POST'])

def webhook():

    # Get event type from header

    event_type = request.headers.get('X-GitHub-Event')

    print(f"рџ“¬ Received event type: {event_type}")

    # Get signature from header

    signature = request.headers.get('X-Hub-Signature-256')

    # Save payload BEFORE verifying signature (to use request.json later)

    payload = request.data

    # Verify signature

    if not verify_signature(payload, signature):

        print("Invalid signature! Possible attack!")

        print(f" Received signature: {signature}")

        return 'Invalid signature', 403

    # Parse data from GitHub

    try:

        data = request.json

        if data is None:

            print(" ERROR: Failed to parse JSON from request")

            return 'Invalid JSON', 400

    except Exception as e:

        print(f" ERROR parsing JSON: {e}")

        return 'Invalid JSON', 400

    # Check if this is a push event

    if event_type != 'push':

        print(f" Ignoring event type '{event_type}' (expecting 'push')")

        return 'Event ignored', 200

    # Check for required fields

    if not data or 'ref' not in data:

        print(f"Missing 'ref' field in event data")

        print(f" Available fields: {list(data.keys()) if data else 'None'}")

        return 'Invalid push event', 400

    branch = data['ref'].split('/')[-1]

    repo_name = data.get('repository', {}).get('name', 'unknown')

    pusher = data.get('pusher', {}).get('name', 'unknown')

    print(f"вњ… Received push from {pusher} to repository {repo_name}, branch {branch}")

    # Check if directory exists

    if not os.path.exists(REPO_PATH):

        print(f" ERROR: Directory {REPO_PATH} does not exist!")

        return 'Repo path not found', 500

    if not os.path.exists(os.path.join(REPO_PATH, '.git')):

        print(f" ERROR: {REPO_PATH} is not a git repository!")

        return 'Not a git repo', 500

    # Execute git pull with detailed output

    try:

        print(f" Executing git pull in {REPO_PATH}...")

        print(f" Command: git pull origin {branch}")

        result = subprocess.run(

            ['git', 'pull', 'origin', branch],

            cwd=REPO_PATH,

            capture_output=True,

            text=True,

            timeout=30

        )

        # Output results

        if result.returncode == 0:

            print(f"рџ“Ґ Git pull executed successfully:")

            print(f" STDOUT: {result.stdout}")

            if result.stderr:

                print(f" STDERR: {result.stderr}")

            return 'OK - Pull successful', 200

        else:

            print(f"вќЊ Git pull finished with error (code {result.returncode}):")

            print(f" STDOUT: {result.stdout}")

            print(f" STDERR: {result.stderr}")

            return f'Git pull failed: {result.stderr}', 500

    except subprocess.TimeoutExpired:

        error_msg = "вЏ±пёЏ Timeout while executing git pull!"

        print(error_msg)

        return error_msg, 500

    except Exception as e:

        error_msg = f"вќЊ Error during git pull: {e}"

        print(error_msg)

        return error_msg, 500

@app.route('/', methods=['GET'])

def index():

    return 'Webhook server is running!', 200

if __name__ == '__main__':

    print(f" Starting webhook server...")

    print(f" Repository path: {REPO_PATH}")

    print(f" Webhook secret set: {'Yes' if WEBHOOK_SECRET != 'your_github_secret' else 'NO (SET IT!)'}")

    app.run(host='0.0.0.0', port=5000, debug=True)