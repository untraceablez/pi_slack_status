#!/bin/bash
# start_pi_status.sh
#
# This script starts the Flask application and then launches a fullscreen
# Chromium browser in kiosk mode to display the web page.

# IMPORTANT: Replace 'pi' with your actual username if it's different.
# This assumes your repository is cloned to /home/pi/pi_slack_status.
REPO_PATH="/home/pi/pi_slack_status"
VENV_PATH="/home/pi/.venv/pi-slack"
USER_NAME="pi"

# Navigate to the repository directory.
cd "$REPO_PATH" || { echo "Failed to change directory to $REPO_PATH"; exit 1; }

# Activate the Python virtual environment.
source "$VENV_PATH/bin/activate" || { echo "Failed to activate virtual environment at $VENV_PATH"; exit 1; }

# Start the Flask application in the background.
# 'nohup' prevents the process from being killed when the parent shell exits.
# Output is redirected to /dev/null to prevent it from cluttering the logs.
# 'python3 -m flask run' is used as it's a standard way to run Flask apps.
nohup python3 -m flask run --host=0.0.0.0 > /dev/null 2>&1 &

# Store the Process ID (PID) of the Flask app so we can manage it later if needed.
FLASK_PID=$!
echo "Flask app started with PID: $FLASK_PID"

# Wait a few seconds to ensure the server has time to start up before the browser tries to access it.
sleep 5

# Launch Chromium in kiosk mode, pointing to the local Flask server.
# The '--incognito' flag prevents caching issues and session persistence.
# The '--noerrdialogs' flag suppresses error dialogs, which is useful in a kiosk environment.
# 'x-terminal-emulator' ensures the browser runs within the graphical session.
/usr/bin/chromium-browser --kiosk --incognito --app="http://127.0.0.1:5000" --disable-pinch --disable-overscroll-edge-effects --noerrdialogs --user-data-dir="/home/$USER_NAME/.config/chromium/kiosk"
