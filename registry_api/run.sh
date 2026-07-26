#!/bin/bash

# Start the Registry API server
# Usage: bash registry_api/run.sh

set -e

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found"
    echo "Please create .env from .env.example:"
    echo "  cp .env.example .env"
    exit 1
fi

# Load environment variables
echo "📂 Loading environment from .env..."
set -a
source .env
set +a

# Verify AWS credentials
if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
    echo "❌ Error: AWS credentials not found in .env"
    exit 1
fi

echo "✅ Environment loaded"
echo ""
echo "🚀 Starting Registry API server..."
echo "📍 Server will run at http://localhost:8000"
echo "📖 API docs available at http://localhost:8000/docs"
echo ""

# Run the server
python -m uvicorn registry_api.app.main:app --host 0.0.0.0 --port 8000 --reload