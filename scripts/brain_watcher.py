#!/usr/bin/env python3
"""
brain_watcher.py — Auto-linker for the second brain vault.

Watches <vault>/memory/ for new or modified .md notes.
When a note changes, calls Claude API (forced tool-use structured output) to:
  1. Add/update YAML frontmatter if missing
  2. Inject validated [[wikilinks]] into the note body (candidates come from
     vector retrieval over the Chroma collection)
  3. Embed the note into the Chroma vector store

High-confidence links (Claude states clear reason) are applied automatically.
A macOS notification is shown for each note processed (if enabled).

The watcher is the SOLE Chroma writer. A built-in reconcile thread runs at
startup and every 6h of uptime: re-embeds changed notes, prunes orphans,
stamps <vault>/.last_reconcile, and auto-commits the vault git repo.

Deletes are handled with a delayed verification (~2s): macOS FSEvents can
deliver a delete event after the file has already been re-created, so the
Chroma eviction only happens if the file is still gone after the grace period.
Renames (on_moved) evict the old stem and re-index the new path.

Usage:
  python3 brain_watcher.py           # Run watcher (file logs only)
  python3 brain_watcher.py --verbose # Also mirror logs to stdout

Requirements:
  pip3 install watchdog anthropic
"""

import os
import re
import sys
import time
import signal
import hashlib
import logging
import argparse
import subprocess
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime
from threading import Timer, Lock, Thread

import anthropic
import voyageai
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

sys.path.insert(0, str(Path(__file__).resolve().parent))
import brain_config
import brain_platform
from brain_vector import (
    EMBED_DIM, EMBED_MODEL, embed_note, get_collection, get_collection_dim,
    get_link_candidates,
)

VAULT_ROOT       = brain_config.VAULT_MEMORY
LOG_FILE         = brain_config.LOG_FILE
DEBOUNCE_SEC     = 4.0    # wait this long after last edit before processing
DELETE_VERIFY_SEC = 2.0   # wait this long after a delete event before evicting from Chroma
SKIP_STEMS       = {"link_review"}  # never auto-process these files

# Reconcile: periodic vault hygiene. The watcher is the sole Chroma writer.
VAULT_GIT_ROOT       = brain_config.VAULT_DIR
LAST_RECONCILE_FILE  = brain_config.LAST_RECONCILE_FILE
RECONCILE_INTERVAL_SEC = 6 * 60 * 60  # 6 hours of process uptime
RECONCILE_RATE_LIMIT_SLEEP = 0.35     # stay under Voyage free-tier rate

# Only the RotatingFileHandler writes — launchd redirects stdout/stderr to the same log,
# so adding a StreamHandler would double-log every line in the file.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[RotatingFileHandler(LOG_FILE, maxBytes=1_000_000, backupCount=3)]
)
log = logging.getLogger(__name__)

# Suppress spammy INFO logs from dependencies.
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# Self-write mute: hash of content we wrote, keyed by path. If the file's
# current hash still matches what we wrote, the pending event is our echo
# (skip). If it differs, a user edit raced in — process it. Hash-based so the
# mute never hides a legitimate user edit regardless of timing.
_self_writes: dict[str, str] = {}
_self_writes_lock = Lock()


def _content_hash(data: str) -> str:
    return hashlib.md5(data.encode("utf-8")).hexdigest()


def _mark_self_write(path: str, content: str) -> None:
    with _self_writes_lock:
        _self_writes[path] = _content_hash(content)


def _is_self_write(path: str) -> bool:
    with _self_writes_lock:
        expected = _self_writes.get(path)
    if expected is None:
        return False
    try:
        current = _content_hash(Path(path).read_text(encoding="utf-8"))
    except Exception:
        # File gone or unreadable — not a self-write echo to skip
        with _self_writes_lock:
            _self_writes.pop(path, None)
        return False
    if current == expected:
        with _self_writes_lock:
            _self_writes.pop(path, None)
        return True
    # Content has diverged from what we wrote (user edit raced in); clear mark.
    with _self_writes_lock:
        _self_writes.pop(path, None)
    return False

