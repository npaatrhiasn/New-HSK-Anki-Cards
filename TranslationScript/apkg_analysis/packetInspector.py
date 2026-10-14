#!/usr/bin/env python3

import json
import sqlite3
import tempfile
import zipfile
from pathlib import Path
import sys


def print_header(title):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def find_collection_file(extract_dir):
    for name in ("collection.anki21", "collection.anki2"):
        path = Path(extract_dir) / name
        if path.exists():
            return path
    return None


def inspect_database(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    print_header("SQLITE TABLES")

    tables = cur.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type='table'
        ORDER BY name
    """).fetchall()

    for (table,) in tables:
        print(table)

    for (table,) in tables:
        print_header(f"TABLE: {table}")

        try:
            columns = cur.execute(
                f"PRAGMA table_info({table})"
            ).fetchall()

            print("Columns:")
            for col in columns:
                print(f"  {col[1]} ({col[2]})")

            rows = cur.execute(
                f"SELECT * FROM {table} LIMIT 3"
            ).fetchall()

            print("\nSample rows:")
            for row in rows:
                print(row)

        except Exception as e:
            print(f"Error: {e}")

    print_header("DECKS")

    try:
        decks_json = cur.execute(
            "SELECT decks FROM col"
        ).fetchone()[0]

        decks = json.loads(decks_json)

        for deck_id, deck in decks.items():
            print(f"{deck_id}: {deck['name']}")

    except Exception as e:
        print(f"Unable to read decks: {e}")

    print_header("NOTES PREVIEW")

    try:
        notes = cur.execute("""
            SELECT id, flds
            FROM notes
            LIMIT 20
        """).fetchall()

        for note_id, fields in notes:
            print("-" * 40)
            print(f"NOTE ID: {note_id}")

            split_fields = fields.split("\x1f")

            for idx, field in enumerate(split_fields):
                print(f"Field {idx}:")
                print(field[:300])

    except Exception as e:
        print(f"Unable to read notes: {e}")

    conn.close()


def inspect_apkg(apkg_path):
    print_header(f"INSPECTING {apkg_path}")

    with tempfile.TemporaryDirectory() as tmpdir:

        with zipfile.ZipFile(apkg_path, "r") as zf:
            zf.extractall(tmpdir)

            print_header("ARCHIVE CONTENTS")

            for name in sorted(zf.namelist()):
                print(name)

        db_file = find_collection_file(tmpdir)

        if not db_file:
            print("\nNo collection database found.")
            return

        print_header("DATABASE FILE")
        print(db_file)

        inspect_database(db_file)

        media_file = Path(tmpdir) / "media"

        if media_file.exists():
            print_header("MEDIA")

            try:
                media = json.loads(media_file.read_text())

                print(f"Total media files: {len(media)}")

                for k, v in list(media.items())[:20]:
                    print(f"{k} -> {v}")

            except Exception as e:
                print(f"Unable to parse media file: {e}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} file.apkg")
        sys.exit(1)

    apkg_path = Path(sys.argv[1])

    if not apkg_path.exists():
        print(f"File not found: {apkg_path}")
        sys.exit(1)

    if apkg_path.is_dir():
        print(f"Expected an .apkg file, got directory: {apkg_path}")
        sys.exit(1)

    inspect_apkg(str(apkg_path))