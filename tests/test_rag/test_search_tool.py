"""
Unit tests for src/agents/tools/example_tool.py — search_knowledge tool.

Verifies the tool is correctly wired to rag.query_handbook without
exercising ChromaDB or OpenAI.
"""

from unittest.mock import patch

import pytest


class TestSearchKnowledgeTool:
    def test_tool_is_callable(self):
        from src.agents.tools.example_tool import search_knowledge
        # LangChain StructuredTool is not a plain function — check it has .invoke
        assert hasattr(search_knowledge, "invoke")

    def test_tool_has_correct_name(self):
        from src.agents.tools.example_tool import search_knowledge
        assert search_knowledge.name == "search_knowledge"

    def test_tool_delegates_to_query_handbook(self):
        """search_knowledge must forward its query to rag.query_handbook."""
        # Patch WHERE the name is looked up (already bound in example_tool module).
        with patch("src.agents.tools.example_tool.query_handbook", return_value="Mocked answer") as mock_qh:
            from src.agents.tools.example_tool import search_knowledge
            result = search_knowledge.invoke({"query": "parking rules"})

        mock_qh.assert_called_once_with("parking rules")
        assert result == "Mocked answer"

    def test_tool_passes_query_string_through(self):
        """The exact query string must be forwarded unchanged."""
        question = "What are the move-out procedures?"
        with patch("src.agents.tools.example_tool.query_handbook", return_value="Some answer") as mock_qh:
            from src.agents.tools.example_tool import search_knowledge
            search_knowledge.invoke({"query": question})

        mock_qh.assert_called_once_with(question)

    def test_tool_returns_string(self):
        with patch("src.agents.tools.example_tool.query_handbook", return_value="Electricity deposit is VND 500,000."):
            from src.agents.tools.example_tool import search_knowledge
            result = search_knowledge.invoke({"query": "electricity deposit"})

        assert isinstance(result, str)
        assert "500,000" in result
