#!/usr/bin/env python3
"""Minimal offline lookup demo. Usage: python3 lookup.py WORD."""
from contextlib import closing
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
LEXICAL_FIELDS = ('word', 'ipa', 'cefr', 'entries')
TEXT_FIELDS = ('definition_en', 'definition_cn', 'example_en', 'example_cn')
CACHE_SCHEMA = 3


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False)


def jsonlines(path):
    with Path(path).open(encoding='utf-8') as stream:
        for line_number, line in enumerate(stream, 1):
            try:
                yield json.loads(line)
            except ValueError as error:
                raise ValueError(f'{path}:{line_number}: invalid JSON') from error


def validate_record(record):
    if not isinstance(record, dict):
        raise ValueError('Dictionary record must be an object')
    for name in LEXICAL_FIELDS:
        if name not in record:
            raise ValueError(f'Missing lexical field: {name}')
    word = record['word']
    if not isinstance(word, str) or not word or any(ord(c) < 32 for c in word):
        raise ValueError('Invalid headword')
    if not all(isinstance(record[k], str) for k in ('ipa', 'cefr')):
        raise ValueError(f'{word}: invalid word metadata')
    if not isinstance(record['entries'], list) or not record['entries']:
        raise ValueError(f'{word}: empty inventory')
    for entry in record['entries']:
        if not isinstance(entry, dict):
            raise ValueError(f'{word}: invalid sense')
        for name in ('pos', *TEXT_FIELDS):
            if not isinstance(entry.get(name), str) or not entry[name].strip():
                raise ValueError(f'{word}: missing {name}')


def source_identity(data):
    """Detect ordinary edits, replacements, and a different source file cheaply."""
    data = Path(data).resolve()
    stat = data.stat()
    return canonical([str(data), stat.st_dev, stat.st_ino, stat.st_size,
                      stat.st_mtime_ns, stat.st_ctime_ns])


def build_index(data, database):
    """Build a disposable cache atomically; leave any previous cache on failure."""
    data, database = Path(data), Path(database)
    if data.resolve() == database.resolve():
        raise ValueError('Database cache must not overwrite the dictionary JSONL')
    identity = source_identity(data)
    database.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.dictionary-', suffix='.sqlite3', dir=database.parent)
    os.close(fd)
    temporary = Path(name)
    count = senses = visible = 0
    try:
        with closing(sqlite3.connect(temporary)) as db, db:
            db.executescript(f"""
                PRAGMA page_size=4096;
                PRAGMA user_version={CACHE_SCHEMA};
                CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL) WITHOUT ROWID;
                CREATE TABLE words(word TEXT PRIMARY KEY COLLATE BINARY,
                    folded TEXT NOT NULL COLLATE BINARY, payload TEXT NOT NULL) WITHOUT ROWID;
            """)
            for record in jsonlines(data):
                validate_record(record)
                word = record['word']
                try:
                    db.execute('INSERT INTO words VALUES (?,?,?)',
                               (word, word.casefold(), canonical(record)))
                except sqlite3.IntegrityError as error:
                    raise ValueError('Duplicate headword: '+word) from error
                count += 1
                senses += len(record['entries'])
                visible += min(6, len(record['entries']))
            if not count:
                raise ValueError('Dictionary is empty')
            db.execute('CREATE INDEX words_folded ON words(folded,word)')
            db.execute('INSERT INTO metadata VALUES (?,?)', ('source_identity', identity))
            if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise ValueError('SQLite integrity check failed')
        if source_identity(data) != identity:
            raise ValueError('Dictionary changed while building the cache; retry lookup')
        os.replace(temporary, database)
    finally:
        temporary.unlink(missing_ok=True)
    return {'words': count, 'senses': senses, 'displayed_senses': visible}


def connect_readonly(database):
    return sqlite3.connect(Path(database).resolve().as_uri()+'?mode=ro', uri=True)


def ensure_index(data, database):
    identity = source_identity(data)
    try:
        with closing(connect_readonly(database)) as db:
            actual = db.execute("SELECT value FROM metadata WHERE key='source_identity'").fetchone()
            if db.execute('PRAGMA user_version').fetchone()[0] == CACHE_SCHEMA and actual == (identity,):
                if db.execute('SELECT 1 FROM words LIMIT 1').fetchone():
                    return
    except sqlite3.Error:
        pass
    build_index(data, database)


def find_word(db, word):
    row = db.execute('SELECT payload FROM words WHERE word=?', (word,)).fetchone()
    if row:
        return row, []
    alternatives = db.execute('SELECT word,payload FROM words WHERE folded=? ORDER BY word',
                              (word.casefold(),)).fetchall()
    if len(alternatives) == 1:
        return alternatives[0][1:], []
    return None, [r[0] for r in alternatives]


def selected_record(row):
    record = json.loads(row[0])
    record['entries'] = record['entries'][:6]
    return record


def main():
    if len(sys.argv) != 2:
        print('Usage: python3 lookup.py WORD', file=sys.stderr)
        return 2
    word = sys.argv[1]
    data = ROOT/'dict.jsonl'
    database = ROOT/'.cache/dict.sqlite3'
    try:
        ensure_index(data, database)
        with closing(connect_readonly(database)) as db:
            row, alternatives = find_word(db, word)
            if row is None:
                message = 'Ambiguous capitalization; use: '+', '.join(alternatives) if alternatives else 'Word not found: '+word
                print(message, file=sys.stderr)
                return 2
            print(json.dumps(selected_record(row), ensure_ascii=False, indent=2))
    except (OSError, ValueError, KeyError, sqlite3.Error) as error:
        print(f'Lookup failed: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
