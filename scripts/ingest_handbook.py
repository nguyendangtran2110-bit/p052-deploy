#!/usr/bin/env python3
"""
Offline ingestion script for the Resident Handbook.

Reads all documents from data/raw/, applies quality gates, chunks them
using heading-aware parsing, attaches metadata, then upserts into a
persistent ChromaDB collection.

Run this script once before starting the API, or re-run whenever the
handbook is updated. It is idempotent: each run clears and rebuilds the
collection.

Usage:
    python scripts/ingest_handbook.py [--dry-run]

Env:
    CHROMA_PERSIST_DIR  override the default from src/config.py
    OPENAI_API_KEY      required for embedding (read from .env automatically)
"""

import argparse
import base64
import hashlib
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Bootstrap: add repo root to sys.path so `src.*` imports work when the
# script is run directly (i.e. not as a package).
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

from src.config import get_settings  # noqa: E402

# ---------------------------------------------------------------------------
# LlamaIndex & Third-Party imports
# ---------------------------------------------------------------------------
from llama_index.core import (  # noqa: E402
    Document,
    SimpleDirectoryReader,
    StorageContext,
    VectorStoreIndex,
)
from llama_index.embeddings.openai import OpenAIEmbedding  # noqa: E402
from llama_index.core.node_parser import MarkdownNodeParser, SentenceSplitter  # noqa: E402
from llama_index.vector_stores.chroma import ChromaVectorStore  # noqa: E402
import chromadb  # noqa: E402
import openai  # noqa: E402

try:
    import pymupdf as fitz  # PyMuPDF
except ImportError:
    fitz = None

RAW_DATA_DIR = ROOT / "data" / "raw"
PROCESSED_DATA_DIR = ROOT / "data" / "processed"
COLLECTION_NAME = "resident_handbook"
MIN_NODE_WORDS = 10  # Quality gate: nodes below this are discarded
MIN_PDF_PAGE_WORDS = 15  # PDF Native text quality gate per page


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def compute_file_hash(filepath: Path) -> str:
    """Compute a stable SHA-256 hash of a file's raw bytes."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def export_pdf_to_markdown(documents: list[Document], source_filepath: Path, output_dir: Path = PROCESSED_DATA_DIR) -> Path:
    """
    Save parsed PDF pages / OCR Markdown into an intermediate .md file
    in data/processed/ for human inspection, audit, and reusable ingestion.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    out_name = f"{source_filepath.stem}.md"
    out_path = output_dir / out_name

    md_lines = [
        f"# {source_filepath.stem}",
        f"",
        f"> **Source File**: `{source_filepath.name}`  ",
        f"> **Generated Hash**: `{compute_file_hash(source_filepath)[:16]}`  ",
        f"",
        "---",
        "",
    ]

    for doc in documents:
        page_num = doc.metadata.get("page_number", 1)
        is_ocr = doc.metadata.get("is_ocr", False)
        ocr_tag = " (Qwen OCR)" if is_ocr else ""
        
        md_lines.append(f"<!-- Page {page_num}{ocr_tag} -->")
        md_lines.append(doc.text or "")
        md_lines.append("")

    content = "\n".join(md_lines).strip() + "\n"
    out_path.write_text(content, encoding="utf-8")
    print(f"[ingest] Exported Markdown document: {out_path}")
    return out_path



def quality_gate(nodes: list) -> tuple[list, list]:
    """
    Split nodes into (valid, rejected).

    A node is rejected when:
    - Its text is empty / whitespace-only.
    - It contains fewer than MIN_NODE_WORDS words (likely OCR noise or headers).
    """
    valid, rejected = [], []
    for node in nodes:
        text = (node.text or "").strip()
        word_count = len(text.split())
        if word_count >= MIN_NODE_WORDS:
            valid.append(node)
        else:
            rejected.append(node)
    return valid, rejected


def render_pdf_page_to_base64(page) -> str:
    """Render a PyMuPDF PDF page to a PNG base64 data URI."""
    pix = page.get_pixmap(dpi=150)
    img_bytes = pix.tobytes("png")
    b64_str = base64.b64encode(img_bytes).decode("utf-8")
    return f"data:image/png;base64,{b64_str}"


