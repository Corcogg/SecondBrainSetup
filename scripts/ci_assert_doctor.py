#!/usr/bin/env python3
"""
ci_assert_doctor.py — assert a doctor --json report is green on every check
that CI can legitimately verify.

CI installs with --skip-mcp --skip-hooks --skip-index and stub API keys, so the
MCP-registration and hooks checks are expected red and are ignored here.
Everything else must be ok.

Usage: python ci_assert_doctor.py <doctor.json>
Exit 0 iff all required checks are ok.
"""
import json
import sys

IGNORED_PREFIXES = (
    "MCP registered",
    "hooks installed",
)


def main() -> int:
    report = json.load(open(sys.argv[1], encoding="utf-8"))
    failed = []
    for c in report["checks"]:
        if c["name"].startswith(IGNORED_PREFIXES):
            print(f"  (ignored) {c['name']}: ok={c['ok']} {c['detail']}")
            continue
        marker = "OK " if c["ok"] else "RED"
        print(f"  {marker} {c['name']}: {c['detail']}")
        if not c["ok"]:
            failed.append(c["name"])
    if failed:
        print(f"\nci_assert_doctor: {len(failed)} required check(s) red: {failed}")
        return 1
    print("\nci_assert_doctor: all required checks green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
