import re
import base64
from app.models import SandboxedFacts

SUSPICIOUS_PATTERNS = [
    r"ignore previous instructions",
    r"delete all",
    r"drop table",
    r"send password",
    r"reveal secret",
    r"transfer funds",
    r"reset admin",
    r"sudo",
    r"rm -rf",
    r"bypass security",
    r"override policy"
]

DANGEROUS_WORDS = [
    "delete",
    "drop",
    "send",
    "sudo",
    "override",
    "password",
    "secret"
]


def normalize_text(text: str) -> str:
    text = text.lower()

    text = re.sub(
        r'\b(?:[a-zA-Z]\s+){2,}[a-zA-Z]\b',
        lambda m: m.group(0).replace(" ", ""),
        text
    )

    return text


def try_decode_base64(text: str) -> str:
    try:
        padding = len(text) % 4
        if padding != 0:
            text = text + ("=" * (4 - padding))

        decoded = base64.b64decode(text, validate=True).decode("utf-8")
        return decoded.lower()
    except Exception:
        return ""


def extract_decoded_suspicious(content: str) -> list[str]:
    hits = []

    for word in content.split():
        decoded = try_decode_base64(word)
        if not decoded:
            continue

        normalized_decoded = normalize_text(decoded)

        for pattern in SUSPICIOUS_PATTERNS:
            if re.search(pattern, normalized_decoded):
                hits.append(f"{pattern} (decoded)")

    return hits


def is_suspicious(text: str) -> bool:
    normalized = normalize_text(text)

    for pattern in SUSPICIOUS_PATTERNS:
        if re.search(pattern, normalized):
            return True

    decoded_hits = extract_decoded_suspicious(text)
    if decoded_hits:
        return True

    return False


def looks_like_fact(line: str) -> bool:
    lowered = line.lower()

    if len(line.strip()) < 4:
        return False

    if len(line) > 300:
        return False

    if is_suspicious(line):
        return False

    business_keywords = [
        "customer",
        "issue",
        "problem",
        "fails",
        "failed",
        "error",
        "login",
        "payment",
        "account",
        "application",
        "android",
        "ios",
        "cannot",
        "crash",
        "ticket",
        "checkout",
        "upload",
        "verification",
        "email"
    ]

    if any(word in lowered for word in business_keywords):
        return True

    if any(word in lowered for word in DANGEROUS_WORDS):
        return False

    return True


def sandbox_parse(content: str) -> SandboxedFacts:
    normalized = normalize_text(content)
    suspicious_hits = []

    for pattern in SUSPICIOUS_PATTERNS:
        if re.search(pattern, normalized):
            suspicious_hits.append(pattern)

    suspicious_hits.extend(extract_decoded_suspicious(content))

    facts = []
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        parts = re.split(r'[.!?]\s+', line)
        for part in parts:
            part = part.strip()
            if not part:
                continue
            if looks_like_fact(part):
                facts.append(part)

    unique_facts = []
    seen_facts = set()
    for fact in facts:
        key = fact.lower()
        if key not in seen_facts:
            seen_facts.add(key)
            unique_facts.append(fact)

    unique_suspicious = []
    seen_suspicious = set()
    for item in suspicious_hits:
        if item not in seen_suspicious:
            seen_suspicious.add(item)
            unique_suspicious.append(item)

    summary = " | ".join(unique_facts[:5]) if unique_facts else "No safe facts extracted."

    return SandboxedFacts(
        extracted_facts=unique_facts[:10],
        suspicious_patterns=unique_suspicious,
        raw_summary=summary
    )
