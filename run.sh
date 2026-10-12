#!/usr/bin/env bash
set -e

echo "=== Starting Nyaya-Setu Legal Agent ==="

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

echo "Activating virtual environment..."
source .venv/bin/activate

echo "Installing/checking dependencies..."
pip install -r requirements.txt

# Check for .env file
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "Creating .env from .env.example..."
        cp .env.example .env
        echo "Please add your SARVAM_API_KEY inside the .env file."
    fi
fi

echo "Launching Streamlit application on http://localhost:8501..."
streamlit run app.py --server.port=8501