FRONTMATTER_SYSTEM = """\
You are a knowledge management assistant. Given a markdown note's filename and content,
classify it and record the result by calling the set_frontmatter tool with:
- title: declarative one-line title (state what note claims, not just topic)
- type: one of: fact, preference, project, person, moc
- domain: one of: {domains}
- status: "seedling"
- summary: one sentence (max 25 words) stating what this note provides
- created: YYYY-MM-DD from first date bullet, or "unknown"
""".format(domains=", ".join(
    f"{d} ({brain_config.DOMAIN_DESCRIPTIONS[d]})" if d in brain_config.DOMAIN_DESCRIPTIONS else d
    for d in brain_config.DOMAINS
))

WIKILINK_SYSTEM = """\
You are a knowledge graph assistant. Given a note and a list of candidate related
notes, suggest 2-5 [[wikilinks]] to add by calling the suggest_wikilinks tool.

Rules:
- Only suggest links to notes in the provided candidate list — never invent titles
- Links must add genuine navigational value, not coincidental word overlap
- Embed each link mid-sentence where the connection is clear
- No broad topic-noun links

For each suggestion provide:
- anchor: exact text in note to replace (verbatim match required)
- target: exact note stem from the candidate list
- replacement: full replacement e.g. [[note_stem|display text]]
- confidence: "high" or "low"
- reason: one sentence

Call the tool with an empty suggestions array if no good links exist."""

SUMMARY_SYSTEM = """\
You are a knowledge management assistant. Given a markdown note's filename and content,
call the set_summary tool with:
- summary: one sentence (max 25 words) stating what this note provides or claims.
  Write it as if explaining to someone who has never seen the vault.
"""

# ── Structured-output tool schemas (forced tool_use replaces raw-JSON parsing) ──

# Wikilink suggestion needs cross-note reasoning; frontmatter/summary are
# simple classification and stay on the cheaper classify model for cost.
STRUCTURED_MODEL = brain_config.STRUCTURED_MODEL
CLASSIFY_MODEL   = brain_config.CLASSIFY_MODEL

FRONTMATTER_TOOL = {
    "name": "set_frontmatter",
    "description": "Record the classified frontmatter fields for the note.",
    "input_schema": {
        "type": "object",
        "properties": {
            "title":   {"type": "string", "description": "Declarative one-line title"},
            "type":    {"type": "string", "enum": ["fact", "preference", "project", "person", "moc"]},
            "domain":  {"type": "string", "enum": list(brain_config.DOMAINS)},
            "status":  {"type": "string", "description": 'Always "seedling"'},
            "summary": {"type": "string", "description": "One sentence, max 25 words"},
            "created": {"type": "string", "description": 'YYYY-MM-DD or "unknown"'},
        },
        "required": ["title", "type", "domain", "status", "summary", "created"],
        "additionalProperties": False,
    },
}

SUMMARY_TOOL = {
    "name": "set_summary",
    "description": "Record the one-sentence summary for the note.",
    "input_schema": {
        "type": "object",
        "properties": {
            "summary": {"type": "string", "description": "One sentence, max 25 words"},
        },
        "required": ["summary"],
        "additionalProperties": False,
    },
}

