#!/usr/bin/env bash

# Da eseguire nella root dir:
#   ./Translations/scripts/automatic_compressor.sh <lingua> [livelli HSK...]
# Esempi:
#   ./Translations/scripts/automatic_compressor.sh italian
#   ./Translations/scripts/automatic_compressor.sh english 1 2 3 4 5 6

set -euo pipefail

if [ $# -lt 1 ]; then
    echo "Uso: $0 <lingua> [livelli HSK...]" >&2
    exit 1
fi

LANGUAGE="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')"   # es. italian
FIRST="$(printf '%s' "${LANGUAGE:0:1}" | tr '[:lower:]' '[:upper:]')"
LANG_DIR="${FIRST}${LANGUAGE:1}"                              # es. Italian
shift

if [ $# -gt 0 ]; then
    LEVELS=("$@")
else
    LEVELS=(1 2 3 4 5 6)
fi

for HSK in "${LEVELS[@]}"
do
    echo ""
    echo "======================================="
    echo "Processing HSK${HSK} (${LANG_DIR})"
    echo "======================================="

    CSV="Translations/processed/${LANGUAGE}/HSK${HSK}_processed.csv"

    if [ ! -f "$CSV" ]; then
        echo "WARNING: $CSV non trovato, salto HSK${HSK}" >&2
        continue
    fi

    mkdir -p "decks/${LANG_DIR}/New_HSK${HSK}"

    for TYPE in Audio Francais Hanzi
    do
        INPUT="decks/French/New_HSK${HSK}/New_HSK${HSK}_${TYPE}.apkg"

        if [ "${TYPE}" = "Francais" ]; then
            OUTPUT="decks/${LANG_DIR}/New_HSK${HSK}/New_HSK${HSK}_${LANG_DIR}.apkg"
        else
            OUTPUT="decks/${LANG_DIR}/New_HSK${HSK}/New_HSK${HSK}_${TYPE}.apkg"
        fi

        echo ""
        echo "Input : $INPUT"
        echo "CSV   : $CSV"
        echo "Output: $OUTPUT"

        uv run TranslationScript/compressor_apkg.py \
            "$INPUT" \
            "$CSV" \
            "$OUTPUT" \
            "$LANGUAGE"
    done
done

echo ""
echo "Done."