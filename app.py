# app.py
# This is a Python Flask web application that serves your Slack status.
# To run this, you need to have Flask and requests installed:
# pip install Flask requests

import os
import requests
from flask import Flask, render_template

# --- Configuration ---
# You MUST replace 'YOUR_SLACK_API_TOKEN' with your actual Slack API token.
# You can get this from https://api.slack.com/apps/ and create a new app.
# The token needs the 'users.profile:read' scope.
# Note: It's a good practice to store this in an environment variable, but for simplicity,
# we are hardcoding it here.
SLACK_API_TOKEN = os.environ.get('SLACK_API_TOKEN', 'YOUR_SLACK_API_TOKEN')

# You can change the port if you need to.
PORT = 5000

# --- App Setup ---
app = Flask(__name__)

# --- Functions ---

def get_slack_status():
    """
    Fetches the current user's profile from the Slack API.
    Returns a dictionary with status information or an error message.
    """
    headers = {
        'Authorization': f'Bearer {SLACK_API_TOKEN}',
        'Content-type': 'application/json'
    }
    url = 'https://slack.com/api/users.profile.get'
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
        data = response.json()

        if data.get('ok'):
            profile = data.get('profile', {})
            status_text = profile.get('status_text', 'No status set')
            status_emoji = profile.get('status_emoji', '')
            
            # Remove the emoji colons for a cleaner display
            if status_emoji.startswith(':') and status_emoji.endswith(':'):
                status_emoji = status_emoji[1:-1]

            return {
                'ok': True,
                'status_text': status_text,
                'status_emoji': status_emoji,
            }
        else:
            return {
                'ok': False,
                'error': data.get('error', 'Unknown Slack API error')
            }
    except requests.exceptions.RequestException as e:
        # Handle network-related errors
        return {
            'ok': False,
            'error': f'Network Error: {e}'
        }

# --- Routes ---

@app.route('/')
def home():
    """
    This is the main route. It fetches the Slack status and renders
    the HTML template to display it.
    """
    status_data = get_slack_status()

    if not status_data['ok']:
        return render_template('index.html', 
                               status_emoji='❌', 
                               status_text=f"Error: {status_data['error']}",
                               is_error=True)

    return render_template('index.html',
                           status_emoji=status_data['status_emoji'],
                           status_text=status_data['status_text'],
                           is_error=False)


# --- Main Entry Point ---

if __name__ == '__main__':
    # Running this with debug=True is good for development.
    # When running as a daemon, you might want to set debug=False.
    print(f"Starting Slack Status app on http://127.0.0.1:{PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=True)