def ocr_pdf_page_with_qwen(image_data_uri: str, settings) -> str:
    """
    Call Qwen Vision API (via OpenAI-compatible DashScope endpoint) to OCR a page image
    into structured Markdown format.
    """
    api_key = settings.qwen_api_key or settings.openai_api_key
    base_url = settings.qwen_api_base or settings.openai_api_base
    client = openai.OpenAI(api_key=api_key, base_url=base_url)

    model_name = settings.model_name or "qwen3.6-plus"

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Act as an expert OCR system. Extract all text from this document page, "
                                "preserving headers (`#`, `##`), lists, tables, and exact wording in clean Markdown."
                            ),
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": image_data_uri},
                        },
                    ],
                }
            ],
            temperature=0.1,
        )
        return response.choices[0].message.content or ""
    except Exception as e:
        print(f"[ingest] WARNING: Qwen Vision OCR failed: {e}")
        return ""


def load_pdf_document_hybrid(filepath: Path, settings) -> list[Document]:
    """
    Hybrid PDF Loader:
    1. Extracts native text per page using PyMuPDF (fitz).
    2. If a page has < MIN_PDF_PAGE_WORDS, triggers Qwen Vision OCR fallback.
    """
    if not fitz:
        print(f"[ingest] WARNING: PyMuPDF (fitz) not installed. Falling back to default LlamaIndex loader for {filepath.name}.")
        reader = SimpleDirectoryReader(input_files=[str(filepath)])
        return reader.load_data()

    doc_hash = compute_file_hash(filepath)
    pdf_doc = fitz.open(filepath)
    documents = []

    for page_idx in range(len(pdf_doc)):
        page = pdf_doc[page_idx]
        native_text = page.get_text("text").strip()
        word_count = len(native_text.split())

        is_ocr = False
        final_text = native_text

        if word_count < MIN_PDF_PAGE_WORDS:
            print(f"[ingest] Page {page_idx + 1}/{len(pdf_doc)} of '{filepath.name}' has low native text ({word_count} words). Triggering Qwen Vision OCR...")
            img_b64 = render_pdf_page_to_base64(page)
            ocr_text = ocr_pdf_page_with_qwen(img_b64, settings)
            if ocr_text.strip():
                final_text = ocr_text.strip()
                is_ocr = True
            else:
                print(f"[ingest] Page {page_idx + 1} OCR returned empty response, keeping native text fallback.")

        doc_obj = Document(
            text=final_text,
            metadata={
                "source_file": filepath.name,
                "file_path": str(filepath),
                "page_number": page_idx + 1,
                "is_ocr": is_ocr,
                "version": "1.0",
                "document_hash": doc_hash,
            },
        )
        documents.append(doc_obj)

    pdf_doc.close()
    return documents


# ---------------------------------------------------------------------------
# File Discovery Helper
# ---------------------------------------------------------------------------

def discover_target_files(file_path: str = None, dir_path: str = None) -> list[Path]:
    """
    Discover target files for ingestion.
    - If file_path is provided: returns [file_path] if it exists.
    - If dir_path is provided: scans dir_path recursively for .pdf, .md, .txt.
    - If neither is provided: checks ROOT / 'data' / 'raw', ROOT / 'data' / 'processed', and ROOT / 'data'.
    """
    valid_exts = {".pdf", ".md", ".txt"}
    if file_path:
        p = Path(file_path).resolve()
        if p.exists() and p.is_file():
            return [p]
        print(f"[ingest] ERROR: Specified file '{file_path}' does not exist. Aborting.")
        sys.exit(1)

    search_dirs = []
    if dir_path:
        search_dirs.append(Path(dir_path).resolve())
    else:
        search_dirs.append(ROOT / "data" / "raw")
        search_dirs.append(ROOT / "data" / "processed")
        search_dirs.append(ROOT / "data")

    discovered = set()
    for sdir in search_dirs:
        if sdir.exists() and sdir.is_dir():
            for p in sdir.rglob("*"):
                if p.is_file() and p.suffix.lower() in valid_exts and not p.name.startswith("."):
                    # Exclude files inside chroma vector store directory
                    if "chroma" not in p.parts:
                        discovered.add(p.resolve())

    return sorted(list(discovered), key=lambda x: x.name)


