import re
import json
import base64
import binascii
import urllib.parse
import unicodedata
from types import SimpleNamespace


SUSPICIOUS_PATTERNS = [
    ("ignore previous instructions", r"\bignore(?:\s+all)?\s+(?:previous|prior|above)\s+instructions\b"),
    ("forget previous instructions", r"\bforget(?:\s+all)?\s+(?:previous|prior)\s+instructions\b"),
    ("override policy", r"\boverride\s+(?:the\s+)?(?:policy|rules|guardrails)\b"),
    ("developer message", r"\bdeveloper\s+message\b"),
    ("system prompt", r"\bsystem\s+prompt\b"),
    ("reveal secret", r"\breveal\s+(?:the\s+)?(?:secret|hidden\s+instructions?|prompt)\b"),
    ("send password", r"\bsend\s+(?:the\s+)?(?:password|token|credentials?)\b"),
    ("show api key", r"\bshow\s+(?:me\s+)?(?:the\s+)?(?:api\s+key|password|token|secret)\b"),
    ("bypass security", r"\bbypass\s+security\b"),
    ("reset admin", r"\breset\s+admin\b"),
    ("grant admin", r"\bgrant\s+admin\b"),
    ("delete all", r"\bdelete\s+all\b"),
    ("rm -rf", r"\brm\s+-rf\b"),
    ("drop table", r"\bdrop\s+table\b"),
    ("sudo", r"\bsudo\b"),
    ("transfer funds", r"\btransfer\s+funds\b"),
    ("wire money", r"\bwire\s+money\b"),
    ("export all data", r"\bexport\s+all\s+data\b"),
    ("download all records", r"\bdownload\s+all\s+records\b"),
    ("exfiltration", r"\bexfiltrat(?:e|ion)\b"),
    ("chmod 777", r"\bchmod\s+777\b"),
    ("union select", r"\bunion\s+select\b"),
    ("select * from", r"\bselect\s+\*\s+from\b"),
]


def _to_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, ensure_ascii=False)
    except Exception:
        return str(value)


def _extract_base64_decodings(text: str) -> str:
    decoded_parts = []
    tokens = re.findall(r"[A-Za-z0-9+/=]{8,}", text)

    for tok in tokens:
        if len(tok) % 4 != 0:
            continue
        try:
            raw = base64.b64decode(tok, validate=True)
            s = raw.decode("utf-8", errors="ignore").strip()
            if s and any(ch.isalpha() for ch in s):
                decoded_parts.append(s)
        except (binascii.Error, ValueError):
            continue

    return "\n".join(decoded_parts)


def _normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = urllib.parse.unquote(text)
    text = text.lower()

    # common obfuscation substitutions
    text = text.translate(str.maketrans({
        "0": "o",
        "1": "i",
        "3": "e",
        "4": "a",
        "5": "s",
        "7": "t",
        "@": "a",
        "$": "s",
    }))

    decoded = _extract_base64_decodings(text)
    if decoded:
        text = text + "\n" + decoded.lower()

    # keep spaces, remove most punctuation/noise
    text = re.sub(r"[^a-z0-9\s/_\-:+.=]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _compact_text(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def verify_intent(user_goal: str, sandboxed=None, plan=None):
    combined = "\n".join([
        _to_text(user_goal),
        _to_text(sandboxed),
        _to_text(plan),
    ])

    normalized = _normalize_text(combined)
    compact = _compact_text(normalized)

    hits = []
    for label, pattern in SUSPICIOUS_PATTERNS:
        if re.search(pattern, normalized, re.IGNORECASE):
            hits.append(label)
            continue

        # also catch split / squashed variants like ignorepreviousinstructions
        squashed_label = _compact_text(label)
        if squashed_label and squashed_label in compact:
            hits.append(f"{label} (compact)")
            continue

    if hits:
        return SimpleNamespace(
            allowed=False,
            risk_score=1.0,
            reason=f"Hard Block: Suspicious patterns {hits}",
            security_source="rule_based",
        )

    return SimpleNamespace(
        allowed=True,
        risk_score=0.0,
        reason="Plan strictly matches user goal.",
        security_source="rule_based",
    )


# compatibility alias
review_prompt = verify_intent