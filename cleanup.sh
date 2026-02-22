#!/bin/bash

echo "========================================"
echo "  Attend-X Project Cleanup"
echo "========================================"
echo ""
echo "This will remove:"
echo "- Virtual environments"
echo "- Node modules"
echo "- Cache files"
echo "- Log files"
echo "- Temporary files"
echo ""
read -p "Press Enter to continue or Ctrl+C to cancel..."

echo ""
echo "Cleaning up..."
echo ""

# Remove Python cache
echo "Removing Python cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null

# Remove virtual environments
echo "Removing virtual environments..."
rm -rf .venv
rm -rf backend/venv

# Remove Node modules
echo "Removing node_modules..."
rm -rf frontend/node_modules
rm -rf node_modules

# Remove log files
echo "Removing log files..."
rm -f backend.log
rm -f backend/check_db.log
rm -f backend/*.log

# Remove package-lock.json
echo "Removing package-lock.json..."
rm -f frontend/package-lock.json
rm -f package-lock.json

echo ""
echo "========================================"
echo "  Cleanup Complete!"
echo "========================================"
echo ""
echo "To reinstall dependencies:"
echo ""
echo "Backend:"
echo "  cd backend"
echo "  python -m venv venv"
echo "  source venv/bin/activate"
echo "  pip install -r requirements.txt"
echo ""
echo "Frontend:"
echo "  cd frontend"
echo "  npm install"
echo ""
