from __future__ import annotations

import re

PATTERNS = (
    (re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b"), "[PAN]"),
    (re.compile(r"(?i)(uan:\s*)\d+"), r"\1[UAN]"),
    (re.compile(r"(?i)(account:\s*)\d+"), r"\1[ACCOUNT]"),
    (re.compile(r"(?i)(phone:\s*)\d{10}"), r"\1[PHONE]"),
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "[EMAIL]"),
    (re.compile(r"(?i)(employee:\s*)[A-Za-z][A-Za-z ]+?(?=\s+Employee ID:|$)"), r"\1[NAME]"),
    (re.compile(r"(?i)(member:\s*)[A-Za-z][A-Za-z ]+?(?=\s+UAN:|$)"), r"\1[NAME]"),
    (re.compile(r"(?i)(employee\s+id:\s*)[A-Z0-9-]+"), r"\1[EMPLOYEE_ID]"),
    (re.compile(r"(?i)(address:\s*)[^;\n]+"), r"\1[ADDRESS]"),
    (re.compile(r"\b\d{12}\b"), "[UAN]"),
    (re.compile(r"\b[6-9]\d{9}\b"), "[PHONE]"),
)


def mask_sensitive(text: str) -> str:
    masked = text
    for pattern, replacement in PATTERNS:
        masked = pattern.sub(replacement, masked)
    return masked
