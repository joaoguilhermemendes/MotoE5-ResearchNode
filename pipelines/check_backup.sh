#!/bin/bash
# Research Node — Check: Backup
BACKUP_DIR="${HOME}/backups"
LATEST=$(ls -t "$BACKUP_DIR"/*.tar.gz 2>/dev/null | head -1)

if [ -n "$LATEST" ]; then
    # Verifica se o backup tem menos de 48h
    if find "$LATEST" -mmin -2880 -print -quit | grep -q .; then
        SIZE=$(du -h "$LATEST" | cut -f1)
        echo "OK: backup $SIZE"
        exit 0
    else
        echo "WARN: last backup older than 48h"
        exit 2
    fi
else
    echo "FAIL: no backups found"
    exit 1
fi
