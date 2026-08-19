"""
Unit tests for scripts/ingest_handbook.py.

No real OpenAI API calls. No real disk writes.
Uses pytest tmp_path fixture to isolate file operations.
"""

import hashlib
from pathlib import Path

import pytest

# Import helpers directly — avoids running the __main__ block.
from scripts.ingest_handbook import (
    compute_file_hash,
    quality_gate,
    MIN_NODE_WORDS,
    evaluate_ocr_quality,
    run_audit_scan,
)


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

class _FakeNode:
    """Minimal stand-in for a LlamaIndex TextNode."""
    def __init__(self, text: str):
        self.text = text
        self.node_id = id(self)


# ---------------------------------------------------------------------------
# compute_file_hash
# ---------------------------------------------------------------------------

class TestComputeFileHash:
    def test_returns_hex_string(self, tmp_path: Path):
        f = tmp_path / "doc.txt"
        f.write_bytes(b"hello world")
        result = compute_file_hash(f)
        assert isinstance(result, str)
        assert len(result) == 64  # SHA-256 hex digest length

    def test_deterministic(self, tmp_path: Path):
        f = tmp_path / "doc.txt"
        f.write_bytes(b"hello world")
        assert compute_file_hash(f) == compute_file_hash(f)

    def test_different_content_different_hash(self, tmp_path: Path):
        f1 = tmp_path / "a.txt"
        f2 = tmp_path / "b.txt"
        f1.write_bytes(b"content A")
        f2.write_bytes(b"content B")
        assert compute_file_hash(f1) != compute_file_hash(f2)

    def test_matches_manual_sha256(self, tmp_path: Path):
        content = b"deterministic check"
        f = tmp_path / "c.txt"
        f.write_bytes(content)
        expected = hashlib.sha256(content).hexdigest()
        assert compute_file_hash(f) == expected


# ---------------------------------------------------------------------------
# quality_gate
# ---------------------------------------------------------------------------

class TestQualityGate:
    def test_empty_text_rejected(self):
        node = _FakeNode("")
        valid, rejected = quality_gate([node])
        assert node in rejected
        assert node not in valid

    def test_whitespace_only_rejected(self):
        node = _FakeNode("   \n\t  ")
        valid, rejected = quality_gate([node])
        assert node in rejected

    def test_below_min_words_rejected(self):
        # MIN_NODE_WORDS words - 1 → rejected
        short_text = " ".join(["word"] * (MIN_NODE_WORDS - 1))
        node = _FakeNode(short_text)
        valid, rejected = quality_gate([node])
        assert node in rejected

    def test_exact_min_words_accepted(self):
        text = " ".join(["word"] * MIN_NODE_WORDS)
        node = _FakeNode(text)
        valid, rejected = quality_gate([node])
        assert node in valid
        assert node not in rejected

    def test_long_text_accepted(self):
        long_text = "This is a well-formed handbook section with enough content. " * 5
        node = _FakeNode(long_text)
        valid, rejected = quality_gate([node])
        assert node in valid

    def test_mixed_nodes(self):
        good = _FakeNode("word " * 20)
        bad = _FakeNode("hi")
        valid, rejected = quality_gate([good, bad])
        assert good in valid
        assert bad in rejected
        assert len(valid) == 1
        assert len(rejected) == 1

    def test_all_valid(self):
        nodes = [_FakeNode("word " * 15) for _ in range(5)]
        valid, rejected = quality_gate(nodes)
        assert len(valid) == 5
        assert len(rejected) == 0

    def test_all_rejected(self):
        nodes = [_FakeNode("") for _ in range(3)]
        valid, rejected = quality_gate(nodes)
        assert len(valid) == 0
        assert len(rejected) == 3


# ---------------------------------------------------------------------------
# Hybrid PDF & Qwen OCR tests
# ---------------------------------------------------------------------------

from unittest.mock import MagicMock, patch
from scripts.ingest_handbook import (
    ocr_pdf_page_with_qwen,
    load_pdf_document_hybrid,
    MIN_PDF_PAGE_WORDS,
)


