import subprocess
import sys
import requests
import os

SERVICE_NAME = "reviewer"

def get_discord_secrets():
    secrets_path = os.path.join(os.path.dirname(__file__), "secrets.txt")
    with open(secrets_path, "r") as f:
        lines = [line.strip() for line in f if line.strip()]
        if len(lines) < 2:
            raise ValueError("secrets.txt must contain bot token and user id on separate lines")
        return lines[0], lines[1]

DISCORD_BOT_TOKEN, DISCORD_USER_ID = get_discord_secrets()

def git_pull():
    result = subprocess.run(["git", "pull"], capture_output=True, text=True)
    print(result.stdout)
    print(result.stderr, file=sys.stderr)
    return result.stdout, result.stderr

def restart_service():
    result = subprocess.run(["systemctl", "restart", SERVICE_NAME], capture_output=True, text=True)
    print(result.stdout)
    print(result.stderr, file=sys.stderr)
    return result.returncode

def send_discord_dm(message):
    url = "https://discord.com/api/v10/users/@me/channels"
    headers = {
        "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    # Create DM channel
    payload = {"recipient_id": DISCORD_USER_ID}
    resp = requests.post(url, headers=headers, json=payload)
    if resp.status_code == 200:
        channel_id = resp.json()["id"]
        # Send message
        msg_url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
        msg_payload = {"content": message}
        msg_resp = requests.post(msg_url, headers=headers, json=msg_payload)
        if msg_resp.status_code == 200:
            print("Discord DM sent successfully.")
        else:
            print(f"Failed to send Discord DM: {msg_resp.text}", file=sys.stderr)
    else:
        print(f"Failed to create DM channel: {resp.text}", file=sys.stderr)

if __name__ == "__main__":
    stdout, stderr = git_pull()
    if "Already up to date." not in stdout:
        print("Updates detected. Restarting service...")
        rc = restart_service()
        if rc == 0:
            print(f"Service '{SERVICE_NAME}' restarted successfully.")
            send_discord_dm("Reviewer codebase was updated and the service was restarted.")
        else:
            print(f"Failed to restart service '{SERVICE_NAME}'.", file=sys.stderr)
    else:
        print("No updates detected. Service not restarted.")
