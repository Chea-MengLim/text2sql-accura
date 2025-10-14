#!/bin/bash
# Start the Model Service (loads Snowflake model once)
# Run this FIRST before starting your application instances

echo "🚀 Starting SQL Model Service on port 8888..."
echo "📝 This service will load the Snowflake model ONCE and share it across all app instances"
echo ""

# Activate your virtual environment if needed
# source venv/bin/activate
# or for conda: conda activate your_env

# Start the model service
python -m service.model_service

# Alternative using uvicorn directly:
# uvicorn service.model_service:app --host 0.0.0.0 --port 8888 --reload

