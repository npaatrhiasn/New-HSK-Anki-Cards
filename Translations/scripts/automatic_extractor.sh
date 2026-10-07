#!/usr/bin/env bash

set -euo pipefail

find "For French" \
    -type f \
    -name "*.apkg" \
    | sort \
    | while read -r file
do
    echo
    echo "========================================"
    echo "Processing:"
    echo "$file"
    echo "========================================"

    uv run TranslationScript/extractor_apkg.py "$file"
done

echo
echo "Done."