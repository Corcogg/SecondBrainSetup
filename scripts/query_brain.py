#!/usr/bin/env python3
"""
query_brain.py — CLI interface for second-brain semantic search.

Usage:
  python3 query_brain.py "project physics model"
  python3 query_brain.py "design preferences" --domain projects
  python3 query_brain.py "what do I know about AI behavior" --xml
  python3 query_brain.py "config notes" --raw
  python3 query_brain.py "some topic" --domain projects --n 5

Flags:
  --domain   Pre-filter by domain (configured in brain_config.json)
  --n        Number of results (default 8)
  --xml      Output XML block for Claude context injection
  --raw      Output raw JSON
"""

import os
import sys
import json
import argparse
from pathlib import Path

import voyageai

sys.path.insert(0, str(Path(__file__).resolve().parent))
import brain_config
from brain_vector import get_collection, query_brain, format_for_injection

DOMAINS = set(brain_config.DOMAINS)


def main():
    parser = argparse.ArgumentParser(description="Query the second-brain vector store")
    parser.add_argument("query", nargs="+", help="Search query")
    parser.add_argument("--domain", type=str, default=None,
                        choices=list(DOMAINS), help="Filter by domain")
    parser.add_argument("--n", type=int, default=8, help="Number of results")
    parser.add_argument("--xml",  action="store_true", help="Output Claude injection XML")
    parser.add_argument("--raw",  action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    api_key = os.environ.get("VOYAGE_API_KEY")
    if not api_key:
        print("ERROR: VOYAGE_API_KEY not set in environment.")
        sys.exit(1)

    query_text = " ".join(args.query)
    vc         = voyageai.Client(api_key=api_key)
    collection = get_collection()

    if collection.count() == 0:
        print("ERROR: Index is empty. Run build_index.py first.")
        sys.exit(1)

    hits = query_brain(vc, collection, query_text, domain=args.domain, n=args.n)

    if not hits:
        print("No results found.")
        sys.exit(0)

    # ── Output modes ──────────────────────────────────────────────────────────

    if args.raw:
        print(json.dumps(hits, indent=2))
        return

    if args.xml:
        print(format_for_injection(hits))
        return

    # ── Human-readable default ────────────────────────────────────────────────
    domain_label = f" [{args.domain}]" if args.domain else ""
    print(f"\nQuery: \"{query_text}\"{domain_label}")
    print(f"Results: {len(hits)}\n")
    print("─" * 70)

    for i, h in enumerate(hits, 1):
        print(f"\n[{i}] {h['title']}")
        print(f"    domain={h['domain']}  type={h['type']}  "
              f"similarity={h['sim']:.3f}  rrf={h['score']:.4f}")
        if h["summary"]:
            print(f"    {h['summary']}")
        # Show first 200 chars of body
        snippet = h["text"][:200].replace("\n", " ").strip()
        if len(h["text"]) > 200:
            snippet += "..."
        print(f"    → {snippet}")

    print("\n" + "─" * 70)


if __name__ == "__main__":
    main()
