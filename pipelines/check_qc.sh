#!/bin/bash
# Research Node — Check: Quality Control
QC_DIR="${HOME}/data/qc"
LATEST=$(ls -t "$QC_DIR"/*.html 2>/dev/null | head -1)

if [ -n "$LATEST" ]; then
    if find "$LATEST" -mmin -1440 -print -quit | grep -q .; then
        echo "OK: QC report $(basename $LATEST)"
        exit 0
    else
        echo "WARN: QC report older than 24h"
        exit 2
    fi
else
    echo "FAIL: no QC reports found"
    exit 1
fi
