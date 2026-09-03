#!/usr/bin/env python3
"""
brain_vector.py — Shared embedding + retrieval module for the second brain.

Provides:
  - get_collection()         → ChromaDB collection
  - embed_note()              → embed a single note into ChromaDB
  - query_brain()              → hybrid dense + BM25 search
  - format_for_injection()   → XML-formatted context for Claude

Used by: brain_watcher.py, build_index.py, query_brain.py
"""

import re
import os
import hashlib
import logging
import sys
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape, quoteattr as xml_quoteattr

import chromadb
import voyageai
from rank_bm25 import BM25Okapi

sys.path.insert(0, str(Path(__file__).resolve().parent))
import brain_config

log = logging.getLogger(__name__)

VAULT_ROOT   = brain_config.VAULT_MEMORY
CHROMA_PATH  = brain_config.CHROMA_PATH
EMBED_MODEL  = brain_config.EMBED_MODEL        # unified: embed and query must share a model
EMBED_DIM    = brain_config.EMBED_DIM
QUERY_MODEL  = brain_config.EMBED_MODEL        # keep separate constant for future flexibility
SIMILARITY_THRESHOLD = 0.35      # drop hits below this (cosine similarity)
CHARS_PER_TOKEN = 4              # rough approximation for budget enforcement


# ── ChromaDB ──────────────────────────────────────────────────────────────────

def get_collection() -> chromadb.Collection:
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    return client.get_or_create_collection(
        name="notes",
        metadata={"hnsw:space": "cosine"}
    )


def get_collection_dim(collection: chromadb.Collection) -> int | None:
    """
    Return the dim of stored embeddings, or None if the collection is empty.

    Used by brain_watcher's startup guard to refuse to boot on
    embedding-model dim mismatch.
    """
    try:
        peek = collection.peek(1)
    except Exception:
        return None
    embeds = peek.get("embeddings") if peek else None
    if embeds is None or len(embeds) == 0:
        return None
    first = embeds[0]
    try:
        return len(first)
    except TypeError:
        return None


# ── Note parsing ──────────────────────────────────────────────────────────────

def parse_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter into a flat dict."""
    meta = {}
    if not content.strip().startswith("---"):
        return meta
    m = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not m:
        return meta
    for line in m.group(1).splitlines():
        if ": " in line:
            k, v = line.split(": ", 1)
            meta[k.strip()] = v.strip().strip('"')
    return meta


def clean_body(content: str) -> str:
    """Strip frontmatter and Obsidian syntax for clean embedding."""
    # Strip frontmatter
    body = re.sub(r"^---\n.*?\n---\n?", "", content, flags=re.DOTALL).strip()
    # Strip [[link|display]] → display text
    body = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', r'\2', body)
    # Strip [[link]] → link text
    body = re.sub(r'\[\[([^\]]+)\]\]', r'\1', body)
    # Strip Obsidian callouts
    body = re.sub(r'^> \[!\w+\]', '>', body, flags=re.MULTILINE)
    return body.strip()


def prepare_for_embedding(body: str, meta: dict) -> str:
    """Prepend structured metadata so it's encoded into the vector."""
    parts = []
    if title := meta.get("title"):
        parts.append(f"Title: {title}")
    if domain := meta.get("domain"):
        parts.append(f"Domain: {domain}")
    if ntype := meta.get("type"):
        parts.append(f"Type: {ntype}")
    if created := meta.get("created"):
        parts.append(f"Date: {created}")
    if summary := meta.get("summary"):
        parts.append(f"Summary: {summary}")
    prefix = "\n".join(parts)
    return f"{prefix}\n\n{body}" if prefix else body


# ── Embedding ─────────────────────────────────────────────────────────────────

