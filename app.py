# app.py
# Flask web app that displays a user's Slack status and Last.fm now-playing track.
# Required packages: see requirements.txt

import os
import threading
import time
import requests
from flask import Flask, render_template, jsonify
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import emoji

load_dotenv(os.path.expanduser('~/.env'))

# --- Configuration ---
SLACK_API_TOKEN = os.environ.get('SLACK_API_TOKEN')
SLACK_USER_ID   = os.environ.get('SLACK_USER_ID')
LASTFM_API_KEY  = os.environ.get('LAST_FM_API_KEY')
LASTFM_USERNAME = os.environ.get('LAST_FM_USERNAME')

PORT         = 5000
POLL_INTERVAL = 30  # seconds between Last.fm polls

# --- Global State ---
custom_emojis = {}

current_track = {
    'title':     None,
    'artist':    None,
    'album':     None,
    'cover_art': None,
    'last_checked': 0,
}
music_lock = threading.Lock()

# --- App Setup ---
app    = Flask(__name__)
client = WebClient(token=SLACK_API_TOKEN)

# --- Last.fm ---

def get_lastfm_now_playing():
    """
    Fetches the currently playing track from Last.fm.
    Returns (title, artist, cover_art) or (None, None, None) if nothing is playing.
    """
    if not LASTFM_API_KEY or not LASTFM_USERNAME:
        print("Last.fm API key or username not configured.")
        return None, None, None

    try:
        resp = requests.get(
            'https://ws.audioscrobbler.com/2.0/',
            params={
                'method':  'user.getrecenttracks',
                'user':    LASTFM_USERNAME,
                'api_key': LASTFM_API_KEY,
                'format':  'json',
                'limit':   1,
            },
            timeout=10,
        )
        resp.raise_for_status()
        data   = resp.json()
        tracks = data.get('recenttracks', {}).get('track', [])

        if not tracks:
            return None, None, None

        track = tracks[0]

        # Use the nowplaying track if present (some clients send this),
        # otherwise fall back to the most recently scrobbled track.
        # Qobuz only scrobbles after a track finishes, so nowplaying is rarely set.

        title  = track.get('name')
        artist = track.get('artist', {}).get('#text')
        album  = track.get('album', {}).get('#text') or None

        # Pick the largest available image, skipping Last.fm's blank placeholder
        cover_art = None
        for img in reversed(track.get('image', [])):
            url = img.get('#text', '').strip()
            if url and '2a96cbd8b46e442fc41c2b86b821562f' not in url:
                cover_art = url
                break

        return title, artist, album, cover_art

    except Exception as e:
        print(f"Last.fm error: {e}")
        return None, None, None, None


def lastfm_poll_loop():
    """Background thread: polls Last.fm every POLL_INTERVAL seconds."""
    global current_track
    while True:
        with music_lock:
            last_checked = current_track['last_checked']

        if time.time() - last_checked >= POLL_INTERVAL:
            title, artist, album, cover_art = get_lastfm_now_playing()
            with music_lock:
                if title:
                    current_track['title']     = title
                    current_track['artist']    = artist
                    current_track['album']     = album
                    current_track['cover_art'] = cover_art
                current_track['last_checked'] = time.time()
            print(f"Now playing: {artist} - {title}" if title else "Nothing playing.")

        time.sleep(5)


_poll_thread = threading.Thread(target=lastfm_poll_loop, daemon=True)
_poll_thread.start()

# --- Slack ---

def get_custom_emojis():
    """Fetches and caches all custom emojis from the Slack workspace."""
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
        print(f"Unexpected error fetching emojis: {e}")


