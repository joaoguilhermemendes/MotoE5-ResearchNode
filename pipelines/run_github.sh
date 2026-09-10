#!/bin/bash
# Research Node — Run: GitHub Sync
echo "▶ Syncing repos..."
REPOS_DIR="${HOME}/repos"

for dir in "$REPOS_DIR"/*/; do
    if [ -d "$dir/.git" ]; then
        cd "$dir" || continue
        NAME=$(basename "$dir")
        echo "  → $NAME"
        git add -A 2>/dev/null
        git commit -m "auto-sync from research node" 2>/dev/null
        git push 2>/dev/null || echo "    (push failed)"
    fi
done
echo "✓ Sync done"
