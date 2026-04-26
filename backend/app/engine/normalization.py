from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

MONTHS = {
    "january": "01",
    "february": "02",
    "march": "03",
    "april": "04",
    "may": "05",
    "june": "06",
    "july": "07",
    "august": "08",
    "september": "09",
    "october": "10",
    "november": "11",
    "december": "12",
}

LEGAL_SUFFIXES = (
    "private",
    "pvt",
    "limited",
    "ltd",
    "llp",
    "inc",
    "company",
    "co",
)


def normalize_period(value: str) -> str:
    text = value.strip().lower()
    if re.fullmatch(r"\d{4}-\d{2}", text):
        year, month = text.split("-")
        if int(year) < 2000 or not 1 <= int(month) <= 12:
            raise ValueError(f"Unsupported period: {value}")
        return text

    match = re.fullmatch(r"([a-zA-Z]+)\s+(\d{4})", text)
    if match and match.group(1) in MONTHS and int(match.group(2)) >= 2000:
        return f"{match.group(2)}-{MONTHS[match.group(1)]}"

    raise ValueError(f"Unsupported period: {value}")


def normalize_amount(value: str) -> Decimal:
    match = re.search(r"\d[\d,]*(?:\.\d+)?", value)
    if not match:
        raise ValueError(f"Unsupported amount: {value}")
    cleaned = match.group(0).replace(",", "")
    try:
        return Decimal(cleaned).quantize(Decimal("0.01"))
    except InvalidOperation as exc:
        raise ValueError(f"Unsupported amount: {value}") from exc


def normalize_employer(value: str) -> str:
    words = re.sub(r"[^a-zA-Z0-9 ]", " ", value).lower().split()
    return " ".join(word for word in words if word not in LEGAL_SUFFIXES)
