"""
Unit tests for scripts/ingest_handbook.py.

No real OpenAI API calls. No real disk writes.
Uses pytest tmp_path fixture to isolate file operations.
"""

import hashlib
from pathlib import Path
from unittest.mock import MagicMock, patch

from llama_index.core import Document

# Import helpers directly — avoids running the __main__ block.
from scripts.ingest_handbook import (
    MIN_NODE_WORDS,
    MIN_PDF_PAGE_WORDS,
    compute_file_hash,
    evaluate_ocr_quality,
    export_pdf_to_markdown,
    extract_page_tables_as_markdown,
    load_pdf_document_hybrid,
    ocr_pdf_page_with_qwen,
    quality_gate,
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

    def test_export_pdf_to_markdown_includes_audit_flags(self, tmp_path: Path):
        source = tmp_path / "handbook.pdf"
        source.write_bytes(b"%PDF-1.4 sample content")

        doc = Document(
            text="Sample text content for page",
            metadata={
                "page_number": 1,
                "is_ocr": True,
                "ocr_confidence": 0.5,
                # warning_flags is always a comma-separated string (ChromaDB scalar constraint)
                "warning_flags": "HIGH_SYMBOL_NOISE",
                "needs_human_audit": True,
            }
        )

        out_dir = tmp_path / "processed"
        out_file = export_pdf_to_markdown([doc], source, output_dir=out_dir)
        content = out_file.read_text(encoding="utf-8")
        assert "<!-- Page 1 (Qwen OCR) [AUDIT_REQUIRED: HIGH_SYMBOL_NOISE] -->" in content


class TestEvaluateOCRQuality:
    def test_clean_text_passes(self):
        text = "Điều 1: Quy định chung về giờ yên tĩnh tại chung cư Phú Đông Sky Garden. Tất cả cư dân phải tuân thủ."
        res = evaluate_ocr_quality(text)
        assert res["is_passed"] is True
        assert res["confidence_score"] > 0.8
        assert res["warning_flags"] == []

    def test_garbled_symbol_noise_fails(self):
        text = "????? @@@ ### $$$ %%% 123 !@#$ %^&* ()(*&^%"
        res = evaluate_ocr_quality(text)
        assert res["is_passed"] is False
        assert "HIGH_SYMBOL_NOISE" in res["warning_flags"]

    def test_low_word_count_fails(self):
        text = "Trang 5"
        res = evaluate_ocr_quality(text)
        assert res["is_passed"] is False
        assert "LOW_WORD_COUNT" in res["warning_flags"]


class TestAuditCLI:
    def test_run_audit_scan_detects_flagged_pages(self, tmp_path: Path, capsys):
        md_file = tmp_path / "sample_doc.md"
        md_file.write_text(
            "# sample_doc\n\n"
            "<!-- Page 1 -->\nClean page text\n\n"
            "<!-- Page 2 (Qwen OCR) [AUDIT_REQUIRED: HIGH_SYMBOL_NOISE] -->\nGarbled text\n",
            encoding="utf-8"
        )
        flagged_count = run_audit_scan(processed_dir=tmp_path)
        captured = capsys.readouterr()
        assert flagged_count == 1
        assert "Audit Scan Summary" in captured.out
        assert "Page 2" in captured.out
        assert "HIGH_SYMBOL_NOISE" in captured.out


class TestMultiTenantIngestion:
    @patch("scripts.ingest_handbook.fitz")
    def test_load_pdf_hybrid_includes_building_id(self, mock_fitz, tmp_path: Path):
        mock_doc = MagicMock()
        mock_fitz.open.return_value = mock_doc
        mock_doc.__len__.return_value = 1

        mock_page = MagicMock()
        mock_doc.__getitem__.return_value = mock_page
        mock_page.get_text.return_value = "Word " * (MIN_PDF_PAGE_WORDS + 10)

        pdf_path = tmp_path / "custom_building.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 sample content")

        mock_settings = MagicMock()
        docs = load_pdf_document_hybrid(pdf_path, mock_settings, building_id="vinhomes_central")

        assert len(docs) == 1
        assert docs[0].metadata["building_id"] == "vinhomes_central"


class TestComplexTableParsing:
    def test_extract_page_tables_no_tables(self):
        mock_page = MagicMock()
        mock_page.find_tables.return_value.tables = []
        md_text, count = extract_page_tables_as_markdown(mock_page)
        assert md_text == ""
        assert count == 0

    def test_extract_page_tables_with_table(self):
        mock_page = MagicMock()
        mock_table = MagicMock()
        mock_table.to_markdown.return_value = "| Vehicle | Monthly Fee |\n|---|---|\n| Car | 1,200,000 |"
        mock_page.find_tables.return_value.tables = [mock_table]

        md_text, count = extract_page_tables_as_markdown(mock_page)
        assert count == 1
        assert "| Vehicle | Monthly Fee |" in md_text
        assert "| Car | 1,200,000 |" in md_text
