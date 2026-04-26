from app.engine.redaction import mask_sensitive


def test_mask_sensitive_redacts_identifiers() -> None:
    text = (
        "PAN: ABCDE1234F UAN: 100200300400 Account: 123456789012 "
        "Phone: 9876543210 Email: priya@example.com Employee: Priya Sharma Employee ID: EMP12345 "
        "Address: 42 MG Road, Pune"
    )

    masked = mask_sensitive(text)

    assert "ABCDE1234F" not in masked
    assert "100200300400" not in masked
    assert "123456789012" not in masked
    assert "9876543210" not in masked
    assert "priya@example.com" not in masked
    assert "Priya Sharma" not in masked
    assert "EMP12345" not in masked
    assert "42 MG Road" not in masked
    assert "[PAN]" in masked
    assert "[UAN]" in masked


def test_mask_sensitive_does_not_redact_unlabeled_amounts_as_phone_numbers() -> None:
    masked = mask_sensitive("Employer Contribution: 1234567890")

    assert "1234567890" in masked
