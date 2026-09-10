#!/bin/bash
# Research Node — Check: GitHub Sync
REPOS_DIR="${HOME}/repos"
ISSUES=0

for dir in "$REPOS_DIR"/*/; do
    if [ -d "$dir/.git" ]; then
        cd "$dir" || continue
        CHANGES=$(git status --porcelain 2>/dev/null | wc -l)
        if [ "$CHANGES" -gt 0 ]; then
            echo "WARN: $(basename $dir) has $CHANGES uncommitted changes"
            ISSUES=$((ISSUES + 1))
        fi
    fi
done

if [ "$ISSUES" -eq 0 ]; then
    echo "OK: all repos clean"
    exit 0
elif [ "$ISSUES" -le 2 ]; then
    exit 2
else
    exit 1
fi
