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
import re
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
from src.services.rag import get_chroma_client  # noqa: E402

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


def evaluate_ocr_quality(text: str) -> dict:
    """
    Evaluate extracted page text for OCR quality issues (symbol noise, low word count, missing tables).
    """
    cleaned = (text or "").strip()
    words = cleaned.split()
    word_count = len(words)
    warning_flags = []

    noise_tokens = sum(1 for w in words if not any(c.isalnum() for c in w))
    valid_words = word_count - noise_tokens

    if valid_words < MIN_PDF_PAGE_WORDS:
        warning_flags.append("LOW_WORD_COUNT")

    total_chars = len(cleaned)
    if total_chars > 0:
        symbols = sum(1 for c in cleaned if not c.isalnum() and not c.isspace())
        symbol_ratio = symbols / total_chars
    else:
        symbol_ratio = 1.0

    if symbol_ratio > 0.25 or (word_count > 0 and noise_tokens / word_count > 0.20):
        warning_flags.append("HIGH_SYMBOL_NOISE")

    is_passed = len(warning_flags) == 0
    confidence_score = max(0.0, 1.0 - (0.4 * len(warning_flags)) - (0.3 * min(1.0, symbol_ratio)))

    return {
        "is_passed": is_passed,
        "confidence_score": round(confidence_score, 2),
        "warning_flags": warning_flags,
        "word_count": word_count,
        "valid_words": valid_words,
        "symbol_ratio": round(symbol_ratio, 2),
    }


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
        flags_str = str(doc.metadata.get("warning_flags", "") or "")
        ocr_tag = " (Qwen OCR)" if is_ocr else ""
        audit_tag = f" [AUDIT_REQUIRED: {flags_str}]" if flags_str else ""

        md_lines.append(f"<!-- Page {page_num}{ocr_tag}{audit_tag} -->")
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



def extract_page_tables_as_markdown(page) -> tuple[str, int]:

    """
    Detect PDF grid tables on a page using PyMuPDF (fitz) find_tables().
    Returns (markdown_tables_text, table_count).
    """
    if not hasattr(page, "find_tables"):
        return "", 0

    try:
        tabs = page.find_tables()
        if not tabs or not tabs.tables:
            return "", 0

        md_tables = []
        for tab in tabs.tables:
            md_str = tab.to_markdown()
            if md_str and md_str.strip():
                md_tables.append(md_str.strip())

        if md_tables:
            return "\n\n".join(md_tables), len(md_tables)
    except Exception as e:
        print(f"[ingest] WARNING: Table extraction failed on page: {e}")

    return "", 0


