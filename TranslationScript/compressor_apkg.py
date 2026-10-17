#!/usr/bin/env python3

import argparse
import csv
import hashlib
import json
import sqlite3
import tempfile
import zipfile
from pathlib import Path

# Come si chiamano, nella lingua di destinazione, i termini francesi del mazzo originale.
LANGUAGES = {
    "english":    {"label": "English",   "chinese": "Chinese",    "vocabulary": "Chinese Vocabulary"},
    "italian":    {"label": "Italiano",  "chinese": "Cinese",     "vocabulary": "Vocabolario Cinese"},
    "spanish":    {"label": "Español",   "chinese": "Chino",      "vocabulary": "Vocabulario Chino"},
    "german":     {"label": "Deutsch",   "chinese": "Chinesisch", "vocabulary": "Chinesisches Vokabular"},
    "portuguese": {"label": "Português", "chinese": "Chinês",     "vocabulary": "Vocabulário Chinês"},
}


def build_entry_id(hanzi, pinyin):
    data = hanzi.strip() + "::" + pinyin.strip()
    return hashlib.sha1(data.encode("utf-8")).hexdigest()[:12]


def load_translations(csv_file):
    translations = {}
    with open(csv_file, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            translations[row["entry_id"].strip()] = row
    return translations


def find_db(extract_dir):
    for name in ("collection.anki21", "collection.anki2"):
        db = Path(extract_dir) / name
        if db.exists():
            return db
    raise RuntimeError("Collection database not found")


def build_replacements(language, label=None, chinese=None, vocabulary=None):
    """Lista (vecchio, nuovo). L'ordine conta: prima la stringa più lunga."""
    preset = LANGUAGES.get(language.lower(), {})

    label = label or preset.get("label") or language.capitalize()
    chinese = chinese or preset.get("chinese")
    vocabulary = vocabulary or preset.get("vocabulary")

    replacements = []

    if vocabulary:
        replacements.append(("Vocabulaire Chinois", vocabulary))
    else:
        print(f"WARNING: nessun nome per 'Vocabulaire Chinois' ({language}), usa --vocabulary")

    replacements.append(("Français", label))

    if chinese:
        replacements.append(("Chinois", chinese))
    else:
        print(f"WARNING: nessun nome per 'Chinois' ({language}), usa --chinese")

    return replacements


def apply_replacements(name, replacements):
    for old, new in replacements:
        name = name.replace(old, new)
    return name


def update_model_names(cur, replacements):
    row = cur.execute("SELECT models, decks FROM col").fetchone()

    models = json.loads(row[0])
    decks = json.loads(row[1])

    for model in models.values():
        model["name"] = apply_replacements(model["name"], replacements)

    for deck in decks.values():
        deck["name"] = apply_replacements(deck["name"], replacements)

    cur.execute(
        "UPDATE col SET models=?, decks=?",
        (
            json.dumps(models, ensure_ascii=False),
            json.dumps(decks, ensure_ascii=False),
        ),
    )


def main():
    parser = argparse.ArgumentParser(description="Applica traduzioni a un mazzo .apkg")
    parser.add_argument("input_apkg")
    parser.add_argument("translations_csv")
    parser.add_argument("output_apkg")
    parser.add_argument("language", help="es. english, italian, spanish... (anche lingue non in tabella)")
    parser.add_argument("--label", help="sostituisce 'Français' (default: dalla tabella o il nome della lingua)")
    parser.add_argument("--chinese", help="sostituisce 'Chinois'")
    parser.add_argument("--vocabulary", help="sostituisce 'Vocabulaire Chinois'")
    args = parser.parse_args()

    replacements = build_replacements(
        args.language, args.label, args.chinese, args.vocabulary
    )
    translations = load_translations(args.translations_csv)
    applied = 0

    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(args.input_apkg) as z:
            z.extractall(tmp)

        db = find_db(tmp)
        conn = sqlite3.connect(db)
        cur = conn.cursor()

        notes = cur.execute("SELECT id, flds FROM notes").fetchall()

        for note_id, flds in notes:
            fields = flds.split("\x1f")
            if len(fields) < 4:
                continue

            pinyin = fields[1].strip()
            hanzi = fields[2].strip()
            entry_id = build_entry_id(hanzi, pinyin)

            if entry_id not in translations:
                continue

            row = translations[entry_id]
            translation_word = row["translation_word"].strip()
            translation_sentence = row["translation_sentence"].strip()
            changed = False

            if translation_word:
                fields[0] = translation_word
                changed = True

            if translation_sentence:
                parts = fields[3].split(" - ")
                if len(parts) >= 3:
                    parts[-1] = translation_sentence
                    fields[3] = " - ".join(parts)
                    changed = True

            if changed:
                cur.execute(
                    "UPDATE notes SET flds=? WHERE id=?",
                    ("\x1f".join(fields), note_id),
                )
                applied += 1

        update_model_names(cur, replacements)

        conn.commit()
        conn.close()

        with zipfile.ZipFile(args.output_apkg, "w", zipfile.ZIP_DEFLATED) as z:
            for file in Path(tmp).rglob("*"):
                z.write(file, file.relative_to(tmp))

    print(f"Applied translations to {applied} notes")
    print(f"Created: {args.output_apkg}")


if __name__ == "__main__":
    main()