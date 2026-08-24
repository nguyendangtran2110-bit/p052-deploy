"""
Unit/integration tests for src/services/rag.py.

ChromaDB is mocked — no real vector store is accessed.
OpenAI is NOT called.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

class _FakeNode:
    def __init__(self, text: str, metadata: dict | None = None, score: float = 0.8):
        self.metadata = metadata or {}
        self.score = score
        self._text = text

    def get_content(self) -> str:
        return self._text


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

    def test_retrieve_context_uses_processed_files_when_store_missing(self, tmp_path: Path):
        missing_dir = str(tmp_path / "no_such_dir")
        with (
            patch("src.services.rag._get_persist_dir", return_value=missing_dir),
            patch("src.services.rag.PROCESSED_DATA_DIR", tmp_path),
        ):
            (tmp_path / "handbook.md").write_text("Hồ bơi mở cửa từ 06:00 đến 22:00.", encoding="utf-8")
            from src.services import rag
            chunks = rag.retrieve_context("giờ mở cửa hồ bơi")
        assert len(chunks) == 1
        assert "06:00" in chunks[0].text


# ---------------------------------------------------------------------------
# Happy path: mocked vector store returns an answer
# ---------------------------------------------------------------------------

class TestQueryHandbookHappyPath:
    def test_returns_string_answer(self, tmp_path: Path):
        """When the store exists, query_handbook returns a string."""
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
            from src.services import rag
            if hasattr(rag._build_query_engine, "cache_clear"):
                rag._build_query_engine.cache_clear()

            result = rag.query_handbook("What are the quiet hours?")

        assert isinstance(result, str)
        assert len(result) > 0
        assert "Quiet hours" in result

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
# retrieve_context tests
# ---------------------------------------------------------------------------

class TestRetrieveContext:
    def test_retrieve_context_returns_chunks(self, tmp_path: Path):
        persist_dir = str(tmp_path / "chroma_ctx")
        Path(persist_dir).mkdir()

        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = [
            _FakeNode(
                "Quiet hours are 22:00-06:00 on weekdays.",
                {"source_file": "handbook.pdf", "page_number": 12, "section_title": "Quiet hours"},
                score=0.92,
            )
        ]

        with (
            patch("src.services.rag._get_persist_dir", return_value=persist_dir),
            patch("src.services.rag._collection_count", return_value=1),
            patch("src.services.rag._build_retriever", return_value=mock_retriever),
        ):
            from src.services import rag
            chunks = rag.retrieve_context("What are the quiet hours?", top_k=5)

        assert len(chunks) == 1
        assert chunks[0].text == "Quiet hours are 22:00-06:00 on weekdays."
        assert chunks[0].source_file == "handbook.pdf"
        assert chunks[0].page_number == 12
        assert chunks[0].section_title == "Quiet hours"
        assert chunks[0].score == 0.92
        chunk_dict = chunks[0].to_dict()
        assert chunk_dict["source_file"] == "handbook.pdf"
        assert chunk_dict["score"] == 0.92


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


# ---------------------------------------------------------------------------
# Dual-Mode: PersistentClient vs HttpClient Selection
# ---------------------------------------------------------------------------

class TestChromaDualMode:
    @patch("chromadb.PersistentClient")
    def test_get_chroma_client_persistent_mode(self, mock_persistent, tmp_path: Path):
        """When chroma_server_host is empty, get_chroma_client instantiates PersistentClient."""
        from src.services.rag import get_chroma_client
        mock_settings = MagicMock()
        mock_settings.chroma_server_host = ""
        persist_dir = str(tmp_path / "chroma_local")

        client = get_chroma_client(mock_settings, persist_dir)
        assert client is not None
        mock_persistent.assert_called_once_with(path=persist_dir)

    @patch("chromadb.HttpClient")
    def test_get_chroma_client_http_mode(self, mock_http):
        """When chroma_server_host is set, get_chroma_client instantiates HttpClient."""
        from src.services.rag import get_chroma_client
        mock_settings = MagicMock()
        mock_settings.chroma_server_host = "chromadb"
        mock_settings.chroma_server_port = 8000
        mock_settings.chroma_server_ssl = False

        client = get_chroma_client(mock_settings, "./data/chroma")
        assert client is not None
        mock_http.assert_called_once_with(host="chromadb", port=8000, ssl=False)


# ---------------------------------------------------------------------------
# Multi-Tenant Metadata Filtering
# ---------------------------------------------------------------------------

class TestMultiTenantRetrieval:
    @patch("src.services.rag._build_query_engine")
    def test_query_handbook_passes_building_id(self, mock_build_engine, tmp_path: Path):
        persist_dir = str(tmp_path / "chroma_mt")
        Path(persist_dir).mkdir()

        mock_engine = MagicMock()
        mock_build_engine.return_value = mock_engine
        mock_engine.query.return_value = "Filtered building answer"

        with patch("src.services.rag._get_persist_dir", return_value=persist_dir):
            from src.services import rag
            res = rag.query_handbook("Parking fee?", building_id="vinhomes_central")

        mock_build_engine.assert_called_once_with(persist_dir, building_id="vinhomes_central")
        assert res == "Filtered building answer"


# ---------------------------------------------------------------------------
# Qdrant Vector Store Mode
# ---------------------------------------------------------------------------

class TestQdrantMode:
    def test_is_qdrant_enabled_detection(self):
        from src.services.rag import is_qdrant_enabled

        mock_settings = MagicMock()
        mock_settings.vector_store_type = "auto"
        mock_settings.qdrant_url = ""
        assert is_qdrant_enabled(mock_settings) is False

        mock_settings.qdrant_url = "https://example.cloud.qdrant.io:6333"
        assert is_qdrant_enabled(mock_settings) is True

        mock_settings.vector_store_type = "qdrant"
        mock_settings.qdrant_url = ""
        assert is_qdrant_enabled(mock_settings) is True

        mock_settings.vector_store_type = "chroma"
        mock_settings.qdrant_url = "https://example.cloud.qdrant.io:6333"
        assert is_qdrant_enabled(mock_settings) is False

    @patch("qdrant_client.QdrantClient")
    def test_get_qdrant_client_instantiation(self, mock_qdrant_cls):
        from src.services.rag import get_qdrant_client

        mock_settings = MagicMock()
        mock_settings.qdrant_url = "https://xyz.cloud.qdrant.io:6333"
        mock_settings.qdrant_api_key = "test-qdrant-key"

        client = get_qdrant_client(mock_settings)
        assert client is not None
        mock_qdrant_cls.assert_called_once_with(url="https://xyz.cloud.qdrant.io:6333", api_key="test-qdrant-key")

    @patch("src.services.rag.get_qdrant_client")
    def test_collection_count_with_qdrant(self, mock_get_client):
        from src.services.rag import _collection_count

        mock_settings = MagicMock()
        mock_settings.vector_store_type = "qdrant"
        mock_settings.qdrant_url = "https://xyz.cloud.qdrant.io:6333"
        mock_settings.qdrant_collection_name = "resident_handbook"

        mock_client = MagicMock()
        mock_info = MagicMock()
        mock_info.points_count = 42
        mock_client.get_collection.return_value = mock_info
        mock_get_client.return_value = mock_client

        count = _collection_count(mock_settings, "./data/chroma")
        assert count == 42
        mock_client.get_collection.assert_called_once_with(collection_name="resident_handbook")

    def test_ensure_qdrant_payload_index(self):
        from src.services.rag import ensure_qdrant_payload_index

        mock_client = MagicMock()
        ensure_qdrant_payload_index(mock_client, "test_collection", "building_id")
        mock_client.create_payload_index.assert_called_once()

    def test_ensure_qdrant_payload_index_handles_exception(self):
        from src.services.rag import ensure_qdrant_payload_index

        mock_client = MagicMock()
        mock_client.create_payload_index.side_effect = RuntimeError("Index already exists")
        # Should not raise
        ensure_qdrant_payload_index(mock_client, "test_collection", "building_id")

