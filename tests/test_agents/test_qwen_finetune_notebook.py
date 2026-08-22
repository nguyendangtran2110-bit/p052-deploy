from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK_PATH = ROOT / "eval" / "finetune" / "finetune.ipynb"
TUTORIAL_PATH = ROOT / "eval" / "finetune" / "StepByStepTutorial.md"


def _sanitize_ipython_magics(source: str) -> str:
    lines: list[str] = []
    for line in source.splitlines(keepends=True):
        stripped = line.lstrip()
        indent = line[: len(line) - len(stripped)]
        if stripped.startswith(("!", "%")):
            lines.append(f"{indent}pass\n")
        else:
            lines.append(line)
    return "".join(lines)


def test_qwen_qlora_notebook_is_valid_and_has_executable_code_cells():
    notebook = json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))

    assert notebook["nbformat"] == 4
    assert len(notebook["cells"]) >= 20
    code_cells = [cell for cell in notebook["cells"] if cell["cell_type"] == "code"]
    assert code_cells
    for cell in code_cells:
        compile(_sanitize_ipython_magics("".join(cell["source"])), NOTEBOOK_PATH.name, "exec")

    content = NOTEBOOK_PATH.read_text(encoding="utf-8")
    assert "Qwen/Qwen3-4B" in content
    assert "qwen3_nothink" in content
    assert "quantization_bit" in content
    assert "llamafactory-cli train" in content
    assert "all_checks_pass_rate" in content
    assert "base_evaluation_summary.json" in content
    assert "benchmark_comparison.json" in content


def test_qwen_qlora_tutorial_covers_kaggle_and_evaluation_workflow():
    content = TUTORIAL_PATH.read_text(encoding="utf-8")

    for required_text in (
        "Kaggle Dataset",
        "LLaMA-Factory",
        "QLoRA",
        "all-checks pass rate",
        "không nên train nhiều epoch",
    ):
        assert required_text in content
