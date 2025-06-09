#!/bin/bash

# Define the service file name
SERVICE_FILE="slack_status.service"
SERVICE_PATH="/etc/systemd/system/${SERVICE_FILE}"

echo "Starting systemd service deployment for ${SERVICE_FILE}"

# Check if the service file exists in the current directory
if [ ! -f "$SERVICE_FILE" ]; then
    echo "Error: ${SERVICE_FILE} not found in the current directory."
    echo "Please ensure the script is run from the directory containing ${SERVICE_FILE}."
    exit 1
fi

# Copy the service file to the systemd directory
echo "Copying ${SERVICE_FILE} to ${SERVICE_PATH}..."
sudo cp "$SERVICE_FILE" "$SERVICE_PATH"

# Check if the copy was successful
if [ $? -ne 0 ]; then
    echo "Error: Failed to copy ${SERVICE_FILE}. Please check permissions."
    exit 1
fi
echo "Copy successful."

# Reload systemd daemon
echo "Reloading systemd daemon..."
sudo systemctl daemon-reload
if [ $? -ne 0 ]; then
    echo "Error: Failed to reload systemd daemon."
    exit 1
fi
echo "Systemd daemon reloaded."

# Restart the service
echo "Restarting ${SERVICE_FILE}..."
sudo systemctl restart "${SERVICE_FILE}"
if [ $? -ne 0 ]; then
    echo "Error: Failed to restart ${SERVICE_FILE}. Check service file for errors."
    exit 1
fi
echo "${SERVICE_FILE} restarted."

# Print the status of the service
echo -e "\n--- Status of ${SERVICE_FILE} ---"
sudo systemctl status "${SERVICE_FILE}"
echo -e "--- End Status ---"

echo "Deployment script finished."