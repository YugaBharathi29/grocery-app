#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status
set -o errexit

# Upgrade pip packages to latest stable versions for build tools
pip install --upgrade pip setuptools wheel

# Install all dependencies from requirements.txt
pip install -r requirements.txt

# Initialize the database
python init_db.py