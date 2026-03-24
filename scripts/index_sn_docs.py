#!/usr/bin/env python3
"""
Index ServiceNow documentation into Qdrant for semantic search.

Chunks Markdown, DOCX, PDF, and HTML files, embeds them with
BGE-M3 (1024-dim), and upserts into the Qdrant collection with
namespace_id="sn_mcp".

Supported source types:
  - "process"      — ITIL process documentation (Incident, Change, Problem, etc.)
  - "training"     — Training materials (Schulungen)
  - "api_reference"— REST API, GlideRecord, scripting references
  - "handbook"     — Implementation handbooks, best practices
  - "customizing"  — Consulting/customizing guides

Usage:
    python scripts/index_sn_docs.py [--rebuild]
    python scripts/index_sn_docs.py --batch-size 64
    python scripts/index_sn_docs.py --docs-only
"""

import argparse
import hashlib
import os
import re
import sys
import time
from pathlib import Path

from bs4 import BeautifulSoup
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

NAMESPACE = "sn_mcp"
PROJECT_ROOT = Path(__file__).parent.parent
DOCS_DIR = PROJECT_ROOT / "docs"
SCHULUNGEN_DIR = PROJECT_ROOT / "schulungen"
CONSULTING_DIR = PROJECT_ROOT / "consulting"

# Chunking settings
CHUNK_SIZE = 800  # characters (roughly ~200 tokens)
CHUNK_OVERLAP = 100


def chunk_id(source: str, idx: int) -> str:
    """Deterministic chunk ID from source path + index."""
    h = hashlib.sha256(f"{source}:{idx}".encode()).hexdigest()[:16]
    return f"sn_mcp_{h}"