WIKILINK_TOOL = {
    "name": "suggest_wikilinks",
    "description": "Record suggested wikilink insertions for the note. "
                   "Use an empty suggestions array when no good links exist.",
    "input_schema": {
        "type": "object",
        "properties": {
            "suggestions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "anchor":      {"type": "string", "description": "Exact text in the note to replace"},
                        "target":      {"type": "string", "description": "Exact note stem from the candidate list"},
                        "replacement": {"type": "string", "description": "Full replacement incl. [[target|display]]"},
                        "confidence":  {"type": "string", "enum": ["high", "low"]},
                        "reason":      {"type": "string"},
                    },
                    "required": ["anchor", "target", "replacement", "confidence", "reason"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["suggestions"],
        "additionalProperties": False,
    },
}


def _call_structured(client: anthropic.Anthropic, system: str, user_content: str,
                     tool: dict, max_tokens: int,
                     model: str = STRUCTURED_MODEL) -> dict | None:
    """
    Forced tool-use call: the model must invoke `tool`, and we read the
    tool_use block's input (already-parsed dict — no raw-JSON parsing).
    Retries ONCE on any failure, then returns None so callers can fall back
    (log error / empty suggestions / skip).
    """
    last_err = None
    for attempt in (1, 2):
        try:
            resp = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system,
                tools=[tool],
                tool_choice={"type": "tool", "name": tool["name"]},
                messages=[{"role": "user", "content": user_content}],
            )
            for block in resp.content:
                if block.type == "tool_use" and block.name == tool["name"]:
                    if isinstance(block.input, dict):
                        return block.input
                    last_err = f"tool input not a dict: {type(block.input).__name__}"
                    break
            else:
                last_err = f"no tool_use block (stop_reason={resp.stop_reason})"
        except Exception as e:
            last_err = f"{type(e).__name__}: {e}"
        log.warning("structured call %s attempt %d/2 failed: %s",
                    tool["name"], attempt, last_err)
    return None

def notify(title: str, message: str):
    """Desktop notification — delegates to brain_platform (macOS: osascript;
    Windows: no-op). Kept as a module-level function because brain_test.py
    imports `notify` from this module.
    """
    try:
        brain_platform.notify(title, message)
    except Exception as e:
        log.warning("notify failed (%s): %s", type(e).__name__, e)

def already_has_frontmatter(content: str) -> bool:
    return content.strip().startswith("---")


def _extract_frontmatter_block(content: str) -> tuple[str, str] | None:
    """Return (frontmatter_text, rest) or None if no frontmatter."""
    m = re.match(r"^(---\n.*?\n---\n?)(.*)$", content, re.DOTALL)
    if not m:
        return None
    return m.group(1), m.group(2)


def _frontmatter_summary_empty(frontmatter: str) -> bool:
    """True if the frontmatter has a summary line and it's empty/whitespace."""
    m = re.search(r'^summary:\s*"?(.*?)"?\s*$', frontmatter, re.MULTILINE)
    if not m:
        return False  # no summary line at all — let full classification handle
    return m.group(1).strip() == ""


def _set_summary_in_frontmatter(frontmatter: str, summary: str) -> str:
    """Replace the summary line in the frontmatter block, preserving everything else."""
    safe = summary.replace('"', '\\"')
    return re.sub(
        r'^summary:\s*"?.*?"?\s*$',
        f'summary: "{safe}"',
        frontmatter, count=1, flags=re.MULTILINE
    )


def _backfill_summary(client: anthropic.Anthropic, filepath: Path, content: str) -> str | None:
    """Fill in an empty summary only, preserving user-pinned type/domain. Returns updated content or None."""
    split = _extract_frontmatter_block(content)
    if not split:
        return None
    frontmatter, body = split
    fields = _call_structured(
        client,
        system=SUMMARY_SYSTEM,
        user_content=f"Filename: {filepath.stem}\n\nContent:\n{body}",
        tool=SUMMARY_TOOL,
        max_tokens=1024,
        model=CLASSIFY_MODEL,
    )
    if fields is None:
        log.error(f"Summary backfill error on {filepath.name}: structured call failed")
        return None
    summary = str(fields.get("summary", "")).strip()
    if not summary:
        return None
    return _set_summary_in_frontmatter(frontmatter, summary) + body

