#!/bin/bash
# SelimCam - GitHub Upload Helper
# Just run this script to get started!

echo "════════════════════════════════════════════════════════"
echo "  SelimCam v2.0 - GitHub Upload Helper"
echo "════════════════════════════════════════════════════════"
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install git first:"
    echo "   brew install git  (on macOS)"
    echo "   sudo apt install git  (on Linux)"
    exit 1
fi

# Get GitHub username
echo "📋 Enter your GitHub username:"
read -p "   GitHub username: " GITHUB_USERNAME

if [ -z "$GITHUB_USERNAME" ]; then
    echo "❌ GitHub username is required!"
    exit 1
fi

echo ""
echo "📋 Enter repository name (default: FINALMAINCAMMM):"
read -p "   Repository name: " REPO_NAME

REPO_NAME=${REPO_NAME:-FINALMAINCAMMM}

echo ""
echo "════════════════════════════════════════════════════════"
echo "  Setting up git repository..."
echo "════════════════════════════════════════════════════════"
echo ""

# Initialize git
cd "$(dirname "$0")"

if [ -d ".git" ]; then
    echo "✅ Git repository already initialized"
else
    echo "🔧 Initializing git..."
    git init
fi

# Configure git (optional)
echo ""
echo "📝 Configuring git..."
git config user.name "SelimCam User"
git config user.email "selimcam@local"

# Add all files
echo ""
echo "📦 Adding all files..."
git add .

# Show status
echo ""
echo "📊 Files to be pushed:"
git status

# Create initial commit
echo ""
echo "💾 Creating initial commit..."
git commit -m "Initial commit: SelimCam v2.0 - Production camera app for Raspberry Pi 3 A+"

# Add remote
echo ""
echo "🔗 Connecting to GitHub..."
echo "   Repository: https://github.com/${GITHUB_USERNAME}/${REPO_NAME}.git"

git remote remove origin 2>/dev/null
git remote add origin "https://github.com/${GITHUB_USERNAME}/${REPO_NAME}.git"

# Rename to main
git branch -M main

echo ""
echo "════════════════════════════════════════════════════════"
echo "  ✅ Ready to push!"
echo "════════════════════════════════════════════════════════"
echo ""
echo "📌 Next steps:"
echo ""
echo "1️⃣  Create repository on GitHub:"
echo "    Go to: https://github.com/new"
echo "    Name: ${REPO_NAME}"
echo "    Create repository"
echo ""
echo "2️⃣  Push to GitHub:"
echo "    git push -u origin main"
echo ""
echo "3️⃣  Enter your GitHub credentials when prompted"
echo ""
echo "════════════════════════════════════════════════════════"
echo ""
echo "ℹ️  After creating the repo on GitHub, run:"
echo "   git push -u origin main"
echo ""
