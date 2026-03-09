# app.py
# This is a Python Flask web application that serves your Slack status and
# identifies music playing nearby using a USB microphone via Shazam.
# To run this, you need to have the packages in requirements.txt installed.

import os
import asyncio
import threading
import tempfile
import time
from flask import Flask, render_template, jsonify
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import emoji
import sounddevice as sd
import scipy.io.wavfile as wavfile
import numpy as np
from shazamio import Shazam

# Load environment variables from the .env file.
load_dotenv()

# --- Configuration ---
SLACK_API_TOKEN = os.environ.get('SLACK_API_TOKEN')
SLACK_USER_ID = os.environ.get('SLACK_USER_ID')
PORT = 5000

# Audio device index for the USB mic. Set AUDIO_DEVICE in .env to the device
# index if the default device is not your USB mic. Leave unset to use default.
AUDIO_DEVICE = os.environ.get('AUDIO_DEVICE')
if AUDIO_DEVICE is not None:
    AUDIO_DEVICE = int(AUDIO_DEVICE)

SAMPLE_RATE = 44100
RECORD_DURATION = 12      # seconds of audio to capture per recognition attempt
RECOGNITION_INTERVAL = 30 # seconds between recognition attempts

# --- Global State ---
custom_emojis = {}

current_track = {
    'title': None,
    'artist': None,
    'cover_art': None,
    'last_checked': 0,
}
is_detecting = False
music_lock = threading.Lock()

# --- App Setup ---
app = Flask(__name__)
client = WebClient(token=SLACK_API_TOKEN)

# --- Music Recognition ---

def record_audio():
    """Record a short clip from the USB mic and return as a numpy array."""
    audio = sd.rec(
        int(RECORD_DURATION * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype='int16',
        device=AUDIO_DEVICE,
    )
    sd.wait()
    rms = int(np.sqrt(np.mean(audio.astype(np.float32) ** 2)))
    print(f"Audio captured: {len(audio)} samples, RMS level: {rms}")
    return audio


async def _shazam_recognize(wav_path):
    shazam = Shazam()
    return await shazam.recognize(wav_path)


def identify_track(wav_path):
    """Run Shazam recognition synchronously and return (title, artist, cover_art) or (None, None, None)."""
    result = asyncio.run(_shazam_recognize(wav_path))
    track = result.get('track', {})
    title = track.get('title')
    artist = track.get('subtitle')
    images = track.get('images', {})
    cover_art = (images.get('coverarthq')
                 or images.get('coverart')
                 or track.get('share', {}).get('image'))
    return title, artist, cover_art


def music_recognition_loop():
    """Background thread: periodically records audio and identifies music."""
    global current_track, is_detecting
    while True:
        with music_lock:
            last_checked = current_track['last_checked']

        if time.time() - last_checked >= RECOGNITION_INTERVAL:
            tmp_path = None
            try:
                with music_lock:
                    is_detecting = True

                audio = record_audio()
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                    tmp_path = f.name
                    wavfile.write(f.name, SAMPLE_RATE, audio)

                title, artist, cover_art = identify_track(tmp_path)

                with music_lock:
                    current_track = {
                        'title': title,
                        'artist': artist,
                        'cover_art': cover_art,
                        'last_checked': time.time(),
                    }
                    is_detecting = False
                print(f"Music identified: {artist} - {title}" if title else "No music detected.")
            except Exception as e:
                print(f"Music recognition error: {e}")
                with music_lock:
                    current_track['last_checked'] = time.time()
                    is_detecting = False
            finally:
                if tmp_path and os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        time.sleep(5)


# Start the music recognition background thread
_music_thread = threading.Thread(target=music_recognition_loop, daemon=True)
_music_thread.start()

# --- Slack Functions ---

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
        print(f"An unexpected error occurred while fetching emojis: {e}")


def get_slack_status():
    """
    Fetches the profile of the specified user from the Slack API.
    Returns a dictionary with status information or an error message.
    """
    if not SLACK_API_TOKEN:
        return {'ok': False, 'error': 'Slack API Token not found in environment variables.'}
    if not SLACK_USER_ID:
        return {'ok': False, 'error': 'Slack User ID not found in environment variables.'}

    try:
        response = client.users_profile_get(user=SLACK_USER_ID)

        if response.get('ok'):
            profile = response.get('profile', {})
            first_name = profile.get('first_name', 'My')
            status_text = profile.get('status_text', 'No status set')
            status_emoji = profile.get('status_emoji', '')

            emoji_info = {'type': 'text', 'value': ''}
            if status_emoji:
                emoji_name = status_emoji.strip(':')
                if emoji_name in custom_emojis:
                    emoji_info['type'] = 'url'
                    emoji_info['value'] = custom_emojis[emoji_name]
                else:
                    converted_emoji = emoji.emojize(status_emoji)
                    emoji_info['value'] = converted_emoji

            return {
                'ok': True,
                'first_name': first_name,
                'status_text': status_text,
                'status_emoji': emoji_info,
            }
        else:
            return {'ok': False, 'error': response.get('error', 'Unknown Slack API error')}
    except SlackApiError as e:
        return {'ok': False, 'error': f'Slack API Error: {e.response["error"]}'}
    except Exception as e:
        return {'ok': False, 'error': f'An unexpected error occurred: {e}'}


# --- Routes ---

@app.route('/')
def home():
    if not custom_emojis:
        get_custom_emojis()

    status_data = get_slack_status()

    with music_lock:
        track_title = current_track['title']
        track_artist = current_track['artist']
        track_cover_art = current_track['cover_art']
        detecting = is_detecting

    if not status_data['ok']:
        return render_template('index.html',
                               first_name='My',
                               status_emoji_value='❌',
                               status_emoji_type='text',
                               status_text=f"Error: {status_data['error']}",
                               is_error=True,
                               track_title=track_title,
                               track_artist=track_artist,
                               track_cover_art=track_cover_art,
                               is_detecting=detecting)

    return render_template('index.html',
                           first_name=status_data['first_name'],
                           status_emoji_value=status_data['status_emoji']['value'],
                           status_emoji_type=status_data['status_emoji']['type'],
                           status_text=status_data['status_text'],
                           is_error=False,
                           track_title=track_title,
                           track_artist=track_artist,
                           track_cover_art=track_cover_art,
                           is_detecting=detecting)


@app.route('/debug-music')
def debug_music():
    """
    Forces an immediate audio capture and Shazam recognition attempt.
    Returns the raw result as JSON for debugging.
    """
    tmp_path = None
    try:
        audio = record_audio()
        rms = int(np.sqrt(np.mean(audio.astype(np.float32) ** 2)))

        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            tmp_path = f.name
            wavfile.write(f.name, SAMPLE_RATE, audio)

        title, artist, cover_art = identify_track(tmp_path)

        return jsonify({
            'ok': True,
            'audio_rms': rms,
            'audio_device': AUDIO_DEVICE,
            'sample_rate': SAMPLE_RATE,
            'record_duration': RECORD_DURATION,
            'title': title,
            'artist': artist,
            'cover_art': cover_art,
        })
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


# --- Main Entry Point ---

if __name__ == '__main__':
    print(f"Starting Slack Status app on http://127.0.0.1:{PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=True)