def build_frontmatter(fields: dict) -> str:
    title   = str(fields.get("title", "")).replace('"', '\\"')
    ftype   = fields.get("type", "fact")
    domain  = fields.get("domain", brain_config.DOMAINS[0])
    status  = fields.get("status", "seedling")
    summary = str(fields.get("summary", "")).replace('"', '\\"')
    created = fields.get("created", datetime.now().strftime("%Y-%m-%d"))

    if ftype not in {"fact", "preference", "project", "person", "moc"}:
        ftype = "fact"
    if domain not in brain_config.DOMAINS:
        domain = brain_config.DOMAINS[0]

    return f"""---
title: "{title}"
type: {ftype}
domain: {domain}
status: {status}
summary: "{summary}"
tags: []
related: []
created: {created}
up: ""
---

"""

def get_note_index() -> dict:
    index = {}
    for note in VAULT_ROOT.rglob("*.md"):
        if ".obsidian" in str(note):
            continue
        content = note.read_text(encoding="utf-8")
        title_m   = re.search(r'^title:\s*"?(.+?)"?\s*$', content, re.MULTILINE)
        summary_m = re.search(r'^summary:\s*"?(.+?)"?\s*$', content, re.MULTILINE)
        index[note.stem] = {
            "title":   title_m.group(1).strip()   if title_m   else note.stem,
            "summary": summary_m.group(1).strip() if summary_m else "",
            "path":    note,
        }
    return index

def process_note(client: anthropic.Anthropic, voyage_client, collection, filepath: Path):
    if not filepath.exists():
        return
    if filepath.stem in SKIP_STEMS:
        return
    if filepath.stem.startswith("MOC-"):
        return  # MOCs are human-curated; don't auto-modify

    content = filepath.read_text(encoding="utf-8")
    if not content.strip():
        return

    modified = False

    # ── Step 1: Add frontmatter if missing ─────────────────────────────────
    if not already_has_frontmatter(content):
        log.info(f"Adding frontmatter: {filepath.name}")
        fields = _call_structured(
            client,
            system=FRONTMATTER_SYSTEM,
            user_content=f"Filename: {filepath.stem}\n\nContent:\n{content}",
            tool=FRONTMATTER_TOOL,
            max_tokens=1024,
            model=CLASSIFY_MODEL,
        )
        if fields is not None:
            fm = build_frontmatter(fields)
            content = fm + content
            modified = True
        else:
            log.error(f"Frontmatter error on {filepath.name}: structured call failed")
    else:
        # Frontmatter already present — if it's a stub with empty summary, backfill only that field.
        split = _extract_frontmatter_block(content)
        if split and _frontmatter_summary_empty(split[0]):
            log.info(f"Backfilling empty summary: {filepath.name}")
            updated = _backfill_summary(client, filepath, content)
            if updated:
                content = updated
                modified = True

    # ── Step 2: Suggest and inject high-confidence wikilinks ───────────────
    # Candidates come from the vector store: the 40 nearest notes to this
    # one, rather than the first 80 files in rglob order.
    try:
        candidates = get_link_candidates(
            voyage_client, collection, content, filepath.stem, k=40
        )
    except Exception as e:
        log.error(f"Link candidate retrieval error on {filepath.name}: {e}")
        candidates = []

    suggestions = []
    if candidates:
        candidate_text = "\n".join(
            f"- {stem}: {title} — {summary}"
            for stem, title, summary in candidates
        )
        result = _call_structured(
            client,
            system=WIKILINK_SYSTEM,
            user_content=(
                f"NOTE FILE: {filepath.stem}\n\n"
                f"NOTE CONTENT:\n{content}\n\n"
                f"CANDIDATE NOTES (nearest first):\n{candidate_text}"
            ),
            tool=WIKILINK_TOOL,
            max_tokens=2048,
        )
        if result is not None:
            raw_suggestions = result.get("suggestions", [])
            suggestions = [s for s in raw_suggestions if isinstance(s, dict)]
        else:
            log.error(f"Wikilink error on {filepath.name}: structured call failed")

    # Apply only high-confidence links whose targets exist and anchor is present.
    # Target validation checks the FULL vault index (disk), not just the 40
    # candidates, so a stale candidate list can't validate a dead target.
    # Replacements apply to the BODY only — an anchor that happens to match
    # frontmatter text must never inject [[links]] into YAML fields.
    applied_count = 0
    if suggestions:
        split = _extract_frontmatter_block(content)
        fm, body = split if split else ("", content)
        note_index = get_note_index()
        for s in suggestions:
            if s.get("confidence") != "high":
                continue
            target      = s.get("target", "")
            anchor      = s.get("anchor", "")
            replacement = s.get("replacement", "")
            if not anchor or not replacement or not target:
                continue
            if target not in note_index:
                continue
            if anchor in body and replacement not in body:
                body = body.replace(anchor, replacement, 1)
                applied_count += 1
                modified = True
        if applied_count:
            content = fm + body

    if modified:
        # Re-check existence — file may have been deleted during our API calls;
        # writing now would spuriously recreate it.
        if not filepath.exists():
            log.info(f"File vanished during processing: {filepath.name}")
            return
        _mark_self_write(str(filepath), content)
        filepath.write_text(content, encoding="utf-8")
        log.info(f"Updated {filepath.name} — {applied_count} links injected")
        notify("Second Brain", f"{filepath.stem}: {applied_count} links added")
    else:
        log.info(f"No changes needed: {filepath.name}")

    # ── Step 3: Embed into vector store ───────────────────────────────────────
    try:
        did_embed = embed_note(voyage_client, collection, filepath)
        if did_embed:
            log.info(f"Re-embedded: {filepath.name}")
        else:
            log.info(f"Skipped (unchanged): {filepath.name}")
    except Exception as e:
        log.error(f"Embed error on {filepath.name}: {e}")

