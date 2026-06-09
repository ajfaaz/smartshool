#!/bin/bash

# Deployment script for SmartSchool on cPanel (No Rsync version)
# This script copies files from the git repository folder to the live app folder.

set -e

# Configuration - Update these if paths differ on your server
REPO_DIR="/home/jvlbvywb/repositories/smartschool"
LIVE_DIR="/home/jvlbvywb/smartschool"

echo "--- Starting Deployment: $(date) ---"

# 1. Update the repository folder
echo "Step 1: Pulling latest changes from GitHub..."
cd $REPO_DIR
git pull origin main

# 2. Copy files to the live directory
# We use 'cp -rf' to copy everything. 
# Note: .env and db.sqlite3 should be in your .gitignore so they aren't in the repo.
echo "Step 2: Copying files to $LIVE_DIR..."
cp -rf $REPO_DIR/* $LIVE_DIR/

# 3. Django maintenance
echo "Step 3: Running Django migrations and static collection..."
cd $LIVE_DIR

# Assuming the virtual environment is already activated or using the system python 
# as configured in cPanel's Setup Python App
python manage.py migrate
python manage.py collectstatic --noinput

# 4. Restart Passenger
echo "Step 4: Restarting the application..."
mkdir -p tmp
touch tmp/restart.txt

echo "--- Deployment Successful! ---"