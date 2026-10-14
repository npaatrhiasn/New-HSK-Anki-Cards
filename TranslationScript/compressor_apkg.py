#!/usr/bin/env python3

import csv
import hashlib
import json
import sqlite3
import tempfile
import zipfile

from pathlib import Path


def build_entry_id(
    hanzi,
    pinyin
):

    data = (
        hanzi.strip()
        + "::"
        + pinyin.strip()
    )

    return hashlib.sha1(
        data.encode("utf-8")
    ).hexdigest()[:12]


def load_translations(csv_file):

    translations = {}

    with open(
        csv_file,
        newline="",
        encoding="utf-8",
    ) as f:

        reader = csv.DictReader(f)

        for row in reader:

            entry_id = row[
                "entry_id"
            ].strip()

            translations[
                entry_id
            ] = row

    return translations


def find_db(extract_dir):

    for name in (
        "collection.anki21",
        "collection.anki2",
    ):

        db = Path(extract_dir) / name

        if db.exists():
            return db

    raise RuntimeError(
        "Collection database not found"
    )


def update_model_names(
    cur,
    language,
):

    row = cur.execute(
        """
        SELECT models, decks
        FROM col
        """
    ).fetchone()

    models = json.loads(row[0])
    decks = json.loads(row[1])

    language = language.lower()

    for model in models.values():

        if language == "english":

            model["name"] = (
                model["name"]
                .replace(
                    "Français",
                    "English"
                )
                .replace(
                    "Chinois",
                    "Chinese"
                )
            )

        elif language == "italian":

            model["name"] = (
                model["name"]
                .replace(
                    "Français",
                    "Italiano"
                )
                .replace(
                    "Chinois",
                    "Cinese"
                )
            )

    for deck in decks.values():

        if language == "english":

            deck["name"] = (
                deck["name"]
                .replace(
                    "Français",
                    "English"
                )
                .replace(
                    "Vocabulaire Chinois",
                    "Chinese Vocabulary"
                )
            )

        elif language == "italian":

            deck["name"] = (
                deck["name"]
                .replace(
                    "Vocabulaire Chinois",
                    "Vocabolario Cinese"
                )
                .replace(
                    "Français",
                    "Italiano"
                )
            )

    cur.execute(
        """
        UPDATE col
        SET models=?,
            decks=?
        """,
        (
            json.dumps(
                models,
                ensure_ascii=False
            ),
            json.dumps(
                decks,
                ensure_ascii=False
            ),
        )
    )


def main():

    import sys

    if len(sys.argv) != 5:

        print(
            "Usage:"
        )

        print(
            "python compressor.py "
            "deck.apkg "
            "translations.csv "
            "output.apkg "
            "[english|italian]"
        )

        return

    input_apkg = sys.argv[1]
    csv_file = sys.argv[2]
    output_apkg = sys.argv[3]
    language = sys.argv[4]

    translations = load_translations(
        csv_file
    )

    applied = 0

    with tempfile.TemporaryDirectory() as tmp:

        with zipfile.ZipFile(
            input_apkg
        ) as z:

            z.extractall(tmp)

        db = find_db(tmp)

        conn = sqlite3.connect(db)

        cur = conn.cursor()

        notes = cur.execute(
            """
            SELECT id, flds
            FROM notes
            """
        ).fetchall()

        for note_id, flds in notes:

            fields = flds.split("\x1f")

            if len(fields) < 4:
                continue

            pinyin = fields[1].strip()
            hanzi = fields[2].strip()

            entry_id = build_entry_id(
                hanzi,
                pinyin
            )

            if (
                entry_id
                not in translations
            ):
                continue

            row = translations[
                entry_id
            ]

            translation_word = (
                row[
                    "translation_word"
                ].strip()
            )

            translation_sentence = (
                row[
                    "translation_sentence"
                ].strip()
            )

            changed = False

            if translation_word:

                fields[0] = (
                    translation_word
                )

                changed = True

            if translation_sentence:

                parts = (
                    fields[3]
                    .split(" - ")
                )

                if len(parts) >= 3:

                    parts[-1] = (
                        translation_sentence
                    )

                    fields[3] = (
                        " - ".join(parts)
                    )

                    changed = True

            if changed:

                cur.execute(
                    """
                    UPDATE notes
                    SET flds=?
                    WHERE id=?
                    """,
                    (
                        "\x1f".join(
                            fields
                        ),
                        note_id,
                    ),
                )

                applied += 1

        update_model_names(
            cur,
            language,
        )

        conn.commit()
        conn.close()

        with zipfile.ZipFile(
            output_apkg,
            "w",
            zipfile.ZIP_DEFLATED,
        ) as z:

            for file in Path(
                tmp
            ).rglob("*"):

                z.write(
                    file,
                    file.relative_to(
                        tmp
                    )
                )

    print(
        f"Applied translations to "
        f"{applied} notes"
    )

    print(
        f"Created: {output_apkg}"
    )


if __name__ == "__main__":
    main()
