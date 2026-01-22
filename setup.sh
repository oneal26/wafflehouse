#!/bin/bash

echo "🧇 Waffle House Simulator - Setup Script"
echo "========================================"
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Initialize database
echo ""
echo "Initializing database..."
python3 -c "from models import init_db; init_db(); print('✅ Database initialized')"

echo ""
echo "========================================"
echo "✅ Setup complete!"
echo ""
echo "To start the server:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Run the app: python3 app.py"
echo ""
echo "Or simply run: ./run.sh"
echo ""
echo "The app will be available at: http://localhost:3333"
echo "========================================"
