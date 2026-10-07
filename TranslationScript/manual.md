uv run --with pandas --with deep-translator TranslationScript/processor_translator.py "Translations/Unprocessed/AnkiCards_Audio_2026-09-02_16-48_['New HSK1']_unprocessed.csv" > "Translations/Processed/ForEnglish/AnkiCards_Audio_2026-09-02_16-49_['New HSK1']_processed.csv"

and so on (need automated script)



# extraction

automated script

# Compression

uv run TranslationScript/compressor_apkg.py \
decks/french/HSK3/HSK3_Francais.apkg \
Translations/processed/english/HSK3_Francais_processed.csv \
decks/english/HSK3/HSK3_English.apkg \
english