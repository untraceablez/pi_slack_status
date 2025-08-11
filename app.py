# app.py
# This is a Python Flask web application that serves your Slack status.
# To run this, you need to have Flask, python-dotenv, slack_sdk, and emoji installed:
# pip install Flask python-dotenv slack_sdk emoji

import os
from flask import Flask, render_template
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import emoji

# Load environment variables from the .env file.
load_dotenv()

# --- Configuration ---
# Get your Slack API token from the .env file.
# The token needs the 'users.profile:read' scope.
SLACK_API_TOKEN = os.environ.get('SLACK_API_TOKEN')

# Get the Slack User ID from the .env file.
# This is the user whose status will be displayed.
SLACK_USER_ID = os.environ.get('SLACK_USER_ID')

# You can change the port if you need to.
PORT = 5000

# Global variable to cache custom emojis
custom_emojis = {}

# --- App Setup ---
app = Flask(__name__)

# Initialize the Slack WebClient with your token
# This is the primary way to interact with the Slack API using the SDK.
client = WebClient(token=SLACK_API_TOKEN)

# --- Functions ---

def get_custom_emojis():
    """
    Fetches and caches all custom emojis from the Slack workspace.
    """
    global custom_emojis
    try:
        response = client.emoji_list()
        if response['ok']:
            custom_emojis = response['emoji']
            print("Successfully fetched custom emojis.")
        else:
            print(f"Failed to fetch custom emojis: {response['error']}")
    except SlackApiError as e:
        print(f"Error fetching custom emojis: {e.response['error']}")
    except Exception as e:
        print(f"An unexpected error occurred while fetching emojis: {e}")

def get_slack_status():
    """
    Fetches the profile of the specified user from the Slack API using slack_sdk.
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
    
    try:
        # Call the users_profile_get API method with the specified user ID
        response = client.users_profile_get(user=SLACK_USER_ID)

        if response.get('ok'):
            profile = response.get('profile', {})
            status_text = profile.get('status_text', 'No status set')
            status_emoji = profile.get('status_emoji', '')
            
            # --- Emoji Handling Logic ---
            emoji_info = {'type': 'text', 'value': ''}
            if status_emoji:
                # Get the name of the emoji without the colons
                emoji_name = status_emoji.strip(':')

                # Check if the emoji is a custom one by looking it up in our cached list
                if emoji_name in custom_emojis:
                    emoji_info['type'] = 'url'
                    emoji_info['value'] = custom_emojis[emoji_name]
                else:
                    # It's a shortcode, so use the 'emoji' library to convert it.
                    converted_emoji = emoji.emojize(status_emoji)
                    emoji_info['value'] = converted_emoji
            # --- End of Emoji Handling ---

            return {
                'ok': True,
                'status_text': status_text,
                'status_emoji': emoji_info,
            }
        else:
            return {
                'ok': False,
                'error': response.get('error', 'Unknown Slack API error')
            }
    except SlackApiError as e:
        # Handle API-related errors
        return {
            'ok': False,
            'error': f'Slack API Error: {e.response["error"]}'
        }
    except Exception as e:
        # Handle other unexpected errors
        return {
            'ok': False,
            'error': f'An unexpected error occurred: {e}'
        }

# --- Routes ---

@app.route('/')
def home():
    """
    This is the main route. It fetches the Slack status and renders
    the HTML template to display it.
    """
    # Fetch custom emojis once when the app starts
    if not custom_emojis:
        get_custom_emojis()

    status_data = get_slack_status()

    if not status_data['ok']:
        return render_template('index.html', 
                               status_emoji_value='❌', 
                               status_emoji_type='text',
                               status_text=f"Error: {status_data['error']}",
                               is_error=True)

    return render_template('index.html',
                           status_emoji_value=status_data['status_emoji']['value'],
                           status_emoji_type=status_data['status_emoji']['type'],
                           status_text=status_data['status_text'],
                           is_error=False)


# --- Main Entry Point ---

if __name__ == '__main__':
    # Running this with debug=True is good for development.
    # When running as a daemon, you might want to set debug=False.
    print(f"Starting Slack Status app on http://127.0.0.1:{PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=True)
