#!/bin/bash
# Research Node — Check: Variant Calling Pipeline
VCF_DIR="${HOME}/data/variants"
LATEST_VCF=$(ls -t "$VCF_DIR"/*.vcf.gz 2>/dev/null | head -1)

if [ -n "$LATEST_VCF" ]; then
    if find "$LATEST_VCF" -mmin -4320 -print -quit | grep -q .; then
        # Conta variantes no VCF
        COUNT=$(zcat "$LATEST_VCF" 2>/dev/null | grep -cv "^#" || echo "?")
        echo "OK: $COUNT variants in $(basename $LATEST_VCF)"
        exit 0
    else
        echo "WARN: VCF older than 7 days"
        exit 2
    fi
else
    echo "FAIL: no VCF files found"
    exit 1
fi
