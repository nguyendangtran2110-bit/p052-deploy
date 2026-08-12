"""
Unit/integration tests for src/services/rag.py.

ChromaDB is mocked — no real vector store is accessed.
OpenAI is NOT called.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Graceful degradation: vector store directory does not exist
# ---------------------------------------------------------------------------

class TestQueryHandbookDegradation:
    def test_returns_safe_message_when_store_missing(self, tmp_path: Path):
        """If the chroma persist dir doesn't exist, we get a friendly message."""
        missing_dir = str(tmp_path / "no_such_dir")
        from src.services import rag
        if hasattr(rag._build_query_engine, "cache_clear"):
            rag._build_query_engine.cache_clear()
        with patch("src.services.rag._get_persist_dir", return_value=missing_dir):
            result = rag.query_handbook("What are the quiet hours?")

        assert isinstance(result, str)
        assert len(result) > 0
        # Should NOT raise; should contain a human-friendly message
        assert "not available" in result.lower() or "contact" in result.lower()


# ---------------------------------------------------------------------------
# Happy path: mocked vector store returns an answer
# ---------------------------------------------------------------------------

class TestQueryHandbookHappyPath:
    def test_returns_string_answer(self, tmp_path: Path):
        """When the store exists, query_handbook returns a string."""
        # Create the directory so the existence check passes.
        persist_dir = str(tmp_path / "chroma")
        Path(persist_dir).mkdir()

        mock_response = MagicMock()
        mock_response.__str__ = lambda self: "Quiet hours are 22:00-06:00 on weekdays."

        mock_engine = MagicMock()
        mock_engine.query.return_value = mock_response

        with (
            patch("src.services.rag._get_persist_dir", return_value=persist_dir),
            patch("src.services.rag._build_query_engine", return_value=mock_engine),
        ):
            # Clear lru_cache before each call so our mock is used.
            from src.services import rag
            rag._build_query_engine.cache_clear() if hasattr(rag._build_query_engine, "cache_clear") else None

            result = rag.query_handbook("What are the quiet hours?")

        assert isinstance(result, str)
        assert len(result) > 0

    def test_engine_receives_exact_query(self, tmp_path: Path):
        persist_dir = str(tmp_path / "chroma2")
        Path(persist_dir).mkdir()

        mock_response = MagicMock()
        mock_response.__str__ = lambda self: "Parking deposit is VND 200,000."

        mock_engine = MagicMock()
        mock_engine.query.return_value = mock_response

        question = "How do I register my motorbike?"

        with (
            patch("src.services.rag._get_persist_dir", return_value=persist_dir),
            patch("src.services.rag._build_query_engine", return_value=mock_engine),
        ):
            from src.services import rag
            rag.query_handbook(question)

        mock_engine.query.assert_called_once_with(question)


# ---------------------------------------------------------------------------
# Error handling: engine raises an exception
# ---------------------------------------------------------------------------

class TestQueryHandbookErrorHandling:
    def test_returns_safe_message_on_exception(self, tmp_path: Path):
        persist_dir = str(tmp_path / "chroma3")
        Path(persist_dir).mkdir()

        mock_engine = MagicMock()
        mock_engine.query.side_effect = RuntimeError("DB connection failed")

        with (
            patch("src.services.rag._get_persist_dir", return_value=persist_dir),
            patch("src.services.rag._build_query_engine", return_value=mock_engine),
        ):
            from src.services import rag
            result = rag.query_handbook("Will this crash?")

        assert isinstance(result, str)
        assert "RuntimeError" in result or "contact" in result.lower()
