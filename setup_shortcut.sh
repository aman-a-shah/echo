#!/bin/bash

# Setup script for Echo

echo "Setting up Echo..."

# Check if Python is installed
if ! command -v python3 &> /dev/null
then
    echo "Python3 could not be found. Please install Python3 and try again."
    exit
fi

# Create a virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate the virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run the app
echo "Starting Echo..."
python3 main.py
