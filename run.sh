#!/bin/bash

echo "🧇 Starting Waffle House Simulator..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "❌ Virtual environment not found!"
    echo "Please run ./setup.sh first"
    exit 1
fi

# Check if database exists
if [ ! -f "wafflehouse.db" ]; then
    echo "📊 Initializing database..."
    python3 -c "from models import init_db; init_db()"
fi

# Run the Flask app
echo "🚀 Launching server..."
echo ""
echo "========================================"
echo "Waffle House Simulator is running!"
echo "Open your browser to: http://localhost:3333"
echo "Press Ctrl+C to stop the server"
echo "========================================"
echo ""

python3 app.py
