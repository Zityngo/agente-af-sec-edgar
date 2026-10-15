from __future__ import annotations
import sqlite3
from pathlib import Path
SCHEMA = Path(__file__).with_name("schema.sql")

def connect_rw(path):
    con = sqlite3.connect(str(path)); con.row_factory = sqlite3.Row
    con.executescript(SCHEMA.read_text(encoding="utf-8")); return con

def connect_ro(path):
    """Apertura de solo lectura: la app nunca puede escribir."""
    con = sqlite3.connect(f"file:{Path(path).resolve()}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row; return con
