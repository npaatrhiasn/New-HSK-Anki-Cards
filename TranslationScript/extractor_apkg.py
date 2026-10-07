#!/usr/bin/env python3

import csv
import hashlib
import sqlite3
import tempfile
import zipfile

from pathlib import Path


def find_db(extract_dir):

    for name in (
        "collection.anki21",
        "collection.anki2",
    ):

        candidate = Path(extract_dir) / name

        if candidate.exists():
            return candidate

    raise RuntimeError(
        "Collection database not found"
    )


def detect_deck_type(filename):

    name = filename.lower()

    if "audio" in name:
        return "Audio"

    if "hanzi" in name:
        return "Hanzi"

    if "francais" in name:
        return "Francais"

    return "Unknown"


def detect_hsk(path):

    parts = Path(path).parts

    for part in parts:

        if part.startswith("New HSK"):

            return (
                part
                .replace("New ", "")
                .replace(" ", "")
            )

    return "Unknown"


def build_entry_id(
    hanzi,
    pinyin
):

    data = (
        hanzi
        + "::"
        + pinyin
    )

    return hashlib.sha1(
        data.encode("utf-8")
    ).hexdigest()[:12]


def extract_rows(apkg):

    deck_type = detect_deck_type(
        Path(apkg).name
    )

    deck_level = detect_hsk(apkg)

    rows_out = []

    with tempfile.TemporaryDirectory() as tmp:

        with zipfile.ZipFile(apkg) as z:

            z.extractall(tmp)

        db = find_db(tmp)

        conn = sqlite3.connect(db)

        cur = conn.cursor()

        rows = cur.execute(
            """
            SELECT flds
            FROM notes
            """
        ).fetchall()

        conn.close()

        for (flds,) in rows:

            fields = flds.split("\x1f")

            if len(fields) < 4:
                continue

            french_word = fields[0].strip()

            pinyin = fields[1].strip()

            hanzi = fields[2].strip()

            example = fields[3].strip()

            chinese_sentence = ""
            pinyin_sentence = ""
            french_sentence = ""

            parts = example.split(" - ")

            if len(parts) >= 3:

                chinese_sentence = parts[0].strip()

                pinyin_sentence = parts[1].strip()

                french_sentence = (
                    " - ".join(parts[2:])
                    .strip()
                )

            entry_id = build_entry_id(
                hanzi,
                pinyin
            )

            rows_out.append({

                "deck_level":
                    deck_level,

                "deck_type":
                    deck_type,

                "entry_id":
                    entry_id,

                "french_word":
                    french_word,

                "pinyin":
                    pinyin,

                "hanzi":
                    hanzi,

                "chinese_sentence":
                    chinese_sentence,

                "pinyin_sentence":
                    pinyin_sentence,

                "french_sentence":
                    french_sentence,

                "translation_word":
                    "",

                "translation_sentence":
                    "",
            })

    return rows_out


def write_csv(
    rows,
    output_file
):

    fieldnames = [

        "deck_level",
        "deck_type",
        "entry_id",

        "french_word",

        "pinyin",
        "hanzi",

        "chinese_sentence",
        "pinyin_sentence",
        "french_sentence",

        "translation_word",
        "translation_sentence",
    ]

    with open(
        "Translations/Unprocessed/" + output_file,
        "w",
        newline="",
        encoding="utf-8",
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames
        )

        writer.writeheader()

        writer.writerows(rows)


def main():

    import sys

    if len(sys.argv) != 2:

        print(
            "Usage:"
        )

        print(
            "python extractor_rich_v2.py deck.apkg"
        )

        return

    apkg = sys.argv[1]

    rows = extract_rows(apkg)

    output_file = (
        Path(apkg).stem
        + "_unprocessed.csv"
    )

    write_csv(
        rows,
        output_file
    )

    print(
        f"Extracted {len(rows)} notes"
    )

    print(
        f"Created {output_file}"
    )


if __name__ == "__main__":
    main()