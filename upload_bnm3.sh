#!/bin/bash

# 1. Load the secret from the .env file
if [ -f .env ]; then
    # Export variables (this will load NEPA_TOKEN)
    export $(grep -v '^#' .env | xargs)
else
    echo "❌ Error: .env file not found"
    exit 1
fi

# 2. Token validation and URL definition
if [ -z "$NEPA_TOKEN" ]; then
    echo "❌ Error: NEPA_TOKEN variable is empty in the .env file"
    exit 1
fi

# Define the URL using your username and the loaded token
GITHUB_USER="nepamuceno"
REPO_URL="https://${GITHUB_USER}:${NEPA_TOKEN}@github.com/${GITHUB_USER}/borednomore3.git"

# 3. Configure paths and history
PROJECT_DIR=$(pwd)
HIST_DIR="$PROJECT_DIR/history"
HIST_FILE="$HIST_DIR/last-100-history.txt"
mkdir -p "$HIST_DIR"

if [ -f "$HOME/.bash_history" ]; then
    tail -n 100 "$HOME/.bash_history" | awk '{$1=""; sub(/^ /,""); print}' > "$HIST_FILE"
fi

# 4. Prepare commit messages and tags
echo "--- Uploading changes to GitHub (borednomore3 - Safe Mode) ---"
read -p "Enter commit message: " COMMIT_MSG

if [ -z "$COMMIT_MSG" ]; then
    COMMIT_MSG="Update: $(date +'%Y-%m-%d %H:%M')"
fi

read -p "Extra note for the tag (optional): " EXTRA_NOTE
EXTRA_NOTE_CLEAN=$(echo "$EXTRA_NOTE" | tr ' ' '_')

BASE_TAG="stable-$(date +'%d_%m_%Y_%H_%M')"
if [ -n "$EXTRA_NOTE_CLEAN" ]; then
    TAG_MSG="${BASE_TAG}-${EXTRA_NOTE_CLEAN}"
else
    TAG_MSG="$BASE_TAG"
fi

# 5. Git operations
git add -A

# Only commit if changes are detected
if ! git diff-index --quiet HEAD --; then
    git commit -m "$COMMIT_MSG"
else
    echo "ℹ No new changes, only tags will be updated if necessary."
fi

git tag "$TAG_MSG"

# 6. Safe synchronization and push
echo "📥 Checking remote state..."
if ! git fetch "$REPO_URL" main; then
    echo "❌ Error: Could not contact remote."
    git tag -d "$TAG_MSG"
    exit 1
fi

LOCAL=$(git rev-parse main)
REMOTE=$(git rev-parse FETCH_HEAD)

if [ "$LOCAL" != "$REMOTE" ]; then
    echo "⚠ Your local branch and the remote branch are out of sync."
    read -p "Do you want to run 'git pull --rebase' to synchronize? (y/n): " CONFIRM
    if [ "$CONFIRM" = "y" ]; then
        if ! git pull --rebase "$REPO_URL" main; then
            echo "❌ Error: Conflicts occurred during rebase. Please resolve manually."
            git tag -d "$TAG_MSG"
            exit 1
        fi
    else
        echo "ℹ Operation cancelled by user. Nothing was uploaded."
        git tag -d "$TAG_MSG"
        exit 0
    fi
fi

echo "🚀 Uploading changes..."
if git push "$REPO_URL" main --tags; then
    echo "✅ Upload completed successfully with tag: $TAG_MSG"
else
    echo "❌ Error: Upload failed."
    git tag -d "$TAG_MSG"
    exit 1
fi
