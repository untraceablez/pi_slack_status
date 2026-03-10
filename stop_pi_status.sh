#!/bin/bash
# stop_pi_status.sh
#
# Kills the Flask app and Chromium kiosk so start_pi_status.sh can be re-run
# without rebooting.

echo "Stopping Chromium..."
pkill -f "chromium-browser.*kiosk" && echo "  Chromium stopped." || echo "  Chromium was not running."

echo "Stopping Flask..."
pkill -f "flask run" && echo "  Flask stopped." || echo "  Flask was not running."

# Give processes a moment to exit cleanly before returning to the prompt.
sleep 1
echo "Done. Run ./start_pi_status.sh to restart."