def chunk_text(
    text: str, source: str, max_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP
) -> list[dict]:
    """Split text into overlapping chunks with metadata."""
    text = text.strip()
    if not text:
        return []

    # For short texts, return as single chunk
    if len(text) <= max_size:
        return [{"text": text, "chunk_id": chunk_id(source, 0), "chunk_idx": 0}]

    chunks = []
    start = 0
    idx = 0
    while start < len(text):
        end = start + max_size
        # Try to break at paragraph or sentence boundary
        if end < len(text):
            # Look for paragraph break
            para_break = text.rfind("\n\n", start + max_size // 2, end)
            if para_break > start:
                end = para_break
            else:
                # Look for sentence break
                sent_break = text.rfind(". ", start + max_size // 2, end)
                if sent_break > start:
                    end = sent_break + 1

        chunk = text[start:end].strip()
        if chunk:
            chunks.append({
                "text": chunk,
                "chunk_id": chunk_id(source, idx),
                "chunk_idx": idx,
            })
            idx += 1

        start = end - overlap if end < len(text) else len(text)

    return chunks


# ── Document parsers ─────────────────────────────────────────────────────────

def parse_markdown(path: Path) -> str:
    """Read a Markdown file as plain text."""
    try:
        return path.read_text(encoding="utf-8").strip()
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1").strip()
    except Exception:
        return ""


def parse_docx(path: Path) -> str:
    """Extract text from a DOCX file using python-docx."""
    try:
        from docx import Document
        doc = Document(str(path))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n\n".join(paragraphs)
    except ImportError:
        print("  Warning: python-docx not installed, skipping DOCX files")
        return ""
    except Exception as e:
        print(f"  Warning: Could not parse DOCX {path.name}: {e}")
        return ""


def parse_pdf(path: Path) -> list[tuple[str, int]]:
    """Extract text from PDF, returns [(text, page_no), ...]."""
    try:
        import pymupdf
        pymupdf.TOOLS.mupdf_display_errors(False)  # suppress zlib warnings
        doc = pymupdf.open(str(path))
        pages = []
        for i, page in enumerate(doc):
            try:
                text = page.get_text().strip()
                if text:
                    pages.append((text, i + 1))
            except Exception:
                continue  # skip broken pages
        doc.close()
        return pages
    except ImportError:
        print("  Warning: pymupdf not installed, skipping PDF files")
        return []
    except Exception as e:
        print(f"  Warning: Could not parse PDF {path.name}: {e}")
        return []


def parse_html(path: Path) -> str:
    """Extract clean text from an HTML document."""
    try:
        html = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            html = path.read_text(encoding="latin-1")
        except Exception:
            return ""
    except Exception:
        return ""

    soup = BeautifulSoup(html, "html.parser")

    # Extract title
    title = soup.title.string.strip() if soup.title and soup.title.string else ""

    # Extract body text from content div (skip nav/header boilerplate)
    content_div = soup.find("div", id="content") or soup.find("main") or soup.find("article")
    if content_div:
        text = content_div.get_text(separator="\n", strip=True)
    else:
        text = soup.get_text(separator="\n", strip=True)

    # Prepend title for context
    if title and not text.startswith(title):
        text = f"{title}\n\n{text}"

    # Clean up excessive whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


# ── Source scanners ──────────────────────────────────────────────────────────

def _classify_source_type(path: Path, base_dir: Path) -> str:
    """Classify a file into a source type based on its location and name."""
    rel = str(path.relative_to(PROJECT_ROOT)).lower()

    if "schulung" in rel or str(base_dir) == str(SCHULUNGEN_DIR):
        return "training"
    elif "consulting" in rel or str(base_dir) == str(CONSULTING_DIR):
        return "customizing"
    elif "api" in rel or "rest" in rel or "glide" in rel:
        return "api_reference"
    elif "handbook" in rel or "handbuch" in rel:
        return "handbook"
    else:
        return "process"


def scan_docs_directory(docs_dir: Path) -> list[dict]:
    """Scan the docs/ directory for Markdown, HTML, DOCX, and PDF files."""
    chunks = []
    if not docs_dir.exists():
        print(f"  Docs: directory {docs_dir} not found, skipping")
        return chunks

    # Markdown files
    for path in sorted(docs_dir.rglob("*.md")):
        text = parse_markdown(path)
        if not text:
            continue
        source_type = _classify_source_type(path, docs_dir)
        for c in chunk_text(text, f"docs/{path.name}"):
            chunks.append({
                "chunk_id": c["chunk_id"],
                "content": c["text"],
                "source_type": source_type,
                "source_file": path.name,
                "table_name": "",
                "field_name": "",
                "page_no": None,
                "namespace_id": NAMESPACE,
            })

    # HTML files
    for path in sorted(docs_dir.rglob("*.html")):
        text = parse_html(path)
        if not text:
            continue
        source_type = _classify_source_type(path, docs_dir)
        for c in chunk_text(text, f"docs/{path.name}"):
            chunks.append({
                "chunk_id": c["chunk_id"],
                "content": c["text"],
                "source_type": source_type,
                "source_file": path.name,
                "table_name": "",
                "field_name": "",
                "page_no": None,
                "namespace_id": NAMESPACE,
            })

    # DOCX files
    for path in sorted(docs_dir.rglob("*.docx")):
        text = parse_docx(path)
        if not text:
            continue
        source_type = _classify_source_type(path, docs_dir)
        for c in chunk_text(text, f"docs/{path.name}"):
            chunks.append({
                "chunk_id": c["chunk_id"],
                "content": c["text"],
                "source_type": source_type,
                "source_file": path.name,
                "table_name": "",
                "field_name": "",
                "page_no": None,
                "namespace_id": NAMESPACE,
            })

    # PDF files
    for path in sorted(docs_dir.rglob("*.pdf")):
        pages = parse_pdf(path)
        source_type = _classify_source_type(path, docs_dir)
        for page_text, page_no in pages:
            for c in chunk_text(page_text, f"docs/{path.name}:p{page_no}"):
                chunks.append({
                    "chunk_id": c["chunk_id"],
                    "content": c["text"],
                    "source_type": source_type,
                    "source_file": path.name,
                    "table_name": "",
                    "field_name": "",
                    "page_no": page_no,
                    "namespace_id": NAMESPACE,
                })

    print(f"  Docs: {len(chunks)} chunks")
    return chunks


def scan_schulungen(schulungen_dir: Path) -> list[dict]:
    """Scan training materials (PDFs, Markdown, DOCX)."""
    chunks = []
    if not schulungen_dir.exists():
        print("  Schulungen: directory not found, skipping")
        return chunks

    # PDFs
    for path in sorted(schulungen_dir.rglob("*.pdf")):
        pages = parse_pdf(path)
        for page_text, page_no in pages:
            for c in chunk_text(page_text, f"training/{path.name}:p{page_no}"):
                chunks.append({
                    "chunk_id": c["chunk_id"],
                    "content": c["text"],
                    "source_type": "training",
                    "source_file": path.name,
                    "table_name": "",
                    "field_name": "",
                    "page_no": page_no,
                    "namespace_id": NAMESPACE,
                })

    # Markdown
    for path in sorted(schulungen_dir.rglob("*.md")):
        text = parse_markdown(path)
        if not text:
            continue
        for c in chunk_text(text, f"training/{path.name}"):
            chunks.append({
                "chunk_id": c["chunk_id"],
                "content": c["text"],
                "source_type": "training",
                "source_file": path.name,
                "table_name": "",
                "field_name": "",
                "page_no": None,
                "namespace_id": NAMESPACE,
            })

    # DOCX
    for path in sorted(schulungen_dir.rglob("*.docx")):
        text = parse_docx(path)
        if not text:
            continue
        for c in chunk_text(text, f"training/{path.name}"):
            chunks.append({
                "chunk_id": c["chunk_id"],
                "content": c["text"],
                "source_type": "training",
                "source_file": path.name,
                "table_name": "",
                "field_name": "",
                "page_no": None,
                "namespace_id": NAMESPACE,
            })

    print(f"  Schulungen: {len(chunks)} chunks")
    return chunks


def scan_consulting(consulting_dir: Path) -> list[dict]:
    """Scan consulting/customizing materials (Markdown, DOCX, PDF)."""
    chunks = []
    if not consulting_dir.exists():
        print("  Consulting: directory not found, skipping")
        return chunks

    for path in sorted(consulting_dir.rglob("*.md")):
        text = parse_markdown(path)
        if not text:
            continue
        for c in chunk_text(text, f"customizing/{path.name}"):
            chunks.append({
                "chunk_id": c["chunk_id"],
                "content": c["text"],
                "source_type": "customizing",
                "source_file": path.name,
                "table_name": "",
                "field_name": "",
                "page_no": None,
                "namespace_id": NAMESPACE,
            })

    for path in sorted(consulting_dir.rglob("*.docx")):
        text = parse_docx(path)
        if not text:
            continue
        for c in chunk_text(text, f"customizing/{path.name}"):
            chunks.append({
                "chunk_id": c["chunk_id"],
                "content": c["text"],
                "source_type": "customizing",
                "source_file": path.name,
                "table_name": "",
                "field_name": "",
                "page_no": None,
                "namespace_id": NAMESPACE,
            })

    for path in sorted(consulting_dir.rglob("*.pdf")):
        pages = parse_pdf(path)
        for page_text, page_no in pages:
            for c in chunk_text(page_text, f"customizing/{path.name}:p{page_no}"):
                chunks.append({
                    "chunk_id": c["chunk_id"],
                    "content": c["text"],
                    "source_type": "customizing",
                    "source_file": path.name,
                    "table_name": "",
                    "field_name": "",
                    "page_no": page_no,
                    "namespace_id": NAMESPACE,
                })

    print(f"  Consulting: {len(chunks)} chunks")
    return chunks


# ── Embedding ────────────────────────────────────────────────────────────────

class Embedder:
    """BGE-M3 embedding model via sentence-transformers (1024-dim)."""

    def __init__(self, batch_size: int = 32):
        from sentence_transformers import SentenceTransformer
        print("Loading BGE-M3 embedding model...")
        self.model = SentenceTransformer("BAAI/bge-m3")
        self.batch_size = batch_size
        print(f"Model loaded (dim={self.model.get_sentence_embedding_dimension()}).")

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed texts and return dense vectors (1024-dim)."""
        all_embeddings = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            vecs = self.model.encode(
                batch, show_progress_bar=False, normalize_embeddings=True
            )
            all_embeddings.extend(vecs.tolist())
            done = min(i + self.batch_size, len(texts))
            if done % (self.batch_size * 10) == 0 or done == len(texts):
                print(f"    Embedded {done}/{len(texts)}...")
        return all_embeddings


# ── Qdrant upsert ────────────────────────────────────────────────────────────

def upsert_to_qdrant(
    client: QdrantClient,
    collection: str,
    chunks: list[dict],
    embeddings: list[list[float]],
    batch_size: int = 20,
):
    """Upsert chunks with embeddings into Qdrant."""
    # Ensure collection has the right vector config
    try:
        info = client.get_collection(collection)
        print(f"Using existing collection '{collection}' ({info.points_count} existing points)")
    except Exception:
        print(f"Creating collection '{collection}'...")
        client.create_collection(
            collection_name=collection,
            vectors_config={
                "dense": VectorParams(size=1024, distance=Distance.COSINE, on_disk=True),
            },
        )

    points = []
    for chunk, embedding in zip(chunks, embeddings):
        # Use a deterministic numeric ID from the chunk_id hash
        point_id = int(hashlib.sha256(chunk["chunk_id"].encode()).hexdigest()[:15], 16)
        points.append(
            PointStruct(
                id=point_id,
                vector={"dense": embedding},
                payload={
                    "content": chunk["content"],
                    "source_type": chunk["source_type"],
                    "source_file": chunk["source_file"],
                    "table_name": chunk["table_name"],
                    "field_name": chunk["field_name"],
                    "page_no": chunk["page_no"],
                    "namespace_id": chunk["namespace_id"],
                    "chunk_id": chunk["chunk_id"],
                    "ingestion_timestamp": time.time(),
                },
            )
        )

    # Batch upsert
    for i in range(0, len(points), batch_size):
        batch = points[i:i + batch_size]
        client.upsert(collection_name=collection, points=batch)
        if (i + batch_size) % (batch_size * 5) == 0:
            print(f"  Upserted {min(i + batch_size, len(points))}/{len(points)} points...")

    print(f"  Total: {len(points)} points upserted.")


def delete_namespace_points(client: QdrantClient, collection: str):
    """Delete all existing sn_mcp points from the collection."""
    try:
        client.delete(
            collection_name=collection,
            points_selector=Filter(
                must=[FieldCondition(key="namespace_id", match=MatchValue(value=NAMESPACE))]
            ),
        )
        print(f"Deleted existing '{NAMESPACE}' points from '{collection}'.")
    except Exception as e:
        print(f"Note: Could not delete existing points: {e}")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Index ServiceNow docs into Qdrant")
    parser.add_argument("--rebuild", action="store_true", help="Delete existing sn_mcp points first")
    parser.add_argument("--collection", default="sn_mcp_docs", help="Qdrant collection name")
    parser.add_argument("--qdrant-url", default=os.getenv("QDRANT_URL", "http://localhost:6333"))
    parser.add_argument("--batch-size", type=int, default=32, help="Embedding batch size")
    parser.add_argument("--docs-only", action="store_true", help="Only index docs/ (skip schulungen, consulting)")
    args = parser.parse_args()

    # 1. Scan all sources
    print("Scanning documents...")
    all_chunks = []
    all_chunks.extend(scan_docs_directory(DOCS_DIR))
    if not args.docs_only:
        all_chunks.extend(scan_schulungen(SCHULUNGEN_DIR))
        all_chunks.extend(scan_consulting(CONSULTING_DIR))

    print(f"\nTotal: {len(all_chunks)} chunks to embed")
    if not all_chunks:
        print("No chunks found. Exiting.")
        return

    # 2. Embed all chunks
    print("\nEmbedding chunks with BGE-M3...")
    embedder = Embedder(batch_size=args.batch_size)
    texts = [c["content"] for c in all_chunks]
    t0 = time.time()
    embeddings = embedder.embed(texts)
    dt = time.time() - t0
    print(f"Embedding done: {len(embeddings)} vectors in {dt:.1f}s ({len(embeddings)/dt:.0f} chunks/s)")

    # 3. Upsert to Qdrant
    print(f"\nUpserting to Qdrant ({args.qdrant_url}, collection={args.collection})...")
    client = QdrantClient(url=args.qdrant_url)

    if args.rebuild:
        delete_namespace_points(client, args.collection)

    upsert_to_qdrant(client, args.collection, all_chunks, embeddings)

    # 4. Print summary
    info = client.get_collection(args.collection)
    print(f"\nCollection '{args.collection}' now has {info.points_count} total points.")
    print("Done.")


if __name__ == "__main__":
    main()
