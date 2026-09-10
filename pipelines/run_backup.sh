#!/bin/bash
# Research Node — Run: Backup
echo "▶ Starting backup..."
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p "${HOME}/backups"
tar czf "${HOME}/backups/backup_${TIMESTAMP}.tar.gz" \
    -C "${HOME}" \
    --exclude='backups' \
    --exclude='.cache' \
    --exclude='node_modules' \
    . 2>/dev/null
echo "✓ Backup done: backup_${TIMESTAMP}.tar.gz"