def embed_note(voyage_client: voyageai.Client,
               collection: chromadb.Collection,
               filepath: Path,
               force: bool = False) -> bool:
    """
    Embed a single note and upsert into ChromaDB.
    Returns True if embedding was performed, False if skipped (unchanged).
    When force=True, re-embed even if the content hash is unchanged.
    """
    if not filepath.exists():
        return False

    content = filepath.read_text(encoding="utf-8")
    if not content.strip():
        return False

    # Content hash guard — skip if note hasn't changed (unless forced)
    content_hash = hashlib.md5(content.encode()).hexdigest()
    if not force:
        try:
            existing = collection.get(ids=[filepath.stem], include=["metadatas"])
            if existing["metadatas"] and existing["metadatas"][0]:
                if existing["metadatas"][0].get("content_hash") == content_hash:
                    return False  # unchanged
        except Exception as e:
            log.warning("hash check failed on %s (%s): %s", filepath.name, type(e).__name__, e)

    meta = parse_frontmatter(content)
    body = clean_body(content)
    if not body:
        return False

    text_to_embed = prepare_for_embedding(body, meta)

    result = voyage_client.embed(
        [text_to_embed],
        model=EMBED_MODEL,
        input_type="document",
        truncation=True,
    )
    embedding = result.embeddings[0]

    collection.upsert(
        ids=[filepath.stem],
        embeddings=[embedding],
        documents=[body],
        metadatas=[{
            "path":         str(filepath),
            "domain":       meta.get("domain", "general"),
            "type":         meta.get("type", "fact"),
            "title":        meta.get("title", filepath.stem),
            "summary":      meta.get("summary", ""),
            "created":      meta.get("created", "unknown"),
            "content_hash": content_hash,
        }]
    )
    return True


# ── Retrieval ─────────────────────────────────────────────────────────────────

def _rrf_fuse(dense_ids: list[str], dense_scores: list[float],
              sparse_ids: list[str], sparse_scores: list[float],
              k: int = 60) -> list[tuple[str, float]]:
    """Reciprocal Rank Fusion of dense + sparse result lists."""
    # Build rank maps
    dense_rank  = {id_: i + 1 for i, id_ in enumerate(dense_ids)}
    sparse_rank = {id_: i + 1 for i, id_ in enumerate(sparse_ids)}

    all_ids = set(dense_ids) | set(sparse_ids)
    scores = {}
    for id_ in all_ids:
        dr = dense_rank.get(id_, len(dense_ids) + k)
        sr = sparse_rank.get(id_, len(sparse_ids) + k)
        scores[id_] = (1 / (k + dr)) + (1 / (k + sr))

    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


def query_brain(voyage_client: voyageai.Client,
                collection: chromadb.Collection,
                query: str,
                domain: str | None = None,
                n: int = 8) -> list[dict]:
    """
    Hybrid dense + BM25 search over the vault.
    Returns list of dicts: {title, domain, type, summary, text, score, path}
    """
    # ── Dense retrieval ───────────────────────────────────────────────────────
    q_result = voyage_client.embed(
        [query],
        model=QUERY_MODEL,
        input_type="query",
        truncation=True,
    )
    q_embedding = q_result.embeddings[0]

    where = {"domain": {"$eq": domain}} if domain else None
    chroma_n = min(n * 2, 20)  # over-fetch for RRF

    try:
        results = collection.query(
            query_embeddings=[q_embedding],
            n_results=chroma_n,
            where=where,
            include=["documents", "metadatas", "distances"]
        )
        dense_ids    = results["ids"][0]
        dense_docs   = results["documents"][0]
        dense_metas  = results["metadatas"][0]
        dense_dists  = results["distances"][0]
        # Chroma cosine distance is in [0, 2]; sim = 1 - dist gives [-1, 1] cosine similarity.
        dense_scores = [1 - d for d in dense_dists]
    except Exception as e:
        log.warning("dense retrieval failed (%s): %s", type(e).__name__, e)
        dense_ids = dense_docs = dense_metas = dense_scores = []

    # ── BM25 retrieval ────────────────────────────────────────────────────────
    try:
        all_data = collection.get(
            include=["documents", "metadatas"],
            where=where
        )
        all_ids   = all_data["ids"]
        all_docs  = all_data["documents"]
        all_metas = all_data["metadatas"]

        tokenized = [doc.lower().split() for doc in all_docs]
        bm25 = BM25Okapi(tokenized)
        bm25_scores_arr = bm25.get_scores(query.lower().split())

        # Top-N sparse results
        sparse_ranked = sorted(
            zip(all_ids, bm25_scores_arr),
            key=lambda x: x[1], reverse=True
        )[:chroma_n]
        sparse_ids    = [x[0] for x in sparse_ranked]
        sparse_scores_map = {x[0]: x[1] for x in sparse_ranked}
    except Exception as e:
        log.warning("sparse (BM25) retrieval failed (%s): %s", type(e).__name__, e)
        sparse_ids = []
        sparse_scores_map = {}

    # ── RRF fusion ────────────────────────────────────────────────────────────
    fused = _rrf_fuse(dense_ids, dense_scores, sparse_ids, list(sparse_scores_map.values()))

    # Build lookup maps
    dense_meta_map = {id_: (dense_metas[i], dense_docs[i], dense_scores[i])
                      for i, id_ in enumerate(dense_ids)}
    all_meta_map   = {id_: (all_metas[i], all_docs[i])
                      for i, id_ in enumerate(all_ids)}

    hits = []
    for id_, rrf_score in fused[:n]:
        if id_ in dense_meta_map:
            meta, doc, sim = dense_meta_map[id_]
        elif id_ in all_meta_map:
            meta, doc = all_meta_map[id_]
            sim = 0.0
        else:
            continue

        # Filter very low similarity dense hits (keep BM25-only hits)
        if id_ in dense_meta_map and sim < SIMILARITY_THRESHOLD:
            if id_ not in sparse_scores_map:
                continue  # drop pure-dense low-quality hit

        hits.append({
            "id":      id_,
            "title":   meta.get("title", id_),
            "domain":  meta.get("domain", ""),
            "type":    meta.get("type", ""),
            "summary": meta.get("summary", ""),
            "text":    doc,
            "score":   round(rrf_score, 4),
            "sim":     round(sim, 3),
            "path":    meta.get("path", ""),
        })

    return hits


