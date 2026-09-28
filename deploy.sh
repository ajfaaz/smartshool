#!/bin/bash

# Deployment script for SmartSchool on cPanel
# Syncs repository files to live application directory and executes Django setup.

set -e

REPO_DIR="${REPO_DIR:-/home/jvlbvywb/repositories/smartschool}"
LIVE_DIR="${LIVE_DIR:-/home/jvlbvywb/smartschool}"
VENV_PATH="${VENV_PATH:-/home/jvlbvywb/virtualenv/smartschool/3.10/bin/activate}"

echo "--- Starting SmartSchool Deployment: $(date) ---"

# 1. Update the repository folder
if [ -d "$REPO_DIR/.git" ]; then
    echo "Step 1: Pulling latest changes from GitHub..."
    cd "$REPO_DIR"
    git pull origin main
else
    echo "Step 1: Repo path $REPO_DIR does not exist or is not a git repo. Proceeding..."
fi

# 2. Copy files to the live directory
echo "Step 2: Syncing application files to $LIVE_DIR..."
mkdir -p "$LIVE_DIR"

if command -v rsync >/dev/null 2>&1; then
    rsync -av --delete \
        --exclude='.git' \
        --exclude='.venv' \
        --exclude='*.pyc' \
        --exclude='__pycache__' \
        --exclude='.env' \
        --exclude='db.sqlite3' \
        --exclude='media' \
        --exclude='staticfiles' \
        "$REPO_DIR/" "$LIVE_DIR/"
else
    cp -rf "$REPO_DIR"/* "$LIVE_DIR/"
fi

# 3. Virtual Environment Activation & Django maintenance
echo "Step 3: Running Django migrations and static collection..."
cd "$LIVE_DIR"

if [ -f "$VENV_PATH" ]; then
    echo "Activating virtual environment: $VENV_PATH"
    source "$VENV_PATH"
elif [ -f "/home/jvlbvywb/virtualenv/smartschool/3.14/bin/activate" ]; then
    source "/home/jvlbvywb/virtualenv/smartschool/3.14/bin/activate"
elif [ -f "venv/bin/activate" ]; then
    source "venv/bin/activate"
else
    echo "WARNING: Virtual environment script not found. Using current python..."
fi

echo "Installing & updating dependencies..."
pip install --upgrade pip --quiet || true
pip install -r requirements.txt

echo "Running Django migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

# 4. Restart Passenger WSGI App
echo "Step 4: Restarting Passenger application..."
mkdir -p tmp
touch tmp/restart.txt

echo "--- SmartSchool Deployment Successful! ---"