# ── Reconcile: periodic vault hygiene ───────────────────────────────────────
# The old periodic-job approach was skipped during sleep, leaving the repair
# net unreliable. It now runs inside the watcher process — once at startup
# and every RECONCILE_INTERVAL_SEC of uptime — which also makes the watcher
# the sole Chroma writer.

def _vault_notes() -> list[Path]:
    return [
        p for p in sorted(VAULT_ROOT.rglob("*.md"))
        if ".obsidian" not in str(p)
    ]


def reconcile(voyage_client, collection) -> None:
    """
    1. Re-embed notes whose disk content differs from what's in Chroma
       (catches anything the watcher missed during downtime).
    2. Remove Chroma entries whose source note no longer exists (orphan prune).
    3. Write a unix timestamp to LAST_RECONCILE_FILE.
    4. Auto-commit the vault git repo if it has uncommitted changes.
    """
    log.info("reconcile started")

    # ── 1. Re-embed changed notes ─────────────────────────────────────────
    embedded = skipped = errors = 0
    for note in _vault_notes():
        try:
            did_embed = embed_note(voyage_client, collection, note, force=False)
            if did_embed:
                embedded += 1
                time.sleep(RECONCILE_RATE_LIMIT_SLEEP)
            else:
                skipped += 1
        except Exception as e:
            log.warning("reconcile embed failed on %s: %s", note.name, e)
            errors += 1

    # ── 2. Prune orphans ──────────────────────────────────────────────────
    pruned = 0
    on_disk = {p.stem for p in _vault_notes()}
    try:
        all_data = collection.get(include=[])
        in_chroma = set(all_data.get("ids") or [])
        orphans = sorted(in_chroma - on_disk)
        if orphans:
            log.info("reconcile orphans found: %d (%s%s)", len(orphans),
                     ", ".join(orphans[:5]),
                     "..." if len(orphans) > 5 else "")
            collection.delete(ids=orphans)
            pruned = len(orphans)
    except Exception as e:
        log.warning("reconcile orphan prune failed: %s", e)

    # ── 3. Freshness timestamp ────────────────────────────────────────────
    try:
        LAST_RECONCILE_FILE.write_text(str(int(time.time())), encoding="utf-8")
    except Exception as e:
        log.warning("reconcile timestamp write failed: %s", e)

    # ── 4. Auto-commit vault snapshot (never crash the watcher on git failure)
    try:
        status = subprocess.run(
            ["git", "-C", str(VAULT_GIT_ROOT), "status", "--porcelain"],
            capture_output=True, text=True, check=False,
        )
        if status.returncode == 0 and status.stdout.strip():
            subprocess.run(
                ["git", "-C", str(VAULT_GIT_ROOT), "add", "-A"],
                capture_output=True, text=True, check=False,
            )
            commit = subprocess.run(
                ["git", "-C", str(VAULT_GIT_ROOT), "commit", "-m", "brain: reconcile snapshot"],
                capture_output=True, text=True, check=False,
            )
            if commit.returncode == 0:
                log.info("reconcile: vault snapshot committed")
            else:
                log.warning("reconcile git commit failed: %s",
                            (commit.stderr or commit.stdout).strip()[:300])
        elif status.returncode != 0:
            log.warning("reconcile git status failed: %s",
                        (status.stderr or status.stdout).strip()[:300])
    except Exception as e:
        log.warning("reconcile git snapshot failed (%s): %s", type(e).__name__, e)

    log.info(
        "reconcile complete: embedded=%d skipped=%d errors=%d pruned=%d",
        embedded, skipped, errors, pruned,
    )


