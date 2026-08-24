from __future__ import annotations

import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK_PATH = ROOT / "eval" / "evaluation_analysis.ipynb"
JBB_PATH = ROOT / "eval" / "jailbreakbench-results.json"
DEEPEVAL_PATH = ROOT / "eval" / "deepeval-results.json"


def _sanitize_ipython_magics(source: str) -> str:
    lines: list[str] = []
    for line in source.splitlines(keepends=True):
        stripped = line.lstrip()
        indent = line[: len(line) - len(stripped)]
        if stripped.startswith(("!", "%")):
            lines.append(f"{indent}pass\n")
        elif stripped.startswith("display("):
            # In headless non-IPython exec, display can map to pass or print
            inner = stripped[len("display(") : -1] if stripped.endswith(")") else ""
            lines.append(f"{indent}pass  # display\n")
        else:
            lines.append(line)
    return "".join(lines)


def test_evaluation_analysis_notebook_structure_and_syntax():
    assert NOTEBOOK_PATH.exists(), f"Notebook not found at {NOTEBOOK_PATH}"
    notebook = json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))

    assert notebook["nbformat"] == 4
    assert len(notebook["cells"]) >= 20

    code_cells = [c for c in notebook["cells"] if c["cell_type"] == "code"]
    assert len(code_cells) >= 8

    # Ensure all code cells compile
    for i, cell in enumerate(code_cells):
        code_str = "".join(cell["source"])
        sanitized = _sanitize_ipython_magics(code_str)
        try:
            compile(sanitized, f"cell_{i}", "exec")
        except Exception as e:
            pytest.fail(f"Cell {i} failed syntax compilation: {e}\nCode:\n{code_str}")

    content = NOTEBOOK_PATH.read_text(encoding="utf-8")
    assert "JailbreakBench" in content
    assert "DeepEval" in content
    assert "Tier 1: Fast Guardrail (422)" in content
    assert "Tier 2: LLM Refusal (200)" in content
    assert "Tier 3: Safe RAG Answer (200)" in content
    assert "explore_cases" in content


def test_evaluation_analysis_notebook_headless_execution():
    """Execute the notebook's computational flow and verify all data assertions."""
    notebook = json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))
    code_cells = [c for c in notebook["cells"] if c["cell_type"] == "code"]

    exec_env = {
        "__name__": "__main__",
        "display": lambda *args, **kwargs: None,
    }

    # Execute all code cells in sequence
    for i, cell in enumerate(code_cells):
        code_str = "".join(cell["source"])
        # Mock plt.show to avoid opening GUI windows during tests
        code_str = code_str.replace("plt.show()", "plt.close('all')")
        sanitized = _sanitize_ipython_magics(code_str)
        try:
            exec(sanitized, exec_env)
        except Exception as e:
            pytest.fail(f"Execution failed on code cell {i}: {e}\nCode:\n{code_str}")

    # Verify expected DataFrame variables in execution scope
    assert "df_all" in exec_env
    assert "df_jbb" in exec_env
    assert "df_de" in exec_env

    df_all = exec_env["df_all"]
    df_jbb = exec_env["df_jbb"]
    df_de = exec_env["df_de"]

    # Assert exact data dimensions and metrics
    assert len(df_jbb) == 100
    assert len(df_de) == 100
    assert len(df_all) == 200

    # 100% defense & policy adherence
    assert df_jbb["passed"].all()
    assert df_de["passed"].all()
    assert df_all["passed"].all()

    # Verify tier classifications
    tier1_count = (df_all["defense_tier"] == "Tier 1: Fast Guardrail (422)").sum()
    tier2_count = (df_all["defense_tier"] == "Tier 2: LLM Refusal (200)").sum()
    tier3_count = (df_all["defense_tier"] == "Tier 3: Safe RAG Answer (200)").sum()

    assert tier1_count == 23  # 3 JBB + 20 DeepEval
    assert tier2_count == 164 # 97 JBB + 67 DeepEval
    assert tier3_count == 13  # 13 DeepEval safe answers

    # Verify explore_cases function
    assert "explore_cases" in exec_env
    explore_fn = exec_env["explore_cases"]
    res = explore_fn(df_all, tier="Tier 3", limit=5)
    assert len(res) == 5
    assert (res["defense_tier"] == "Tier 3: Safe RAG Answer (200)").all()
