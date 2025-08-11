# app.py
# This is a Python Flask web application that serves your Slack status.
# To run this, you need to have Flask, requests, and python-dotenv installed:
# pip install Flask requests python-dotenv

import os
import requests
from flask import Flask, render_template
from dotenv import load_dotenv

# Load environment variables from the .env file.
# This must be called before trying to access any variables.
load_dotenv()

# --- Configuration ---
# Get your Slack API token from the .env file.
# The token needs the 'users.profile:read' scope.
SLACK_API_TOKEN = os.environ.get('SLACK_API_TOKEN')

# Get the Slack User ID from the .env file.
# This is the user whose status will be displayed.
SLACK_USER_ID = os.environ.get('SLACK_USER_ID')

# Note: Client Secret and Signing Secret are typically used for a full
# Slack app with events and interactivity. For simply reading a user's status,
# only the SLACK_API_TOKEN is required.
SLACK_CLIENT_SECRET = os.environ.get('SLACK_CLIENT_SECRET')
SLACK_SIGNING_SECRET = os.environ.get('SLACK_SIGNING_SECRET')


# You can change the port if you need to.
PORT = 5000

# --- App Setup ---
app = Flask(__name__)

# --- Functions ---

def get_slack_status():
    """
    Fetches the profile of the specified user from the Slack API.
    Returns a dictionary with status information or an error message.
    """
    # Check if necessary environment variables are set
    if not SLACK_API_TOKEN:
        return {
            'ok': False,
            'error': 'Slack API Token not found in environment variables.'
        }
    if not SLACK_USER_ID:
        return {
            'ok': False,
            'error': 'Slack User ID not found in environment variables.'
        }

    headers = {
        'Authorization': f'Bearer {SLACK_API_TOKEN}',
        'Content-type': 'application/json'
    }
    url = 'https://slack.com/api/users.profile.get'
    
    # Pass the user ID as a parameter to the API call
    params = {
        'user': SLACK_USER_ID
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
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
