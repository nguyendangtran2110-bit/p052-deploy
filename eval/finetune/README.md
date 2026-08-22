# OnBxrd Agent Fine-tuning Dataset

This directory contains reproducible synthetic data for the structured
`AgentStructuredResult` contract. It targets intent routing, draft extraction,
missing-field behavior, proposed actions, confirmation boundaries, and basic
guardrails. It does not train handbook facts or backend authorization logic.

## Generated artifacts

- `canonical/{train,validation,test}.jsonl`: provider-neutral source of truth.
- `openai/{train,validation}.jsonl`: supervised fine-tuning rows using the
  `AgentStructuredResult` function-call format.
- `test_cases.json`: held-out cases accepted by `benchmark_llm_models.py`.
- `summary.json`: split, family, language, intent, and action distributions.
- `validation_report.json`: schema, semantic, uniqueness, and leakage checks.

The default generation target is 2,000 train examples, 400 validation examples,
and 600 held-out test examples across 24 scenario families. Each example is one
production-style model call. Multi-turn behavior is represented through persisted
`workflow_draft`, `pending_action`, workflow state, and recent messages.

## Reproduce and validate

```powershell
.\.venv\Scripts\python.exe scripts\generate_ai_finetune_dataset.py
.\.venv\Scripts\python.exe scripts\validate_ai_finetune_dataset.py
```

Run the held-out provider benchmark with explicit output paths:

```powershell
.\.venv\Scripts\python.exe scripts\benchmark_llm_models.py `
  --cases eval\finetune\test_cases.json `
  --report eval\results\finetune_test_report.md `
  --json-output eval\results\finetune_test_results.json
```

The OpenAI JSONL shape follows the supervised chat fine-tuning function-call
format documented at:
https://developers.openai.com/api/reference/resources/fine_tuning

## Review boundary

This is synthetic seed data, not automatically approved production data. Before
uploading a fine-tuning file:

1. Human-review all validation and test examples.
2. Review a stratified sample from every train scenario family.
3. Keep the test split private and unchanged after model selection begins.
4. Add anonymized real failures as new gold cases; do not copy them into test and train.
5. Never add secrets, real resident identifiers, email addresses, or presigned URLs.

`Average contract-check score` is useful for diagnosing partial correctness.
`All-checks pass rate` remains the acceptance metric for a complete case.
