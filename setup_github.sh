#!/bin/bash

echo "=================================="
echo "GitHub Repository Setup"
echo "=================================="
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install git first."
    exit 1
fi

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "⚠️  GitHub CLI (gh) is not installed."
    echo "Install from: https://cli.github.com/"
    echo ""
    echo "Or continue with manual setup..."
    echo ""
fi

# Initialize git repo
echo "Initializing git repository..."
git init

# Add all files
echo "Adding files to git..."
git add .

# Create initial commit
echo "Creating initial commit..."
git commit -m "Initial commit: Production-ready RAG Documentation API

Features:
- LangChain-based RAG pipeline
- FastAPI REST endpoints
- FAISS vector store
- Evaluation suite
- Docker deployment
- Comprehensive documentation"

echo ""
echo "✅ Local repository initialized!"
echo ""

# Instructions for GitHub
echo "=================================="
echo "Next Steps:"
echo "=================================="
echo ""
echo "Option 1: Using GitHub CLI (if installed)"
echo "  gh auth login"
echo "  gh repo create rag-documentation-api --public --source=. --remote=origin"
echo "  git push -u origin main"
echo ""
echo "Option 2: Manual GitHub Setup"
echo "  1. Go to https://github.com/venumartha"
echo "  2. Click 'New Repository'"
echo "  3. Name it: rag-documentation-api"
echo "  4. Make it public"
echo "  5. Do NOT initialize with README (we already have one)"
echo "  6. Run these commands:"
echo ""
echo "     git remote add origin https://github.com/venumartha/rag-documentation-api.git"
echo "     git branch -M main"
echo "     git push -u origin main"
echo ""
echo "=================================="
echo ""

# Offer to create README badges
echo "Would you like to add GitHub badges to README? (y/n)"
read -r ADD_BADGES

if [ "$ADD_BADGES" = "y" ]; then
    cat > badges.md << 'EOF'
<!-- Add these badges to the top of README.md -->

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![LangChain](https://img.shields.io/badge/LangChain-0.0.335-orange.svg)](https://python.langchain.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-ready-blue.svg)](https://www.docker.com/)

EOF
    echo ""
    echo "✅ Badges saved to badges.md"
    echo "Copy the content and paste at the top of README.md"
    echo ""
fi

echo "🎉 Repository setup complete!"
echo ""
echo "Don't forget to:"
echo "  1. Add your OpenAI API key to .env"
echo "  2. Add documentation files to ./docs"
echo "  3. Test locally before pushing"
echo "  4. Update README with your specific details"
echo ""