class TestQwenOCR:
    @patch("scripts.ingest_handbook.openai.OpenAI")
    def test_ocr_success(self, mock_openai):
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "## Quiet Hours\nNo noise after 10 PM."
        mock_client.chat.completions.create.return_value = mock_response

        mock_settings = MagicMock()
        mock_settings.qwen_api_key = "fake_key"
        mock_settings.qwen_api_base = "http://fake"
        mock_settings.model_name = "qwen3.6-plus"

        result = ocr_pdf_page_with_qwen("data:image/png;base64,abc", mock_settings)
        assert "Quiet Hours" in result
        assert mock_client.chat.completions.create.called

    @patch("scripts.ingest_handbook.openai.OpenAI")
    def test_ocr_handles_exception(self, mock_openai):
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API error")

        mock_settings = MagicMock()
        result = ocr_pdf_page_with_qwen("data:image/png;base64,abc", mock_settings)
        assert result == ""


class TestHybridPDFLoader:
    @patch("scripts.ingest_handbook.fitz")
    def test_native_text_sufficient(self, mock_fitz, tmp_path: Path):
        mock_doc = MagicMock()
        mock_fitz.open.return_value = mock_doc
        mock_doc.__len__.return_value = 1

        mock_page = MagicMock()
        mock_doc.__getitem__.return_value = mock_page
        mock_page.get_text.return_value = "Word " * (MIN_PDF_PAGE_WORDS + 10)

        pdf_path = tmp_path / "handbook.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 dummy content")

        mock_settings = MagicMock()
        docs = load_pdf_document_hybrid(pdf_path, mock_settings)

        assert len(docs) == 1
        assert docs[0].metadata["is_ocr"] is False
        assert docs[0].metadata["page_number"] == 1

    @patch("scripts.ingest_handbook.ocr_pdf_page_with_qwen")
    @patch("scripts.ingest_handbook.render_pdf_page_to_base64")
    @patch("scripts.ingest_handbook.fitz")
    def test_triggers_ocr_when_low_native_text(self, mock_fitz, mock_render, mock_ocr, tmp_path: Path):
        mock_doc = MagicMock()
        mock_fitz.open.return_value = mock_doc
        mock_doc.__len__.return_value = 1

        mock_page = MagicMock()
        mock_doc[0] = mock_page
        mock_page.get_text.return_value = "scanned text"  # only 2 words < MIN_PDF_PAGE_WORDS

        mock_render.return_value = "data:image/png;base64,fake"
        mock_ocr.return_value = "## OCR Header\nExtracted content from image."

        pdf_path = tmp_path / "scanned.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 dummy scanned content")

        mock_settings = MagicMock()
        docs = load_pdf_document_hybrid(pdf_path, mock_settings)

        assert len(docs) == 1
        assert docs[0].metadata["is_ocr"] is True
        assert "OCR Header" in docs[0].text
        assert mock_ocr.called


from llama_index.core import Document
from scripts.ingest_handbook import export_pdf_to_markdown


class TestExportPDFToMarkdown:
    def test_exports_markdown_file(self, tmp_path: Path):
        source = tmp_path / "handbook.pdf"
        source.write_bytes(b"%PDF-1.4 sample content")

        doc1 = Document(text="## Section 1\nContent line 1", metadata={"page_number": 1, "is_ocr": False})
        doc2 = Document(text="## Section 2\nOCR extracted text", metadata={"page_number": 2, "is_ocr": True})

        out_dir = tmp_path / "processed"
        out_file = export_pdf_to_markdown([doc1, doc2], source, output_dir=out_dir)

        assert out_file.exists()
        assert out_file.name == "handbook.md"

        content = out_file.read_text(encoding="utf-8")
        assert "# handbook" in content
        assert "<!-- Page 1 -->" in content
        assert "<!-- Page 2 (Qwen OCR) -->" in content
        assert "Section 1" in content
        assert "Section 2" in content


