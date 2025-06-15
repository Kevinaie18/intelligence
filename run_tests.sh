#!/bin/bash

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run tests with coverage
echo "Running tests with coverage..."
pytest --cov=src --cov-report=html --cov-report=term-missing

# Deactivate virtual environment
deactivate

echo "Tests completed. Coverage report available in htmlcov/index.html" 