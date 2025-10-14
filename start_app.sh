#!/bin/bash
# Start the main application
# Make sure the model service is running first!

PORT=${1:-9008}  # Default to 9008, or use first argument

echo "🚀 Starting NL2SQL Application on port $PORT..."
echo "⚠️  Make sure model service is running on port 8888!"
echo ""

# Check if model service is running
if ! curl -s http://localhost:8888/health > /dev/null; then
    echo "❌ ERROR: Model service is not running on port 8888"
    echo "Please start it first: ./start_model_service.sh"
    exit 1
fi

echo "✅ Model service is running"
echo "Starting application..."
echo ""

# Start the application
uvicorn main:app --reload --port $PORT --host 0.0.0.0

# Usage examples:
# ./start_app.sh         # Start on port 9008 (default)
# ./start_app.sh 9009    # Start on port 9009
# ./start_app.sh 9010    # Start on port 9010