def load_pdf_document_hybrid(filepath: Path, settings, building_id: str = "phu_dong_sky_garden") -> list[Document]:

    """
    Hybrid PDF Loader:
    1. Extracts native text per page using PyMuPDF (fitz).
    2. Detects complex PDF tables and converts them to structured Markdown tables.
    3. If a page has < MIN_PDF_PAGE_WORDS, triggers Qwen Vision OCR fallback.
    """
    if not fitz:
        print(f"[ingest] WARNING: PyMuPDF (fitz) not installed. Falling back to default LlamaIndex loader for {filepath.name}.")
        doc_hash = compute_file_hash(filepath)
        reader = SimpleDirectoryReader(input_files=[str(filepath)])
        docs = reader.load_data()
        for d in docs:
            d.metadata["source_file"] = filepath.name
            d.metadata["file_path"] = str(filepath)
            d.metadata["building_id"] = building_id
            d.metadata["document_hash"] = doc_hash
            d.metadata["has_tables"] = False
            d.metadata["table_count"] = 0
            d.metadata["is_ocr"] = False
            d.metadata["ocr_confidence"] = 1.0
            d.metadata["warning_flags"] = ""
            d.metadata["needs_human_audit"] = False
            d.metadata["version"] = "1.0"
        return docs

    doc_hash = compute_file_hash(filepath)
    # Guard: initialise to None so finally can safely check before calling .close()
    # even if fitz.open() itself raises (e.g. corrupt/locked file).
    pdf_doc = None
    documents = []

    try:
        pdf_doc = fitz.open(filepath)
        for page_idx in range(len(pdf_doc)):
            page = pdf_doc[page_idx]
            native_text = page.get_text("text").strip()
            word_count = len(native_text.split())

            is_ocr = False
            final_text = native_text

            table_md, table_count = extract_page_tables_as_markdown(page)
            has_tables = table_count > 0

            if word_count < MIN_PDF_PAGE_WORDS:
                print(f"[ingest] Page {page_idx + 1}/{len(pdf_doc)} of '{filepath.name}' has low native text ({word_count} words). Triggering Qwen Vision OCR...")
                img_b64 = render_pdf_page_to_base64(page)
                ocr_text = ocr_pdf_page_with_qwen(img_b64, settings)
                if ocr_text.strip():
                    final_text = ocr_text.strip()
                    is_ocr = True
                else:
                    print(f"[ingest] Page {page_idx + 1} OCR returned empty response, keeping native text fallback.")

            if has_tables and not is_ocr:
                final_text = f"{final_text}\n\n### Document Tables\n\n{table_md}".strip()
                print(f"[ingest] Page {page_idx + 1}/{len(pdf_doc)} of '{filepath.name}': Detected {table_count} table(s) -> Converted to Markdown table.")

            ocr_eval = evaluate_ocr_quality(final_text)
            flags_list = ocr_eval["warning_flags"]
            warning_flags_str = ",".join(flags_list) if isinstance(flags_list, list) else str(flags_list or "")
            doc_obj = Document(
                text=final_text,
                metadata={
                    "source_file": filepath.name,
                    "file_path": str(filepath),
                    "page_number": page_idx + 1,
                    "building_id": building_id,
                    "is_ocr": is_ocr,
                    "has_tables": has_tables,
                    "table_count": table_count,
                    "ocr_confidence": ocr_eval["confidence_score"],
                    "warning_flags": warning_flags_str,
                    "needs_human_audit": not ocr_eval["is_passed"],
                    "version": "1.0",
                    "document_hash": doc_hash,
                },
            )

            documents.append(doc_obj)
    finally:
        if pdf_doc is not None:
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
    # When the user explicitly provides a dir_path, trust their intent fully —
    # do NOT silently exclude sub-directories like 'chroma' or 'processed'.
    # Exclusion filters only apply to the automatic default scan.
    explicit_dir = bool(dir_path)
    if explicit_dir:
        search_dirs.append(Path(dir_path).resolve())
    else:
        search_dirs.append(ROOT / "data" / "raw")
        search_dirs.append(ROOT / "data")

    discovered = set()
    for sdir in search_dirs:
        if sdir.exists() and sdir.is_dir():
            for p in sdir.rglob("*"):
                if p.is_file() and p.suffix.lower() in valid_exts and not p.name.startswith("."):
                    if explicit_dir:
                        # User explicitly chose this directory — include everything inside it.
                        discovered.add(p.resolve())
                    else:
                        # Default scan: exclude auto-generated artifacts that should not be re-ingested.
                        if "chroma" not in p.parts and "processed" not in p.parts:
                            discovered.add(p.resolve())

    return sorted(list(discovered), key=lambda x: x.name)



