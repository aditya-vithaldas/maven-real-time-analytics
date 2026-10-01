"""Check local data and optionally verify Gemini access without generation."""
import argparse
import os
from pathlib import Path

import duckdb
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gemini", action="store_true", help="List models to check the API key")
    args = parser.parse_args()
    load_dotenv(ROOT / ".env")
    path = Path(os.environ.get("DUCKDB_PATH", "./data/ecommerce.duckdb"))
    if not path.is_absolute():
        path = ROOT / path
    with duckdb.connect(str(path), read_only=True) as db:
        tables = db.execute("SHOW TABLES").fetchall()
        total = 0
        for (name,) in tables:
            escaped = name.replace('"', '""')
            count = db.execute(f'SELECT count(*) FROM "{escaped}"').fetchone()[0]
            total += count
            print(f"{name}: {count:,} rows")
        start, end, days = db.execute("SELECT min(date), max(date), count(*) FROM calendar").fetchone()
        print(f"Period: {start} through {end} ({days} days)")
        print(f"Total: {total:,} rows")
        assert total == 10_000_000, "Unexpected dataset size"
        assert str(start) == "2025-09-30" and str(end) == "2026-09-29", "Unexpected dataset period"
        revenue = db.execute("SELECT sum(net_amount) FROM orders WHERE status = 'completed'").fetchone()[0]
        print(f"Completed sales: USD {revenue:,.2f}")
    if args.gemini:
        from google import genai
        key = os.environ.get("GEMINI_API_KEY")
        if not key:
            raise SystemExit("GEMINI_API_KEY is missing")
        with genai.Client(api_key=key) as client:
            models = list(client.models.list())
        print(f"Gemini access verified: {len(models)} models available")


if __name__ == "__main__":
    main()
