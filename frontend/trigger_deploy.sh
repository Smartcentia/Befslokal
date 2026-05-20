#!/bin/bash
# Trigger Vercel deploy via Git push

echo "🚀 Triggering Vercel deploy via Git..."

# Check if we're in a git repo
if [ ! -d .git ]; then
    echo "❌ Not a git repository"
    exit 1
fi

# Check if we have changes
if git diff --quiet && git diff --cached --quiet; then
    echo "📝 Creating empty commit to trigger deploy..."
    git commit --allow-empty -m "Trigger Vercel redeploy - DATABASE_URL updated"
    
    echo "📤 Pushing to trigger Vercel deploy..."
    git push
    
    echo "✅ Push complete! Vercel should deploy automatically."
    echo "   Check: https://vercel.com/dashboard"
else
    echo "⚠️  You have uncommitted changes. Commit them first:"
    git status
fi
