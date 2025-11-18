#!/bin/bash

# Script to push the Latent Knowledge Explorer to GitHub

echo "======================================"
echo "Latent Knowledge Explorer - GitHub Push"
echo "======================================"
echo ""

# Check if git is initialized
if [ ! -d .git ]; then
    echo "Error: Git repository not initialized"
    exit 1
fi

echo "Repository is ready to push to GitHub."
echo ""
echo "You have two options to authenticate:"
echo ""
echo "Option 1: Using GitHub Personal Access Token (Recommended)"
echo "  1. Go to https://github.com/settings/tokens"
echo "  2. Generate a new token with 'repo' scope"
echo "  3. Run: git push -u origin main"
echo "  4. Use your GitHub username and the token as password"
echo ""
echo "Option 2: Using SSH (if configured)"
echo "  1. Change remote to SSH:"
echo "     git remote set-url origin git@github.com:johnjanik/LatentKnowledgeExplorer.git"
echo "  2. Push: git push -u origin main"
echo ""
echo "Current remote URL:"
git remote -v
echo ""
echo "To push now with HTTPS (you'll be prompted for credentials):"
echo "Press Enter to continue or Ctrl+C to cancel..."
read

# Attempt to push
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Successfully pushed to GitHub!"
    echo "View your repository at: https://github.com/johnjanik/LatentKnowledgeExplorer"
else
    echo ""
    echo "❌ Push failed. Please check your credentials and try again."
    echo ""
    echo "If you haven't created the repository yet:"
    echo "1. Go to https://github.com/new"
    echo "2. Create a new repository named 'LatentKnowledgeExplorer'"
    echo "3. Don't initialize with README, .gitignore, or license"
    echo "4. Run this script again"
fi