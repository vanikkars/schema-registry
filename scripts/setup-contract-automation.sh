#!/bin/bash
# Setup script for Atlantis-like automation
# Run this once to configure pre-commit hooks and git settings

set -e

echo "🔧 Setting up Atlantis automation..."
echo ""

# Make pre-commit hook executable
if [ -f ".git/hooks/pre-commit" ]; then
    chmod +x .git/hooks/pre-commit
    echo "✅ Pre-commit hook enabled"
else
    echo "⚠️  Pre-commit hook not found"
fi

# Make validation script executable
if [ -f "scripts/validate-contracts.py" ]; then
    chmod +x scripts/validate-contracts.py
    echo "✅ Validation script executable"
else
    echo "⚠️  Validation script not found"
fi

# Check if GitHub workflows directory exists
if [ ! -d ".github/workflows" ]; then
    mkdir -p .github/workflows
    echo "✅ Created .github/workflows directory"
fi

# Check if workflow file exists
if [ -f ".github/workflows/atlantis-schema-validation.yml" ]; then
    echo "✅ GitHub Actions workflow found"
else
    echo "⚠️  GitHub Actions workflow not found"
fi

echo ""
echo "📋 Configuration Summary:"
echo "========================"
echo ""
echo "✅ Atlantis automation is configured!"
echo ""
echo "Next steps:"
echo "1. Push to GitHub: git push origin main"
echo "2. Create a test PR with contract changes"
echo "3. Watch the automation in action!"
echo ""
echo "📚 Learn more:"
echo "  - Quick start: ATLANTIS_QUICKSTART.md"
echo "  - Full docs: docs/ATLANTIS_SETUP.md"
echo ""
echo "🧪 Test locally:"
echo "  - Run: make docker-up"
echo "  - Run: make validate-contracts"
echo ""

echo "✨ Setup complete!"