def get_slack_status():
    """
    Fetches the Slack profile for SLACK_USER_ID.
    Returns a dict with status info, or an error dict.
    """
    if not SLACK_API_TOKEN:
        return {'ok': False, 'error': 'SLACK_API_TOKEN not set.'}
    if not SLACK_USER_ID:
        return {'ok': False, 'error': 'SLACK_USER_ID not set.'}

    try:
        response = client.users_profile_get(user=SLACK_USER_ID)

        if response.get('ok'):
            profile      = response.get('profile', {})
            first_name   = profile.get('first_name', 'My')
            status_text  = profile.get('status_text', 'No status set')
            status_emoji_raw = profile.get('status_emoji', '')

            emoji_info = {'type': 'text', 'value': ''}
            if status_emoji_raw:
                emoji_name = status_emoji_raw.strip(':')
                if emoji_name in custom_emojis:
                    emoji_info['type']  = 'url'
                    emoji_info['value'] = custom_emojis[emoji_name]
                else:
                    emoji_info['value'] = emoji.emojize(status_emoji_raw)

            return {
                'ok':           True,
                'first_name':   first_name,
                'status_text':  status_text,
                'status_emoji': emoji_info,
            }
        else:
            return {'ok': False, 'error': response.get('error', 'Unknown Slack API error')}

    except SlackApiError as e:
        return {'ok': False, 'error': f'Slack API Error: {e.response["error"]}'}
    except Exception as e:
        return {'ok': False, 'error': f'Unexpected error: {e}'}


# --- Routes ---

@app.route('/')
def home():
    if not custom_emojis:
        get_custom_emojis()

    status_data = get_slack_status()

    with music_lock:
        track_title     = current_track['title']
        track_artist    = current_track['artist']
        track_album     = current_track['album']
        track_cover_art = current_track['cover_art']

    if not status_data['ok']:
        return render_template('index.html',
                               first_name='My',
                               status_emoji_value='❌',
                               status_emoji_type='text',
                               status_text=f"Error: {status_data['error']}",
                               is_error=True,
                               track_title=track_title,
                               track_artist=track_artist,
                               track_album=track_album,
                               track_cover_art=track_cover_art)

    return render_template('index.html',
                           first_name=status_data['first_name'],
                           status_emoji_value=status_data['status_emoji']['value'],
                           status_emoji_type=status_data['status_emoji']['type'],
                           status_text=status_data['status_text'],
                           is_error=False,
                           track_title=track_title,
                           track_artist=track_artist,
                           track_album=track_album,
                           track_cover_art=track_cover_art)


@app.route('/preview')
def preview():
    """Renders the page with hardcoded dummy data for local layout testing."""
    return render_template('index.html',
                           first_name='Taylor',
                           status_emoji_value='🎵',
                           status_emoji_type='text',
                           status_text='Available, feel free to DM or walk by.',
                           is_error=False,
                           track_title='Mr. Blue Sky',
                           track_artist='Electric Light Orchestra',
                           track_album='Out of the Blue',
                           track_cover_art='/static/elo-outoftheblue.jpg')


@app.route('/debug-music')
def debug_music():
    """Forces an immediate Last.fm poll and returns diagnostic info as JSON."""
    config = {
        'LAST_FM_API_KEY_set':  bool(LASTFM_API_KEY),
        'LAST_FM_USERNAME_set': bool(LASTFM_USERNAME),
        'LAST_FM_USERNAME':     LASTFM_USERNAME,
    }

    raw_response = None
    parse_error  = None
    title = artist = album = cover_art = None

    try:
        resp = requests.get(
            'https://ws.audioscrobbler.com/2.0/',
            params={
                'method':  'user.getrecenttracks',
                'user':    LASTFM_USERNAME,
                'api_key': LASTFM_API_KEY,
                'format':  'json',
                'limit':   1,
            },
            timeout=10,
        )
        raw_response = resp.json()
        title, artist, album, cover_art = get_lastfm_now_playing()
    except Exception as e:
        parse_error = str(e)

    return jsonify({
        'config':       config,
        'raw_response': raw_response,
        'parsed': {
            'title':     title,
            'artist':    artist,
            'cover_art': cover_art,
        },
        'error': parse_error,
    })


# --- Main ---

if __name__ == '__main__':
    print(f"Starting on http://0.0.0.0:{PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=True)
