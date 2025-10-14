#!/bin/bash
# Start the NL2SQL Frontend

PORT=${1:-3000}  # Default to 3000, or use first argument

echo "🚀 Starting NL2SQL Frontend on port $PORT..."
echo "⚠️  Make sure backend API is running on port 9008!"
echo ""

# Check if backend is running
if ! curl -s http://localhost:9008/health > /dev/null 2>&1; then
    echo "❌ WARNING: Backend API is not running on port 9008"
    echo "Please start it first:"
    echo "  1. cd .. && ./start_model_service.sh"
    echo "  2. cd .. && ./start_app.sh"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✅ Backend API is running"
fi

echo "Starting frontend..."
echo ""

# Start the development server
npm run dev -- -p $PORT

# Usage examples:
# ./start.sh         # Start on port 3000 (default)
# ./start.sh 3001    # Start on port 3001

