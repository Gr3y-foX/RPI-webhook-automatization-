## Installing Flask Script for Automatic `git pull` via GitHub Webhook on Raspberry Pi using ngrok (port 5000)

This file describes how to deploy the `flask-pi.py` script on Raspberry Pi, configure GitHub Webhook, and use ngrok as a "bridge" to the local Flask server on port 5000.

---

### 1. Prerequisites

- **Raspberry Pi** with installed **Raspberry Pi OS / other Linux-like system**.
- **SSH** access or physical terminal access.
- Installed **Git**.
- Installed **Python 3** (usually available by default).
- GitHub account and **repository** that needs to be automatically updated (`git pull`).
- Installed **ngrok** or readiness to install it (see section below).

---

### 2. Preparing Git Repository on Raspberry Pi

1. Navigate to the directory where you want to keep your code:

```bash
cd /home/pi
```

2. Clone the repository that should be updated by `git pull`:

```bash
git clone https://github.com/USERNAME/REPO_NAME.git
```

3. Remember the path to the repository (you'll need it in `flask-pi.py`), for example:

```bash
REPO_PATH="/home/pi/REPO_NAME"
```

4. Make sure everything works:

```bash
cd "$REPO_PATH"
git status
```

---

### 3. Installing Python Dependencies (Flask)

1. Update packages:

```bash
sudo apt update
```

2. Install `pip` and Flask (if not already installed):

```bash
sudo apt install -y python3-pip python3-venv
python3 -m venv venv
source venv/bin/activate
pip install flask
```

If desired, you can use a virtual environment, but for simplicity, everything is installed globally here.

---

### 4. Configuring the `flask-pi.py` Script

1. Copy the `flask-pi.py` file to a separate directory, for example:

```bash
mkdir -p /home/pi/webhook-server
cp /Users/phenix/Downloads/111/flask-pi.py /home/pi/webhook-server/
cd /home/pi/webhook-server
```

> **Important:** Adjust the path in the `cp` command to your actual path if you're copying not from macOS but already on Raspberry Pi itself.

2. Open the `flask-pi.py` file for editing:

```bash
nano flask-pi.py
```

3. Change two important variables at the beginning of the file:

- **`WEBHOOK_SECRET`**  secret key that you will set in GitHub Webhook settings.
- **`REPO_PATH`**  path to your cloned repository on Raspberry Pi.

For example:

```python
WEBHOOK_SECRET = "my_super_secret_token"
REPO_PATH = "/home/pi/REPO_NAME"
```

4. Save changes and exit the editor (`Ctrl+O`, `Enter`, then `Ctrl+X` in nano).

---

### 5. Test Run of Flask Server (port 5000)

1. In the `webhook-server` directory, execute:

```bash
cd /home/pi/webhook-server
python3 flask-pi.py
```

2. In the logs, you should see that the server is running on `0.0.0.0:5000`.

3. Local check (optional, if you have a browser or curl):

```bash
curl http://localhost:5000/
```

Expected response: `Webhook server is running!`.

Leave this process running for now (or later configure systemd/screen/tmux for autostart).

---

### 6. Installing and Configuring ngrok (port 5000)

#### 6.1. Installing ngrok on Raspberry Pi

1. Go to the ngrok website (on any PC) and register:

- Open your browser and go to `https://ngrok.com`.
- Create an account and copy your **Auth Token**.

2. Download ngrok on Raspberry Pi:

```bash
cd /home/pi
wget https://bin.equinox.io/c/4VmDzA7iaHb/ngrok-stable-linux-arm.zip
unzip ngrok-stable-linux-arm.zip
sudo mv ngrok /usr/local/bin/
rm ngrok-stable-linux-arm.zip
```

> If the URL is outdated вАУ get the current ARM binary from ngrok website and substitute it in the `wget` command.

3. Connect your Auth Token:

```bash
ngrok config add-authtoken YOUR_AUTH_TOKEN_HERE
```

---

#### 6.2. Running ngrok on port 5000

1. Make sure the Flask server is still listening on port 5000 on Raspberry Pi.
2. In a **new terminal/session** on Raspberry Pi, execute:

```bash
ngrok http 5000
```

3. In ngrok output, you'll see something like:

```text
Forwarding  https://abcd-1234-5678.eu.ngrok.io -> http://localhost:5000
```

4. Copy the **https-URL** (e.g., `https://abcd-1234-5678.eu.ngrok.io`) вАУ you'll need it for GitHub Webhook.

> **Important:** Each time you restart ngrok, the URL changes if you don't use a paid static domain. After restarting ngrok, don't forget to update the URL in Webhook settings on GitHub.

---

### 7. Configuring GitHub Webhook

1. Go to your repository on GitHub.
2. Open:

- **Settings** вЖТ **Webhooks** вЖТ **Add webhook**.

3. Fill in the fields:

- **Payload URL**:  
  `https://YOUR_NGROK_ADDRESS/webhook`  
  For example:  
  `https://abcd-1234-5678.eu.ngrok.io/webhook`

- **Content type**:  
  `application/json`

- **Secret**:  
  The same secret you recorded in `WEBHOOK_SECRET` in `flask-pi.py` (e.g., `my_super_secret_token`).

- **Which events would you like to trigger this webhook?**  
  Select **"Just the push event"**.

4. Click **Add webhook**.

5. GitHub will send a test `ping`/`push` request. In the Flask logs on Raspberry Pi, you'll see corresponding messages. If the signature or JSON is invalid вАУ check the console output (the script prints them).

---

### 8. Checking Functionality: Automatic `git pull`

1. Make changes to the repository (on GitHub or locally with subsequent `git push` to the required branch, usually `main` or `master`).
2. Do `git push` on GitHub.
3. On Raspberry Pi in the terminal where `flask-pi.py` is running, you should see:

- Log message about received `push` event.
- Command `git pull origin <branch>`.
- Result of `git pull` execution.

4. Check that the local repository was actually updated:

```bash
cd /home/pi/REPO_NAME
git log -1
```

---

### 9. Autostart (optional)

To avoid manually running Flask and ngrok after each Raspberry Pi restart, you can:

- Use **`tmux` or `screen`** and keep processes in them.
- Create **systemd services**:
  - one for `python3 /home/pi/webhook-server/flask-pi.py`
  - second for `ngrok http 5000`

This is beyond the scope of this basic manual, but the general idea is to set up both processes as services that start when the system boots.

---

### 10. Running in Background as a Daemon (systemd)

Below is an example of how to run the **Flask server** and **ngrok** as systemd services so that they automatically start on Raspberry Pi boot.

> **Important:** adjust paths and user (`pi`) to your system if you use a different user or directories.

#### 10.1. Daemon for Flask (`flask-pi.py`)

We assume that:

- project is in `/home/pi/webhook-server`
- virtual environment: `/home/pi/webhook-server/venv`
- script: `/home/pi/webhook-server/flask-pi.py`

1. Create a unit file:

```bash
sudo nano /etc/systemd/system/webhook-flask.service
```

2. Insert the following content:

```ini
[Unit]
Description=GitHub webhook Flask server
After=network.target

[Service]
User=pi
WorkingDirectory=/home/pi/webhook-server
Environment="PATH=/home/pi/webhook-server/venv/bin"
ExecStart=/home/pi/webhook-server/venv/bin/python flask-pi.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

3. Reload systemd configuration and enable the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable webhook-flask.service
sudo systemctl start webhook-flask.service
```

4. Check the status:

```bash
sudo systemctl status webhook-flask.service
```

Logs can be viewed using:

```bash
journalctl -u webhook-flask.service -f
```

---

#### 10.2. Daemon for ngrok (port 5000)

1. Create a unit file:

```bash
sudo nano /etc/systemd/system/ngrok-http-5000.service
```

2. Insert the following content:

```ini
[Unit]
Description=ngrok tunnel for Flask webhook (port 5000)
After=network-online.target
Wants=network-online.target

[Service]
User=pi
ExecStart=/usr/local/bin/ngrok http 5000
Restart=always
RestartSec=5
Environment=NGROK_CONFIG=/home/pi/.config/ngrok/ngrok.yml

[Install]
WantedBy=multi-user.target
```

Make sure that:

- `ngrok` binary is actually located at `/usr/local/bin/ngrok`
- ngrok config with your `authtoken` is stored at `/home/pi/.config/ngrok/ngrok.yml`

3. Reload systemd configuration and enable the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable ngrok-http-5000.service
sudo systemctl start ngrok-http-5000.service
```

4. Check the status:

```bash
sudo systemctl status ngrok-http-5000.service
```

Logs:

```bash
journalctl -u ngrok-http-5000.service -f
```

> **Reminder:** if you have a free ngrok account, the URL will change on each new tunnel start/restart, even via systemd. Don't forget to update the address in GitHub Webhook when it changes.

---

### 11. Quick Summary

- **Flask server** (`flask-pi.py`) listens on `0.0.0.0:5000` and handles `POST /webhook`.
- **ngrok** forwards a public `https` address to `http://localhost:5000`.
- **GitHub Webhook** sends `push` events to `https://YOUR_NGROK_ADDRESS/webhook` with a secret.
- The script verifies the signature, analyzes the `push`, and executes `git pull` in the specified repository directory.
