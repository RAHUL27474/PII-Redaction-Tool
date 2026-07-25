import logging
import re
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

EMAIL_PATTERN = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
)

PHONE_PATTERN_US = re.compile(
    r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
)

SSN_PATTERN = re.compile(
    r"\b\d{3}-\d{2}-\d{4}\b"
)

DOB_PATTERN = re.compile(
    r"\b(?:0?[1-9]|1[0-2])[-/](?:0?[1-9]|[12]\d|3[01])[-/](?:19|20)\d{2}\b"
)

IPV4_PATTERN = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"
)

CREDIT_CARD_PATTERN = re.compile(
    r"\b(?:\d{4}[\s\-]?){3}\d{4}\b"
)

COMPANY_SUFFIX_PATTERN = re.compile(
    r"\b(?:Inc\.?|Corp\.?|Corporation|LLC|Ltd\.?|Co\.?|LP|LLP|PLC|GmbH|AG|SA|BV|N\.V\.|S\.A\.|Pte\.?[ ]?Ltd\.?)\b",
    re.IGNORECASE,
)

STREET_SUFFIX_PATTERN = re.compile(
    r"\b\d+\s+(?:Avenue|Boulevard|Drive|Street|Lane|Road|Court|Place|Square|Terrace|Way|Circle|Parkway|Highway|Alley)\b",
    re.IGNORECASE,
)

FULL_NAME_PATTERN = re.compile(
    r"(?<!\w)([A-Z][a-z]+(?:\s+[A-Z][a-z']+)+)(?!\w)"
)


def is_valid_credit_card(number: str) -> bool:
    digits = re.sub(r"[\s\-]", "", number)
    if not digits.isdigit():
        return False
    if len(digits) < 13 or len(digits) > 19:
        return False
    return _luhn_check(digits)


def _luhn_check(digits: str) -> bool:
    def digits_of(n: str) -> List[int]:
        return [int(d) for d in n]
    d = digits_of(digits)
    odd_digits = d[-1::-2]
    even_digits = d[-2::-2]
    total = sum(odd_digits)
    for d in even_digits:
        total += sum(digits_of(str(d * 2)))
    return total % 10 == 0


def detect_emails(text: str) -> List[str]:
    return list(set(EMAIL_PATTERN.findall(text)))


def detect_phones(text: str) -> List[str]:
    us = PHONE_PATTERN_US.findall(text)
    return list(set(us))


def detect_ssns(text: str) -> List[str]:
    return list(set(SSN_PATTERN.findall(text)))


def detect_dobs(text: str) -> List[str]:
    return list(set(DOB_PATTERN.findall(text)))


def detect_ips(text: str) -> List[str]:
    return [ip for ip in IPV4_PATTERN.findall(text)]


def detect_credit_cards(text: str) -> List[str]:
    candidates = CREDIT_CARD_PATTERN.findall(text)
    return list(set(c for c in candidates if is_valid_credit_card(c)))


def detect_company_names(text: str) -> List[str]:
    return list(set(COMPANY_SUFFIX_PATTERN.findall(text)))


def detect_addresses(text: str) -> List[str]:
    return list(set(STREET_SUFFIX_PATTERN.findall(text)))


def detect_full_names(text: str) -> List[str]:
    matches = FULL_NAME_PATTERN.findall(text)
    return list(set(matches))


def detect_all(text: str) -> Dict[str, List[str]]:
    results: Dict[str, List[str]] = {
        "email": detect_emails(text),
        "phone": detect_phones(text),
        "ssn": detect_ssns(text),
        "dob": detect_dobs(text),
        "ipv4": detect_ips(text),
        "credit_card": detect_credit_cards(text),
        "company": detect_company_names(text),
        "address": detect_addresses(text),
        "full_name": detect_full_names(text),
    }
    logger.info("Detection results: %s", {k: len(v) for k, v in results.items()})
    return results


def detect_all_in_segments(segments: List[str]) -> Dict[str, List[str]]:
    combined: Dict[str, List[str]] = {
        "email": [], "phone": [], "ssn": [], "dob": [],
        "ipv4": [], "credit_card": [], "company": [],
        "address": [], "full_name": [],
    }
    for segment in segments:
        segment_results = detect_all(segment)
        for key in combined:
            combined[key].extend(segment_results.get(key, []))
    for key in combined:
        combined[key] = list(set(combined[key]))
    return combined