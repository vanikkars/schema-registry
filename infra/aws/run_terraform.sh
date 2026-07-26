#!/bin/bash

# Load environment from .env in project root
ENV_FILE="../../.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Error: .env file not found at $ENV_FILE"
    echo "Please create .env from .env.example:"
    echo "  cp .env.example .env"
    exit 1
fi

echo "📂 Loading environment from $ENV_FILE..."
set -a
source "$ENV_FILE"
set +a

# Verify AWS credentials are loaded
if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
    echo "❌ Error: AWS credentials not found in .env"
    echo "Make sure these are set in .env:"
    echo "  export AWS_ACCESS_KEY_ID=your_key"
    echo "  export AWS_SECRET_ACCESS_KEY=your_secret"
    exit 1
fi

echo "✅ Credentials loaded: $AWS_ACCESS_KEY_ID (***)"
echo "Running: terraform $@"
echo ""

# Run terraform with loaded environment
terraform "$@"