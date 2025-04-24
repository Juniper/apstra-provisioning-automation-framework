#!/bin/bash

: <<'HEADER'

********************************************************

Project: Apstra Provisioning Automation Framework

Copyright (c) Juniper Networks, Inc., 2025. All rights reserved.

Notice and Disclaimer: This code is licensed to you under the Apache 2.0 License (the "License"). You may not use this code except in compliance with the License. This code is not an official Juniper product. You can obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.html

SPDX-License-Identifier: Apache-2.0

Third-Party Code: This code may depend on other components under separate copyright notice and license terms. Your use of the source code for those components is subject to the terms and conditions of the respective license as noted in the Third-Party source code file.

********************************************************

DESCRIPTION: This script manages the lifecycle of a Docker container running an application defined in a Docker Compose file. 
It first checks if the Docker service is running, then verifies if the container is already running. 

- If the container is running, the user is prompted to choose between re-running the existing container without rebuilding it or rebuilding and re-running the container. 
- If no running container is found, the script starts a fresh build of the container. 

The script also provides feedback on the containers that are running and their status.

HEADER

# --- Set script to exit on any error
set -e

# --- Function to print messages with timestamp
log() {
    echo ""
    echo "$(date '+%Y-%m-%d %H:%M:%S') $1"
}

# --- Check if a Docker Compose file path was passed as a parameter
if [ -z "$1" ]; then
    echo "Usage: $0 <docker-compose-file>"
    exit 1
fi

# --- Set the docker-compose file variable
compose_file="$1"

# --- Ensure Docker is running
if ! docker info > /dev/null 2>&1; then
    log "Docker is not running. Please start Docker and try again."
    exit 1
fi

# --- Check if the container exists
if docker-compose -f "$compose_file" ps | grep -q "Up"; then
    log "Container is already running."
    echo "Do you want to:"
    echo "1) Re-run the existing container (no rebuild)"
    echo "2) Rebuild and re-run the container"
    read -p "Enter your choice (1 or 2): " choice

    if [[ "$choice" == "1" ]]; then
        echo ""
        log "Restarting container without rebuilding..."
        docker-compose -f "$compose_file" down
        docker-compose -f "$compose_file" up -d --no-build
    elif [[ "$choice" == "2" ]]; then
        echo ""
        log "Rebuilding and restarting container..."
        docker-compose -f "$compose_file" down
        docker-compose -f "$compose_file" up --build -d
    else
        log "Invalid choice. Exiting."
        exit 1
    fi
else
    log "No running container found. Starting with a fresh build..."
    docker-compose -f "$compose_file" up --build -d
fi

# --- Show running containers
echo ""
log "Containers running:"
docker ps

# # --- Follow logs in real-time
# echo ""
# log "Showing live logs. Press Ctrl+C to stop."
# docker-compose -f "$compose_file" logs -f