# ---------------------------------------------------------------------------
# Main ingestion logic
# ---------------------------------------------------------------------------

def run_ingestion(
    dry_run: bool = False,
    force_rebuild: bool = False,
    file_path: str = None,
    dir_path: str = None,
    export_md: bool = True,
) -> None:
    settings = get_settings()
    persist_dir = settings.chroma_persist_dir

    all_raw_files = discover_target_files(file_path=file_path, dir_path=dir_path)

    print(f"[ingest] Discovered   : {len(all_raw_files)} document(s)")
    for f in all_raw_files:
        print(f"           - {f.relative_to(ROOT) if f.is_relative_to(ROOT) else f}")
    print(f"[ingest] Vector store : {persist_dir}")
    print(f"[ingest] Collection   : {COLLECTION_NAME}")
    print(f"[ingest] Export MD    : {export_md}")
    if dry_run:
        print("[ingest] DRY RUN -- no changes will be written.\n")
    if force_rebuild:
        print("[ingest] FORCE REBUILD -- existing collection will be dropped.\n")

    if not all_raw_files:
        print("[ingest] ERROR: No valid document files found (.pdf, .md, .txt). Aborting.")
        sys.exit(1)

    # ------------------------------------------------------------------
    # 1. Connect to ChromaDB & check existing indexed files / hashes
    # ------------------------------------------------------------------
    Path(persist_dir).mkdir(parents=True, exist_ok=True)
    db = chromadb.PersistentClient(path=persist_dir)

    existing_collections = [c.name for c in db.list_collections()]
    if force_rebuild and COLLECTION_NAME in existing_collections:
        db.delete_collection(COLLECTION_NAME)
        print(f"[ingest] Dropped existing collection '{COLLECTION_NAME}'.")
        existing_collections.remove(COLLECTION_NAME)

    chroma_collection = db.get_or_create_collection(COLLECTION_NAME)
    
    # Map of source_file -> document_hash stored in vector DB
    indexed_hashes: dict[str, str] = {}
    if COLLECTION_NAME in existing_collections:
        try:
            records = chroma_collection.get(include=["metadatas"])
            for meta in records.get("metadatas", []) or []:
                if meta and "source_file" in meta and "document_hash" in meta:
                    indexed_hashes[meta["source_file"]] = meta["document_hash"]
        except Exception as e:
            print(f"[ingest] WARNING: Could not read existing collection metadata: {e}")

    # ------------------------------------------------------------------
    # 2. Apply incremental hash filtering
    # ------------------------------------------------------------------
    files_to_process = []
    files_to_remove = []

    for filepath in all_raw_files:
        filename = filepath.name
        current_hash = compute_file_hash(filepath)

        if filename in indexed_hashes:
            if indexed_hashes[filename] == current_hash and not force_rebuild:
                print(f"[ingest] Skipping '{filename}' (unchanged document_hash).")
                continue
            else:
                print(f"[ingest] Document '{filename}' has changed. Will re-index.")
                files_to_remove.append(filename)

        files_to_process.append(filepath)

    if not files_to_process:
        print("[ingest] All documents are up to date in the vector store. Nothing to ingest.")
        return

    # ------------------------------------------------------------------
    # 3. Load & parse candidate documents
    # ------------------------------------------------------------------
    raw_documents = []
    for filepath in files_to_process:
        if filepath.suffix.lower() == ".pdf":
            pdf_docs = load_pdf_document_hybrid(filepath, settings)
            if export_md and pdf_docs:
                export_pdf_to_markdown(pdf_docs, filepath)
            raw_documents.extend(pdf_docs)
        else:
            reader = SimpleDirectoryReader(input_files=[str(filepath)])
            file_docs = reader.load_data()
            doc_hash = compute_file_hash(filepath)
            for d in file_docs:
                d.metadata["source_file"] = filepath.name
                d.metadata["version"] = "1.0"
                d.metadata["document_hash"] = doc_hash
            raw_documents.extend(file_docs)

    print(f"[ingest] Loaded {len(raw_documents)} raw document page(s)/file(s) for processing.")

    # ------------------------------------------------------------------
    # 4. Heading-aware & Sentence chunking
    # ------------------------------------------------------------------
    md_docs = [d for d in raw_documents if str(d.metadata.get("source_file", "")).endswith(".md") or d.metadata.get("is_ocr")]
    other_docs = [d for d in raw_documents if d not in md_docs]

    nodes = []
    if md_docs:
        md_parser = MarkdownNodeParser()
        md_nodes = md_parser.get_nodes_from_documents(md_docs)
        for node in md_nodes:
            if node.metadata.get("Header 1"):
                node.metadata["section_title"] = node.metadata.get("Header 2") or node.metadata.get("Header 1", "")
        nodes.extend(md_nodes)
        print(f"[ingest] Markdown / OCR nodes parsed: {len(md_nodes)}")

    if other_docs:
        sentence_parser = SentenceSplitter(chunk_size=512, chunk_overlap=64)
        other_nodes = sentence_parser.get_nodes_from_documents(other_docs)
        nodes.extend(other_nodes)
        print(f"[ingest] Sentence-split nodes parsed: {len(other_nodes)}")

    # ------------------------------------------------------------------
    # 5. Quality gate on nodes (post-parse)
    # ------------------------------------------------------------------
    valid_nodes, rejected_nodes = quality_gate(nodes)
    if rejected_nodes:
        print(f"[ingest] Quality gate rejected {len(rejected_nodes)} node(s):")
        for n in rejected_nodes:
            snippet = (n.text or "").strip()[:60].replace("\n", " ")
            print(f"           - '{snippet}...'")
    print(f"[ingest] Valid nodes for embedding: {len(valid_nodes)}")

    if dry_run:
        print("\n[ingest] DRY RUN complete. No data written.")
        return

    if not valid_nodes:
        print("[ingest] ERROR: No valid nodes to index. Aborting.")
        sys.exit(1)

    # ------------------------------------------------------------------
    # 6. Incremental Vector Store Indexing
    # ------------------------------------------------------------------
    # Remove stale records for updated files before adding new nodes
    for fname in files_to_remove:
        try:
            chroma_collection.delete(where={"source_file": fname})
            print(f"[ingest] Removed stale vectors for updated file '{fname}'.")
        except Exception as e:
            print(f"[ingest] WARNING: Could not delete stale vectors for '{fname}': {e}")

    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    api_key = settings.qwen_api_key or settings.openai_api_key
    base_url = settings.qwen_api_base or settings.openai_api_base
    embed_model = OpenAIEmbedding(
        model_name=settings.embedding_model_name,
        api_key=api_key,
        api_base=base_url,
        embed_batch_size=10,
    )

    print(f"[ingest] Embedding and indexing {len(valid_nodes)} nodes with model '{settings.embedding_model_name}' ...")
    VectorStoreIndex(valid_nodes, storage_context=storage_context, embed_model=embed_model)

    print(f"[ingest] Done. Indexed {len(valid_nodes)} nodes into '{COLLECTION_NAME}' at '{persist_dir}'.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Ingest resident handbook documents into the ChromaDB vector store."
    )
    parser.add_argument(
        "--file", "-f",
        type=str,
        default=None,
        help="Specify a single PDF, Markdown, or text file to ingest (e.g. data/so-tay-phu-dong-sky-garden.pdf).",
    )
    parser.add_argument(
        "--dir", "-d",
        type=str,
        default=None,
        help="Specify a custom folder containing documents to ingest.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and validate documents without writing to the vector store.",
    )
    parser.add_argument(
        "--force-rebuild",
        action="store_true",
        help="Drop and rebuild the vector store collection from scratch.",
    )
    parser.add_argument(
        "--export-md",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Automatically export parsed PDF / OCR output to Markdown files in data/processed/ (default: True).",
    )
    args = parser.parse_args()
    run_ingestion(
        dry_run=args.dry_run,
        force_rebuild=args.force_rebuild,
        file_path=args.file,
        dir_path=args.dir,
        export_md=args.export_md,
    )



