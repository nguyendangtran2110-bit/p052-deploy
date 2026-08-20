from scripts.generate_ai_finetune_dataset import BUILDERS, generate_split, write_outputs
from scripts.validate_ai_finetune_dataset import validate_dataset


def test_generated_dataset_passes_contract_and_split_validation(tmp_path):
    count = len(BUILDERS) * 2
    splits = {
        split: generate_split(split, count, 20260819 + offset)
        for offset, split in enumerate(("train", "validation", "test"))
    }

    write_outputs(tmp_path, splits, seed=20260819)
    result = validate_dataset(tmp_path)

    assert result["valid"], result["errors"]
    assert result["totals"]["examples"] == count * 3
    assert result["totals"]["unique_inputs"] == count * 3


def test_missing_location_drafts_do_not_contain_empty_placeholders():
    cases = generate_split("test", len(BUILDERS) * 2, 20260819)
    missing_location_cases = [
        case
        for case in cases
        if case.family in {"ticket_missing_location", "ticket_followup_location"}
    ]

    assert missing_location_cases
    for case in missing_location_cases:
        description = str(case.expected["draft"].get("description") or "")
        assert "tại ." not in description
        assert "in the ." not in description