# ── Link candidate retrieval ───────────────────────────────────────────────────

def get_link_candidates(voyage_client: voyageai.Client,
                         collection: chromadb.Collection,
                         note_text: str,
                         exclude_stem: str,
                         k: int = 40) -> list[tuple[str, str, str]]:
    """
    Embed note_text as a query and return the k nearest notes in the
    collection (excluding exclude_stem) as a relevance-ranked candidate list.

    Returns a list of (stem, title, summary) tuples, nearest first. Used by
    brain_watcher's wikilink step in place of an arbitrary rglob-order slice
    of the vault. Returns [] on an empty collection or any retrieval
    failure — callers should treat that as "no candidates" rather than an
    error.
    """
    try:
        count = collection.count()
    except Exception as e:
        log.warning("collection.count failed in get_link_candidates (%s): %s", type(e).__name__, e)
        return []
    if count == 0:
        return []

    try:
        q_result = voyage_client.embed(
            [note_text],
            model=QUERY_MODEL,
            input_type="query",
            truncation=True,
        )
        q_embedding = q_result.embeddings[0]
    except Exception as e:
        log.warning("embed failed in get_link_candidates (%s): %s", type(e).__name__, e)
        return []

    # Over-fetch by one so excluding exclude_stem still leaves up to k results.
    n_results = min(k + 1, count)
    try:
        results = collection.query(
            query_embeddings=[q_embedding],
            n_results=n_results,
            include=["metadatas"],
        )
    except Exception as e:
        log.warning("query failed in get_link_candidates (%s): %s", type(e).__name__, e)
        return []

    ids = results["ids"][0] if results.get("ids") else []
    metas = results["metadatas"][0] if results.get("metadatas") else []

    candidates: list[tuple[str, str, str]] = []
    for id_, meta in zip(ids, metas):
        if id_ == exclude_stem:
            continue
        meta = meta or {}
        candidates.append((id_, meta.get("title", id_), meta.get("summary", "")))
        if len(candidates) >= k:
            break

    return candidates


# ── Context formatting ────────────────────────────────────────────────────────

def format_for_injection(hits: list[dict], token_budget: int = 6000) -> str:
    """Format retrieved hits as XML block for Claude context injection."""
    if not hits:
        return ""

    char_budget = token_budget * CHARS_PER_TOKEN
    used = 0

    header = (
        "<retrieved_knowledge>\n"
        "<instructions>\n"
        f"Use the notes below as ground truth for {brain_config.OWNER_NAME}'s personal context, "
        "preferences, and project decisions. Prioritize these over general knowledge "
        "when they conflict. Cite notes by title when referencing them.\n"
        "</instructions>\n"
    )
    used += len(header)

    note_blocks = []
    for h in hits:
        title_attr  = xml_quoteattr(h["title"])
        domain_attr = xml_quoteattr(h["domain"])
        text        = xml_escape(h["text"])
        block = (
            f'<note title={title_attr} domain={domain_attr} '
            f'relevance="{h["sim"]:.2f}">\n{text}\n</note>'
        )
        if used + len(block) > char_budget:
            # Try summary-only fallback
            if h["summary"]:
                summary = xml_escape(h["summary"])
                block = (
                    f'<note title={title_attr} domain={domain_attr} '
                    f'relevance="{h["sim"]:.2f}" truncated="true">\n'
                    f'{summary}\n</note>'
                )
            else:
                break
        note_blocks.append(block)
        used += len(block)

    return header + "\n".join(note_blocks) + "\n</retrieved_knowledge>"
