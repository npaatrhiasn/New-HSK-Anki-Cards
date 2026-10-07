#!/usr/bin/env python3
"""
processor.py — Completa le colonne translation_word e translation_sentence
traducendo dal francese all'inglese. Prende un solo input (CSV unprocessed)
e produce un solo output (CSV processed).

Uso:
    python processor.py input.csv output.csv
    python processor.py input.csv > output.csv   (se --stdout)
"""

import argparse
import csv
import sys
import time
from pathlib import Path

import pandas as pd
from deep_translator import GoogleTranslator


def translate_fr_en(translator, text, cache):
    text = "" if pd.isna(text) else str(text).strip()
    if not text:
        return ""
    if text in cache:
        return cache[text]
    try:
        out = translator.translate(text)
        cache[text] = out
        time.sleep(0.15)  # evita rate limit di Google
        return out
    except Exception as e:
        print(f"[WARN] Traduzione fallita per {text!r}: {e}", file=sys.stderr)
        return ""


def process(input_path: Path, output_path: Path | None):
    df = pd.read_csv(input_path, dtype=str, keep_default_na=False)

    for col in ["translation_word", "translation_sentence"]:
        if col not in df.columns:
            df[col] = ""

    translator = GoogleTranslator(source="fr", target="en")
    cache = {}

    total = len(df)
    for idx, row in df.iterrows():
        if not str(row.get("translation_word", "")).strip():
            df.at[idx, "translation_word"] = translate_fr_en(
                translator, row.get("french_word", ""), cache
            )
        if not str(row.get("translation_sentence", "")).strip():
            df.at[idx, "translation_sentence"] = translate_fr_en(
                translator, row.get("french_sentence", ""), cache
            )
        print(f"  [{idx + 1}/{total}] elaborato", file=sys.stderr)

    if output_path is None:
        # stdout: utile per redirect con >
        df.to_csv(sys.stdout, index=False, encoding="utf-8-sig",
                  quoting=csv.QUOTE_MINIMAL)
    else:
        df.to_csv(output_path, index=False, encoding="utf-8-sig",
                  quoting=csv.QUOTE_MINIMAL)
        print(f"[OK] Creato: {output_path}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description="Traduce dal francese all'inglese le colonne mancanti di un CSV Anki."
    )
    parser.add_argument("input", type=Path, help="CSV unprocessed di input")
    parser.add_argument(
        "output",
        type=Path,
        nargs="?",
        default=None,
        help="CSV processed di output (se omesso, scrive su stdout)",
    )
    args = parser.parse_args()

    if not args.input.exists():
        print(f"[ERRORE] File non trovato: {args.input}", file=sys.stderr)
        sys.exit(1)

    process(args.input, args.output)


if __name__ == "__main__":
    main()