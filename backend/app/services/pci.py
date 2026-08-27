import hashlib
import re
from typing import Any

_SENSITIVE_FIELDS = frozenset({
    "card_number", "pan", "card_pan", "credit_card_number",
    "debit_card_number", "cc_number", "ccn",
})


def _luhn_check(card_number: str) -> bool:
    digits = [int(d) for d in card_number if d.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False
    checksum = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0


def validate_card_format(card_number: str) -> bool:
    clean = re.sub(r"[\s\-]", "", card_number)
    if not clean.isdigit():
        return False
    return _luhn_check(clean)


def mask_card_number(card_number: str) -> str:
    clean = re.sub(r"[\s\-]", "", card_number)
    if len(clean) < 4:
        return "****"
    last_four = clean[-4:]
    groups = []
    for i in range(0, len(clean) - 4, 4):
        groups.append("****")
    groups.append(last_four)
    return "-".join(groups)


def hash_card(card_number: str) -> str:
    clean = re.sub(r"[\s\-]", "", card_number)
    return hashlib.sha256(clean.encode("utf-8")).hexdigest()


def mask_sensitive_fields(data: dict[str, Any]) -> dict[str, Any]:
    masked = {}
    for key, value in data.items():
        if isinstance(value, str) and key.lower() in _SENSITIVE_FIELDS:
            if validate_card_format(value):
                masked[key] = mask_card_number(value)
            else:
                masked[key] = value
        elif isinstance(value, dict):
            masked[key] = mask_sensitive_fields(value)
        else:
            masked[key] = value
    return masked