def _reconcile_loop(voyage_client, collection) -> None:
    """Daemon thread body: reconcile at startup, then every 6h of uptime."""
    while True:
        try:
            reconcile(voyage_client, collection)
        except Exception as e:
            log.error("reconcile crashed (%s): %s", type(e).__name__, e)
        time.sleep(RECONCILE_INTERVAL_SEC)

# ── Debounced file event handler ───────────────────────────────────────────

class NoteHandler(FileSystemEventHandler):
    def __init__(self, client: anthropic.Anthropic, voyage_client, collection):
        self.client         = client
        self.voyage_client  = voyage_client
        self.collection     = collection
        self._timers: dict[str, Timer] = {}
        # Delete-verify timers, keyed by path. macOS FSEvents delivers delete
        # events late: a delete+recreate within seconds (how Claude sessions
        # rewrite notes) can surface the delete AFTER the file exists again.
        # Instead of evicting from Chroma immediately, we wait
        # DELETE_VERIFY_SEC and re-check the filesystem.
        self._delete_timers: dict[str, Timer] = {}

    def _cancel_delete_verify(self, path: str):
        t = self._delete_timers.pop(path, None)
        if t is not None:
            t.cancel()

    def _schedule(self, path: str):
        # A create/modify for this path supersedes any pending delete-verify.
        self._cancel_delete_verify(path)
        if path in self._timers:
            self._timers[path].cancel()
        t = Timer(DEBOUNCE_SEC, self._run, args=[path])
        self._timers[path] = t
        t.start()

    def _run(self, path: str):
        self._timers.pop(path, None)
        if _is_self_write(path):
            log.debug(f"Skipping self-write: {Path(path).name}")
            return
        fp = Path(path)
        if fp.suffix == ".md" and ".obsidian" not in path:
            log.info(f"Processing: {fp.name}")
            process_note(self.client, self.voyage_client, self.collection, fp)

    def on_created(self, event):
        if not event.is_directory:
            self._schedule(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self._schedule(event.src_path)

    def on_deleted(self, event):
        if event.is_directory:
            return
        path = event.src_path
        if not path.endswith(".md") or ".obsidian" in path:
            return
        # Cancel any pending debounced process for this path — otherwise a
        # queued _run could re-create the file by writing it back after delete.
        pending = self._timers.pop(path, None)
        if pending is not None:
            pending.cancel()
        # Delayed verification instead of immediate eviction: replace any
        # pending verify timer for this path so rapid delete/create sequences
        # don't pile up timers or double-delete.
        self._cancel_delete_verify(path)
        t = Timer(DELETE_VERIFY_SEC, self._verify_delete, args=[path])
        self._delete_timers[path] = t
        t.start()

    def _verify_delete(self, path: str):
        self._delete_timers.pop(path, None)
        if Path(path).exists():
            # File was re-created after the (late) delete event — this was a
            # delete+recreate rewrite. Treat as a modify.
            log.info(f"Delete superseded by recreate, rescheduling: {Path(path).name}")
            self._schedule(path)
            return
        # Still gone after the grace period — evict for real.
        with _self_writes_lock:
            _self_writes.pop(path, None)
        stem = Path(path).stem
        try:
            self.collection.delete(ids=[stem])
            log.info(f"Deleted from vector store: {stem}")
        except Exception as e:
            log.warning(f"Chroma delete failed for {stem}: {e}")

    def on_moved(self, event):
        if event.is_directory:
            return
        src  = event.src_path
        dest = getattr(event, "dest_path", "") or ""
        if src.endswith(".md") and ".obsidian" not in src:
            # The old path is gone for good — clean up its timers/marks and
            # evict the old stem from Chroma (renames orphan the old id).
            pending = self._timers.pop(src, None)
            if pending is not None:
                pending.cancel()
            self._cancel_delete_verify(src)
            with _self_writes_lock:
                _self_writes.pop(src, None)
            old_stem = Path(src).stem
            try:
                self.collection.delete(ids=[old_stem])
                log.info(f"Deleted from vector store (moved): {old_stem}")
            except Exception as e:
                log.warning(f"Chroma delete failed for moved {old_stem}: {e}")
        if dest.endswith(".md") and ".obsidian" not in dest:
            try:
                in_vault = Path(dest).is_relative_to(VAULT_ROOT)
            except Exception:
                in_vault = False
            if in_vault:
                log.info(f"Move detected, scheduling: {Path(dest).name}")
                self._schedule(dest)

# ── Main ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Second brain file watcher — auto-links new notes")
    parser.add_argument("--verbose", action="store_true",
                        help="Mirror logs to stdout in addition to file logging")
    args = parser.parse_args()

    if args.verbose:
        stream = logging.StreamHandler(sys.stdout)
        stream.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logging.getLogger().addHandler(stream)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        log.error("ANTHROPIC_API_KEY not set.")
        sys.exit(1)

    voyage_key = os.environ.get("VOYAGE_API_KEY")
    if not voyage_key:
        log.error("VOYAGE_API_KEY not set.")
        sys.exit(1)

    client         = anthropic.Anthropic(api_key=api_key)
    voyage_client  = voyageai.Client(api_key=voyage_key)
    collection     = get_collection()

    # ── Embedding dim-mismatch boot guard ──────────────────────────────────
    # Refuse to start if the configured Voyage model's dim doesn't match what
    # the Chroma collection already stores. A silent dim mismatch corrupts
    # retrieval; loud exit forces a deliberate rebuild.
    stored_dim = get_collection_dim(collection)
    if stored_dim is not None and stored_dim != EMBED_DIM:
        log.error(
            "EMBED DIM MISMATCH: chroma collection has dim=%d but configured model %s expects dim=%d. "
            "Refusing to start. Rebuild the collection or correct models.embed_dim in brain_config.json.",
            stored_dim, EMBED_MODEL, EMBED_DIM,
        )
        sys.exit(78)  # EX_CONFIG

    handler        = NoteHandler(client, voyage_client, collection)
    observer = Observer()
    observer.schedule(handler, str(VAULT_ROOT), recursive=True)
    observer.start()

    # Reconcile thread: once at startup, then every 6h of process uptime.
    # Uptime-based (not a periodic launchd job) so sleep can't starve it —
    # any wake that keeps the watcher alive eventually reconciles.
    Thread(
        target=_reconcile_loop,
        args=(voyage_client, collection),
        name="reconcile",
        daemon=True,
    ).start()

    log.info(f"Second brain watcher started — watching {VAULT_ROOT}")
    notify("Second Brain", "Watcher active — new notes will be auto-linked")

    def shutdown(sig, frame):
        log.info("Shutting down watcher...")
        observer.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT,  shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
