#!/usr/bin/env bash

# da eseguire nella root dir!! così: ./Translations/scripts/automatic_compressor_english.sh

set -euo pipefail

for HSK in 1 2 3
do
    echo ""
    echo "======================================="
    echo "Processing HSK${HSK}"
    echo "======================================="

    CSV="Translations/processed/italian/HSK${HSK}_processed.csv"

    LANG="Italian"
    mkdir -p "decks/${LANG}/New_HSK${HSK}"

    for TYPE in Audio Francais Hanzi
    do
        INPUT="decks/French/New_HSK${HSK}/New_HSK${HSK}_${TYPE}.apkg"

        if [ "${TYPE}" = "Francais" ]; then
            OUTPUT="decks/${LANG}/New_HSK${HSK}/New_HSK${HSK}_${LANG}.apkg"
        else
            OUTPUT="decks/${LANG}/New_HSK${HSK}/New_HSK${HSK}_${TYPE}.apkg"
        fi

        echo ""
        echo "Input : $INPUT"
        echo "CSV   : $CSV"
        echo "Output: $OUTPUT"

        uv run TranslationScript/compressor_apkg.py \
            "$INPUT" \
            "$CSV" \
            "$OUTPUT" \
            italian
    done
done

echo ""
echo "Done."