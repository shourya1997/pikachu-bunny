from app.contracts import AuditState, Result, ResultCode, contract_metadata


def test_contract_metadata_exposes_state_vocabularies() -> None:
    metadata = contract_metadata()

    assert "confirmed_mismatch" in metadata["audit_states"]
    assert "needs_review" in metadata["audit_states"]
    assert "cancelled" in metadata["job_states"]
    assert "ocr_only_unsupported" in metadata["result_codes"]


def test_result_failure_is_typed() -> None:
    result = Result.failure(ResultCode.UNSUPPORTED_LAYOUT, "Unsupported salary slip")

    assert result.ok is False
    assert result.code == ResultCode.UNSUPPORTED_LAYOUT


def test_audit_state_contains_partial_not_false_mismatch() -> None:
    assert AuditState.PARTIAL.value == "partial"
