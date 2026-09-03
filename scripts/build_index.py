#!/usr/bin/env python3
"""
build_index.py — One-time script to embed all existing second-brain notes.

Run this once after setting up Voyage AI to populate the ChromaDB vector store.
Subsequently, brain_watcher.py keeps the index fresh automatically.

Usage:
  python3 build_index.py
  python3 build_index.py --force   # re-embed all notes even if unchanged
"""

import os
import sys
import time
import argparse
from pathlib import Path

import voyageai

sys.path.insert(0, str(Path(__file__).resolve().parent))
import brain_config
from brain_vector import VAULT_ROOT, embed_note, get_collection

RATE_LIMIT_SLEEP = 0.35  # ~3 req/sec — stay under Voyage free tier limit


def main():
    parser = argparse.ArgumentParser(description="Build second-brain vector index")
    parser.add_argument("--force", action="store_true",
                        help="Re-embed all notes even if content hash unchanged")
    args = parser.parse_args()

    api_key = os.environ.get("VOYAGE_API_KEY")
    if not api_key:
        print("ERROR: VOYAGE_API_KEY not set in environment.")
        sys.exit(1)

    vc         = voyageai.Client(api_key=api_key)
    collection = get_collection()

    notes = sorted(VAULT_ROOT.rglob("*.md"))
    notes = [n for n in notes if ".obsidian" not in str(n)]

    print(f"Indexing {len(notes)} notes into {collection.name}...\n")

    embedded = skipped = errors = 0

    for i, note in enumerate(notes, 1):
        label = f"[{i:>3}/{len(notes)}] {note.stem:<45}"
        try:
            did_embed = embed_note(vc, collection, note, force=args.force)
            if did_embed:
                print(f"  ✓ {label}")
                embedded += 1
                time.sleep(RATE_LIMIT_SLEEP)
            else:
                print(f"  — {label} (unchanged, skipped)")
                skipped += 1
        except Exception as e:
            print(f"  ✗ {label} ERROR: {e}")
            errors += 1

    print(f"\n{'='*60}")
    print(f"Done.  Embedded: {embedded}  |  Skipped: {skipped}  |  Errors: {errors}")
    print(f"Index stored at: {brain_config.CHROMA_PATH}")
    print(f"\nTo query: python3 query_brain.py \"your question here\"")


if __name__ == "__main__":
    main()