def run_audit_scan(processed_dir: Path = PROCESSED_DATA_DIR) -> int:
    """
    Scan processed markdown files in data/processed/ for audit warning tags.
    Returns the total number of flagged pages.
    """
    if not processed_dir.exists() or not processed_dir.is_dir():
        print(f"[ingest] Audit Directory '{processed_dir}' does not exist.")
        return 0

    audit_pattern = re.compile(r"<!-- Page (\d+)(?: \([^)]+\))? \[AUDIT_REQUIRED: (.*?)\] -->")
    flagged_pages = []

    print("\n[ingest] === Audit Scan Summary ===")
    for md_file in sorted(processed_dir.glob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        matches = audit_pattern.findall(content)
        if matches:
            print(f"Document: {md_file.name}")
            for page_num, flags in matches:
                flagged_pages.append((md_file.name, page_num, flags))
                print(f"  - Page {page_num}: [AUDIT_REQUIRED: {flags}]")

    print(f"Total flagged pages needing human audit: {len(flagged_pages)}\n")
    return len(flagged_pages)


# ---------------------------------------------------------------------------
# Main ingestion logic
# ---------------------------------------------------------------------------

def run_ingestion(
    dry_run: bool = False,
    force_rebuild: bool = False,
    file_path: str = None,
    dir_path: str = None,
    export_md: bool = True,
    export_only: bool = False,
    audit: bool = False,
    building_id: str = "phu_dong_sky_garden",
) -> None:
    if audit:
        run_audit_scan(PROCESSED_DATA_DIR)
        return

    settings = get_settings()
    persist_dir = settings.chroma_persist_dir

    all_raw_files = discover_target_files(file_path=file_path, dir_path=dir_path)

    print(f"[ingest] Discovered   : {len(all_raw_files)} document(s)")
    for f in all_raw_files:
        print(f"           - {f.relative_to(ROOT) if f.is_relative_to(ROOT) else f}")
    print(f"[ingest] Building ID  : {building_id}")
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
    if not settings.chroma_server_host:
        Path(persist_dir).mkdir(parents=True, exist_ok=True)
    db = get_chroma_client(settings, persist_dir)

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
            pdf_docs = load_pdf_document_hybrid(filepath, settings, building_id=building_id)
            if export_md and pdf_docs:
                export_pdf_to_markdown(pdf_docs, filepath)
            raw_documents.extend(pdf_docs)
        else:
            reader = SimpleDirectoryReader(input_files=[str(filepath)])
            file_docs = reader.load_data()
            doc_hash = compute_file_hash(filepath)
            for d in file_docs:
                d.metadata["source_file"] = filepath.name
                d.metadata["building_id"] = building_id
                d.metadata["version"] = "1.0"
                d.metadata["document_hash"] = doc_hash
            raw_documents.extend(file_docs)


    print(f"[ingest] Loaded {len(raw_documents)} raw document page(s)/file(s) for processing.")

    if export_only:
        print("[ingest] EXPORT ONLY complete. Skipping vector store indexing.\n")
        return

    # ------------------------------------------------------------------
    # 4. Heading-aware & Sentence chunking
    # ------------------------------------------------------------------
    md_docs = [d for d in raw_documents if str(d.metadata.get("source_file", "")).endswith(".md") or d.metadata.get("is_ocr")]
    other_docs = [d for d in raw_documents if d not in md_docs]

    nodes = []
    if md_docs:
        md_parser = MarkdownNodeParser()
        raw_md_nodes = md_parser.get_nodes_from_documents(md_docs)
        sentence_splitter = SentenceSplitter(chunk_size=512, chunk_overlap=64)
        md_nodes = sentence_splitter.get_nodes_from_documents(raw_md_nodes)
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
    parser.add_argument(
        "--export-only",
        action="store_true",
        help="Export PDF/OCR output to Markdown in data/processed/ without indexing into vector store.",
    )
    parser.add_argument(
        "--audit",
        action="store_true",
        help="Scan data/processed/ for documents with low-confidence OCR flags requiring human review.",
    )
    parser.add_argument(
        "--building-id", "-b",
        type=str,
        default="phu_dong_sky_garden",
        help="Specify the building ID tag for multi-tenant isolation (default: 'phu_dong_sky_garden').",
    )
    args = parser.parse_args()
    run_ingestion(
        dry_run=args.dry_run,
        force_rebuild=args.force_rebuild,
        file_path=args.file,
        dir_path=args.dir,
        export_md=args.export_md,
        export_only=args.export_only,
        audit=args.audit,
        building_id=args.building_id,
    )




