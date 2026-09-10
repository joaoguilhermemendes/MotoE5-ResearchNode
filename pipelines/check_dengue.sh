#!/bin/bash
# Research Node — Check: Dengue Analysis Pipeline
# Exit 0 = OK, 1 = FAILED, outro = WARNING
#
# Este é um placeholder. Substitua pelo comando real que verifica
# se seu pipeline de análise de dengue está saudável.
#
# Exemplos:
#   - Verificar se um arquivo de resultado existe e é recente
#   - Rodar um health check do pipeline
#   - Verificar se o último run foi bem sucedido

RESULT_FILE="${HOME}/data/dengue/latest_results.tsv"

if [ -f "$RESULT_FILE" ]; then
    # Verifica se o arquivo foi modificado nas últimas 24h
    if find "$RESULT_FILE" -mmin -1440 -print -quit | grep -q .; then
        echo "OK: results fresh"
        exit 0
    else
        echo "WARN: results older than 24h"
        exit 2
    fi
else
    echo "FAIL: no results found at $RESULT_FILE"
    exit 1
fi
