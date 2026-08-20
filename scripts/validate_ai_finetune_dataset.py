from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.agents.contracts import AgentStructuredResult  # noqa: E402

DEFAULT_DATASET = ROOT / "eval" / "finetune"
SIDE_EFFECT_ACTIONS = {
    "create_ticket",
    "create_announcement_draft",
    "update_announcement",
    "publish_announcement",
}
KNOWN_ACTIONS = SIDE_EFFECT_ACTIONS | {"ask_clarification", "cancelled"}
TICKET_REQUIRED = {"unit_id", "category", "priority", "title", "description", "location"}
ANNOUNCEMENT_REQUIRED = {"title", "content", "scopes"}


def compact_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_number}: each JSONL row must be an object")
        records.append(value)
    if not records:
        raise ValueError(f"{path}: dataset is empty")
    return records


def trusted_attachment_ids(record: dict[str, Any]) -> set[str]:
    context = record["input"]
    draft = context.get("workflow_draft") if isinstance(context.get("workflow_draft"), dict) else {}
    values = draft.get("attachment_ids") if isinstance(draft.get("attachment_ids"), list) else []
    return {str(value) for value in values}


def validate_semantics(record: dict[str, Any], errors: list[str]) -> None:
    case_id = str(record.get("id") or "<missing-id>")
    context = record.get("input")
    expected_raw = record.get("expected")
    if not isinstance(context, dict) or not isinstance(expected_raw, dict):
        errors.append(f"{case_id}: input and expected must be objects")
        return
    try:
        expected = AgentStructuredResult.model_validate(expected_raw).model_dump(mode="json")
    except Exception as exc:
        errors.append(f"{case_id}: expected output does not match AgentStructuredResult: {exc}")
        return

    actor_role = context.get("actor_role")
    workflow_type = context.get("workflow_type")
    action = expected.get("action") if isinstance(expected.get("action"), dict) else None
    action_type = action.get("type") if action else None
    if action_type and action_type not in KNOWN_ACTIONS:
        errors.append(f"{case_id}: unknown action type {action_type!r}")
    if actor_role == "resident" and action_type in {
        "create_announcement_draft",
        "update_announcement",
        "publish_announcement",
    }:
        errors.append(f"{case_id}: resident output contains a management side effect")
    if actor_role == "management" and action_type == "create_ticket":
        errors.append(f"{case_id}: management output contains resident create_ticket")
    if action_type in SIDE_EFFECT_ACTIONS and not action.get("requires_confirmation"):
        errors.append(f"{case_id}: side-effect action must require confirmation")
    if action_type in {"ask_clarification", "cancelled"} and action.get("requires_confirmation"):
        errors.append(f"{case_id}: non-side-effect action must not require confirmation")

    missing = expected.get("missing_fields") or []
    if missing and action_type != "ask_clarification":
        errors.append(f"{case_id}: missing fields must lead to ask_clarification")
    if action_type == "ask_clarification" and not missing:
        errors.append(f"{case_id}: ask_clarification must identify missing fields")

    draft = expected.get("draft") if isinstance(expected.get("draft"), dict) else {}
    description = str(draft.get("description") or "")
    if "tại ." in description or "in the ." in description:
        errors.append(f"{case_id}: draft contains a malformed location placeholder")
    if action_type == "create_ticket":
        absent = sorted(field for field in TICKET_REQUIRED if draft.get(field) in (None, "", []))
        if absent:
            errors.append(f"{case_id}: create_ticket draft is incomplete: {absent}")
    if action_type in {"create_announcement_draft", "update_announcement", "publish_announcement"}:
        absent = sorted(field for field in ANNOUNCEMENT_REQUIRED if draft.get(field) in (None, "", []))
        if absent:
            errors.append(f"{case_id}: announcement action draft is incomplete: {absent}")

    output_attachment_ids = {str(value) for value in draft.get("attachment_ids") or []}
    untrusted_attachment_ids = output_attachment_ids - trusted_attachment_ids(record)
    if untrusted_attachment_ids:
        errors.append(f"{case_id}: output contains untrusted attachment IDs: {sorted(untrusted_attachment_ids)}")

    action_id = str(action.get("action_id")) if action and action.get("action_id") else None
    pending = context.get("pending_action") if isinstance(context.get("pending_action"), dict) else None
    pending_id = str(pending.get("action_id")) if pending and pending.get("action_id") else None
    if action_id and action_id != pending_id:
        errors.append(f"{case_id}: action_id was not copied from trusted pending_action")

    if workflow_type == "resident_ticket" and expected["intent"] in {
        "create_announcement",
        "announcement_edit",
        "publish_announcement",
    }:
        errors.append(f"{case_id}: resident workflow uses announcement intent")
    if workflow_type == "manager_announcement" and expected["intent"] == "create_ticket":
        errors.append(f"{case_id}: manager workflow uses create_ticket intent")


def validate_openai_rows(canonical: list[dict[str, Any]], rows: list[dict[str, Any]], split: str, errors: list[str]) -> None:
    if len(rows) != len(canonical):
        errors.append(f"{split}: OpenAI row count {len(rows)} != canonical row count {len(canonical)}")
        return
    for index, (source, row) in enumerate(zip(canonical, rows, strict=True)):
        messages = row.get("messages")
        tools = row.get("tools")
        if not isinstance(messages, list) or len(messages) != 3:
            errors.append(f"{split}[{index}]: expected system/user/assistant messages")
            continue
        if [message.get("role") for message in messages] != ["system", "user", "assistant"]:
            errors.append(f"{split}[{index}]: invalid message role order")
        if not isinstance(tools, list) or len(tools) != 1:
            errors.append(f"{split}[{index}]: expected one AgentStructuredResult tool")
            continue
        tool_name = ((tools[0].get("function") or {}).get("name"))
        if tool_name != "AgentStructuredResult":
            errors.append(f"{split}[{index}]: unexpected tool name {tool_name!r}")
        calls = messages[2].get("tool_calls") or []
        if len(calls) != 1:
            errors.append(f"{split}[{index}]: expected one assistant tool call")
            continue
        function = calls[0].get("function") or {}
        if function.get("name") != "AgentStructuredResult":
            errors.append(f"{split}[{index}]: assistant called the wrong function")
        try:
            arguments = json.loads(function.get("arguments") or "")
        except json.JSONDecodeError:
            errors.append(f"{split}[{index}]: tool arguments are not valid JSON")
            continue
        if arguments != source["expected"]:
            errors.append(f"{split}[{index}]: OpenAI target differs from canonical expected output")


def validate_dataset(dataset_dir: Path) -> dict[str, Any]:
    errors: list[str] = []
    splits: dict[str, list[dict[str, Any]]] = {}
    ids: set[str] = set()
    input_owners: dict[str, list[str]] = defaultdict(list)
    message_owners: dict[str, set[str]] = defaultdict(set)

    for split in ("train", "validation", "test"):
        path = dataset_dir / "canonical" / f"{split}.jsonl"
        records = read_jsonl(path)
        splits[split] = records
        for record in records:
            case_id = str(record.get("id") or "")
            if not case_id:
                errors.append(f"{split}: record without id")
                continue
            if case_id in ids:
                errors.append(f"duplicate case id: {case_id}")
            ids.add(case_id)
            if record.get("split") != split:
                errors.append(f"{case_id}: split field does not match file")
            validate_semantics(record, errors)
            input_owners[compact_hash(record.get("input"))].append(split)
            message = str((record.get("input") or {}).get("message") or "").casefold().strip()
            message_owners[hashlib.sha256(message.encode("utf-8")).hexdigest()].add(split)

    for digest, owners in input_owners.items():
        if len(owners) > 1:
            errors.append(f"duplicate full input {digest[:12]} occurs {len(owners)} times across {sorted(set(owners))}")
    cross_split_messages = [owners for owners in message_owners.values() if len(owners) > 1]

    for split in ("train", "validation"):
        rows = read_jsonl(dataset_dir / "openai" / f"{split}.jsonl")
        validate_openai_rows(splits[split], rows, split, errors)

    test_cases = json.loads((dataset_dir / "test_cases.json").read_text(encoding="utf-8"))
    if not isinstance(test_cases, list) or len(test_cases) != len(splits["test"]):
        errors.append("test_cases.json does not match canonical test size")

    coverage: dict[str, Any] = {}
    for split, records in splits.items():
        coverage[split] = {
            "examples": len(records),
            "families": dict(sorted(Counter(record["scenario_family"] for record in records).items())),
            "languages": dict(sorted(Counter(record["language"] for record in records).items())),
            "intents": dict(sorted(Counter(record["expected"]["intent"] for record in records).items())),
            "actions": dict(
                sorted(
                    Counter(
                        (record["expected"].get("action") or {}).get("type", "none")
                        for record in records
                    ).items()
                )
            ),
        }
    return {
        "valid": not errors,
        "errors": errors,
        "coverage": coverage,
        "totals": {
            "examples": sum(len(records) for records in splits.values()),
            "unique_ids": len(ids),
            "unique_inputs": len(input_owners),
            "unique_messages": len(message_owners),
            "cross_split_repeated_messages": len(cross_split_messages),
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate the OnBxrd AI fine-tuning dataset.")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--report", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    dataset_dir = args.dataset.resolve()
    result = validate_dataset(dataset_dir)
    report_path = args.report.resolve() if args.report else dataset_dir / "validation_report.json"
    report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Dataset: {dataset_dir}")
    print(f"Examples: {result['totals']['examples']}")
    print(f"Unique inputs: {result['totals']['unique_inputs']}")
    print(f"Validation: {'PASS' if result['valid'] else 'FAIL'}")
    if result["errors"]:
        for error in result["errors"][:25]:
            print(f"- {error}")
        if len(result["errors"]) > 25:
            print(f"- ... and {len(result['errors']) - 25} more errors")
    print(f"Report: {report_path}")
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
