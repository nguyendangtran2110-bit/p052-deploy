"""Deterministic safety controls at the chatbot trust boundary.

LLM prompts are a useful instruction layer, but they are not an authorization or
content-safety boundary.  This module contains provider-independent checks used
before text is sent to a model and before model text is returned to a client.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

from src.backend.domain.common.errors import ValidationError

_SECRET_PATTERNS = (
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._~+/=-]+"),
    re.compile(r"(?i)(?:access|refresh|api|secret)_?token\s*[=:]\s*[^\s,;]+"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
    re.compile(r"\b(?:sk|gsk)[-_][A-Za-z0-9_-]{16,}\b"),
    re.compile(r"\bAKIA[A-Z0-9]{16}\b"),
)
_URL_PATTERN = re.compile(r"https?://[^\s]+", re.IGNORECASE)
_EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
_VI_PHONE_PATTERN = re.compile(r"(?<!\d)(?:\+?84|0)(?:[ .-]?\d){9}(?!\d)")
_IDENTITY_PATTERN = re.compile(
    r"(?i)\b(?:cccd|cmnd|căn\s*cước|can\s*cuoc)\s*[:=#-]?\s*\d{9,12}\b"
)

_PROMPT_INJECTION_PATTERNS = (
    re.compile(r"(?i)\bignore\s+(?:all\s+)?(?:previous|prior|above|system|developer)\s+instructions?\b"),
    re.compile(r"(?i)\b(?:reveal|show|print|repeat|leak)\s+(?:the\s+)?(?:system|developer)\s+prompt\b"),
    re.compile(r"(?i)\b(?:act|pretend)\s+as\s+(?:the\s+)?(?:system|developer|administrator)\b"),
    re.compile(r"(?i)\b(?:jailbreak|developer\s+mode)\b"),
    re.compile(r"\bDAN\b"),
    re.compile(r"(?i)<\/?(?:system|developer|assistant)>"),
    re.compile(r"(?i)\b(?:bỏ\s+qua|phớt\s+lờ)\s+(?:mọi\s+)?(?:chỉ\s+dẫn|hướng\s+dẫn|quy\s+tắc)\s+(?:trước|ở\s+trên)\b"),
    re.compile(r"(?i)\b(?:tiết\s+lộ|in|hiển\s+thị)\s+(?:system\s+prompt|prompt\s+hệ\s+thống)\b"),
)

_HARMFUL_REQUEST_PATTERNS = (
    re.compile(r"(?i)\b(?:how\s+to|instructions?\s+(?:to|for)|cách|hướng\s+dẫn)\b.{0,50}\b(?:make|build|chế\s+tạo|làm)\b.{0,30}\b(?:bomb|explosive|bom|chất\s+nổ)\b"),
    re.compile(r"(?i)\b(?:how\s+to|cách|hướng\s+dẫn)\b.{0,60}\b(?:kill|poison|harm|giết|đầu\s+độc|làm\s+hại)\b"),
)
_RESOURCE_EXHAUSTION_PATTERNS = (
    re.compile(r"(?i)\b(?:repeat|lặp\s+lại)\b.{0,40}\b\d{4,}\b"),
    re.compile(r"(?i)\b(?:generate|tạo|viết)\b.{0,40}\b\d{3,}\b.{0,40}\b(?:variants?|biến\s+thể|câu\s+trả\s+lời|messages?)\b"),
    re.compile(r"(?i)\b(?:generate|create|tạo|viết)\b.{0,40}\b\d{3,}\b.{0,40}\b(?:tickets?|ticket|phiếu|phieu)\b"),
    re.compile(r"(?i)\b(?:vòng\s+lặp|loop)\b.{0,40}\b(?:gửi|send)\b.{0,40}\b\d{3,}\b.{0,40}\b(?:yêu\s+cầu|requests?)\b"),
    re.compile(r"(?i)\b(?:gửi|send)\b.{0,40}\b\d{3,}\b.{0,40}\b(?:yêu\s+cầu|requests?)\b.{0,40}\b(?:trong|within|per)\b"),
)
_UNVERIFIED_OR_DANGEROUS_POLICY_INPUT_PATTERNS = (
    re.compile(
        r"(?i)\b(?:thong bao khan cap|canh bao khan cap|viet thong bao khan cap)\b"
        r".{0,120}\b(?:ca nhiem|benh truyen nhiem|dich benh|so tan)\b"
    ),
    re.compile(
        r"(?i)\b(?:facebook|group|nghe bao|co nguoi noi|nhan rieng|khong can kiem tra|khong can kiem chung)\b"
        r".{0,140}\b(?:phi.{0,60}(?:giam|mien|tang|doi)|(?:giam|mien|tang|doi).{0,60}phi|khong can dong phi)\b"
    ),
    re.compile(
        r"(?i)\b(?:phi.{0,60}(?:giam|mien|tang|doi)|(?:giam|mien|tang|doi).{0,60}phi|khong can dong phi)\b"
        r".{0,140}\b(?:facebook|group|nghe bao|co nguoi noi|nhan rieng|khong can kiem tra|khong can kiem chung)\b"
    ),
    re.compile(r"(?i)\b(?:khoa|chan|niem phong)\b.{0,40}\b(?:cua thoat hiem|loi thoat hiem)\b"),
)
_UNSAFE_POLICY_OUTPUT_PATTERNS = (
    re.compile(
        r"(?i)\b(?:toi se|chung toi se)\b.{0,80}\b(?:soan|thong bao|xac nhan)\b"
        r".{0,140}\b(?:ca nhiem|benh truyen nhiem|dich benh|so tan)\b"
    ),
    re.compile(
        r"(?i)\b(?:toi se|chung toi se)\b.{0,80}\b(?:soan|thong bao|xac nhan)\b"
        r".{0,140}\b(?:phi.{0,60}(?:giam|mien|tang|doi)|(?:giam|mien|tang|doi).{0,60}phi|khong can dong phi)\b"
    ),
    re.compile(r"(?i)\b(?:cu dan|mọi người|resident)\b.{0,60}\b(?:duoc|được)\b.{0,40}\b(?:khoa|khóa)\b.{0,40}\b(?:cua thoat hiem|cửa thoát hiểm)\b"),
)

_OUTPUT_LEAK_PATTERNS = (
    re.compile(r"(?i)return only the structured schema"),
    re.compile(r"(?i)you are the onbxrd resident/management assistant"),
    re.compile(r"(?i)CÂU HỎI CỦA CƯ DÂN:\s*"),
    re.compile(r"(?i)THÔNG TIN TỪ SỔ TAY CƯ DÂN:\s*"),
)

SAFE_REFUSAL = "Tôi không thể hỗ trợ yêu cầu đó. Tôi có thể giúp về thông tin cư dân hoặc quy trình của tòa nhà."
SAFE_OUTPUT_FALLBACK = (
    "Tôi chưa thể cung cấp câu trả lời an toàn và đáng tin cậy cho yêu cầu này. "
    "Vui lòng liên hệ Ban Quản Lý để được hỗ trợ."
)
UNVERIFIED_POLICY_REFUSAL = (
    "Không thể tạo thông báo từ tuyên bố chính sách chưa được xác minh. "
    "Vui lòng cung cấp hoặc cập nhật văn bản chính thức của Ban Quản Lý trong kho tri thức trước."
)

_ANNOUNCEMENT_PATTERN = re.compile(
    r"\b(?:thong bao|soan (?:tin nhan|thong bao)|viet huong dan|announcement|gui (?:hang xom|cu dan)|send (?:a )?notice)\b"
)
_POLICY_AUTHORITY_PATTERN = re.compile(
    r"\b(?:quy dinh moi|theo quy dinh|ban cap nhat|so tay.{0,20}cap nhat|"
    r"bo quy dinh|huy quy dinh|ban quan ly.{0,30}(?:cho phep|cam|bo|huy)|"
    r"ban quan ly.{0,50}(?:giam|mien|tang|doi).{0,20}phi|"
    r"(?:giam|mien|tang|doi).{0,20}phi|"
    r"phi.{0,50}(?:giam|mien|tang|doi)|"
    r"policy.{0,20}(?:updated|new|allows?|prohibits?|removed|waived))\b"
)
_FEE_CHANGE_PATTERN = re.compile(r"\b(?:phi.{0,50}(?:giam|mien|tang|doi)|(?:giam|mien|tang|doi).{0,50}phi)\b")
_FEE_WAIVER_PATTERN = re.compile(r"\b(?:mien.{0,50}phi|phi.{0,50}mien|khong can dong phi|waived?)\b")
_FEE_REDUCTION_PATTERN = re.compile(r"\b(?:giam.{0,50}phi|phi.{0,50}giam|reduced?|discount)\b")
_SENSITIVE_ANNOUNCEMENT_PATTERN = re.compile(
    r"\b(?:thong bao khan cap|canh bao khan cap|emergency notice|urgent notice)\b"
)
_SENSITIVE_PUBLIC_HEALTH_OR_SAFETY_PATTERN = re.compile(
    r"\b(?:ca nhiem|benh truyen nhiem|dich benh|so tan|toa nha sap|chay no|ro ri khi gas|"
    r"infectious disease|outbreak|evacuate|evacuation|building collapse|fire|gas leak)\b"
)
_DANGEROUS_PET_PATTERN = re.compile(r"\b(?:pitbull|cho nguy hiem|dangerous dogs?)\b")
_LOOSE_PET_PATTERN = re.compile(r"\b(?:tha rong|khong day dat|off leash|roam freely)\b")
_ALLOW_PATTERN = re.compile(r"\b(?:cho phep|duoc phep|duoc|chap nhan|allows?|permitted|accepted)\b")
_DENY_PATTERN = re.compile(r"\b(?:khong duoc phep|cam|not allowed|prohibited|forbidden)\b")
_REVOKE_PATTERN = re.compile(r"\b(?:bo quy dinh|huy quy dinh|khong con yeu cau|removed|waived|no longer required)\b")
_DANGEROUS_POLICY_ACTIVITY_PATTERN = re.compile(
    r"\b(?:dot than|dot lua|bep than|than trong hanh lang|khoa cua thoat hiem|cua thoat hiem|"
    r"de xe may trong sanh|xe may trong sanh|open flame|charcoal|"
    r"gas cylinder|binh gas|hoa chat doc hai|hazardous chemical)\b"
)
_POLICY_SUPPORT_STOPWORDS = {
    "theo",
    "quy",
    "dinh",
    "moi",
    "nhat",
    "thong",
    "bao",
    "rang",
    "rằng",
    "quan",
    "vua",
    "hay",
    "hãy",
    "viet",
    "viết",
    "chinh",
    "thuc",
    "chính",
    "thức",
    "cu",
    "dan",
    "cư",
    "dân",
    "cho",
    "phep",
    "duoc",
    "được",
    "ban",
    "ban quan ly",
}


@dataclass(frozen=True)
class InputSafetyResult:
    safe_text: str
    redactions: int = 0


def _fold(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", str(value).casefold().replace("đ", "d"))
    return re.sub(r"\s+", " ", "".join(char for char in normalized if not unicodedata.combining(char)))


def _verified_policy_sources(handbook_results: Any) -> list[tuple[str, dict[str, Any]]]:
    sources: list[tuple[str, dict[str, Any]]] = []
    for item in handbook_results or []:
        if not isinstance(item, dict):
            continue
        citation = item.get("citation")
        if not isinstance(citation, dict) or citation.get("verified_policy_source") is not True:
            continue
        sources.append((_fold(item.get("content") or item.get("text") or ""), citation))
    return sources


def _policy_terms(folded: str) -> set[str]:
    return {
        token
        for token in re.findall(r"\b[a-z0-9]{4,}\b", folded)
        if token not in _POLICY_SUPPORT_STOPWORDS
    }


def _supports_policy_claim(folded_claim: str, folded_source: str) -> bool:
    terms = _policy_terms(folded_claim)
    overlap = terms.intersection(_policy_terms(folded_source))
    required_overlap = 1 if len(terms) <= 2 else 2
    if len(overlap) < required_overlap:
        return False
    if _FEE_CHANGE_PATTERN.search(folded_claim):
        if not _FEE_CHANGE_PATTERN.search(folded_source):
            return False
        if _FEE_WAIVER_PATTERN.search(folded_claim) and not _FEE_WAIVER_PATTERN.search(folded_source):
            return False
        if _FEE_REDUCTION_PATTERN.search(folded_claim) and not _FEE_REDUCTION_PATTERN.search(folded_source):
            return False
    if _ALLOW_PATTERN.search(folded_claim) and (
        not _ALLOW_PATTERN.search(folded_source) or _DENY_PATTERN.search(folded_source)
    ):
        return False
    if _DENY_PATTERN.search(folded_claim) and not _DENY_PATTERN.search(folded_source):
        return False
    if _REVOKE_PATTERN.search(folded_claim) and not _REVOKE_PATTERN.search(folded_source):
        return False
    return True


def _supports_dangerous_policy_permission(folded_source: str) -> bool:
    for match in _DANGEROUS_POLICY_ACTIVITY_PATTERN.finditer(folded_source):
        start = max(match.start() - 60, 0)
        end = min(match.end() + 60, len(folded_source))
        window = folded_source[start:end]
        if _ALLOW_PATTERN.search(window) and not _DENY_PATTERN.search(window):
            return True
    return False


def enforce_grounded_policy_announcement(message: str, handbook_results: Any) -> None:
    """Block official-looking policy notices unless trusted indexed text supports them."""
    folded = _fold(message)
    dangerous_pet_claim = (
        _DANGEROUS_PET_PATTERN.search(folded)
        and _LOOSE_PET_PATTERN.search(folded)
        and _ALLOW_PATTERN.search(folded)
    )
    announcement_request = _ANNOUNCEMENT_PATTERN.search(folded)
    dangerous_policy_activity = _DANGEROUS_POLICY_ACTIVITY_PATTERN.search(folded)
    policy_notice = announcement_request and (
        _POLICY_AUTHORITY_PATTERN.search(folded) or dangerous_policy_activity
    )
    sensitive_notice = _SENSITIVE_ANNOUNCEMENT_PATTERN.search(
        folded
    ) and _SENSITIVE_PUBLIC_HEALTH_OR_SAFETY_PATTERN.search(folded)
    if not dangerous_pet_claim and not policy_notice and not sensitive_notice:
        return

    sources = _verified_policy_sources(handbook_results)
    if not sources:
        raise ValidationError(UNVERIFIED_POLICY_REFUSAL)

    if sensitive_notice:
        incident_sources = [
            (content, citation)
            for content, citation in sources
            if citation.get("verified_incident_source") is True
            or citation.get("verified_emergency_source") is True
        ]
        if not incident_sources:
            raise ValidationError(UNVERIFIED_POLICY_REFUSAL)
        sources = incident_sources

    if re.search(r"\b(?:hom qua|yesterday)\b", folded):
        expected_date = (date.today() - timedelta(days=1)).isoformat()
        sources = [source for source in sources if source[1].get("effective_date") == expected_date]
        if not sources:
            raise ValidationError(UNVERIFIED_POLICY_REFUSAL)

    if dangerous_pet_claim:
        supported = any(
            _DANGEROUS_PET_PATTERN.search(content)
            and _LOOSE_PET_PATTERN.search(content)
            and _ALLOW_PATTERN.search(content)
            and not _DENY_PATTERN.search(content)
            for content, _citation in sources
        )
        if not supported:
            raise ValidationError(UNVERIFIED_POLICY_REFUSAL)

    dangerous_policy_claim = policy_notice and dangerous_policy_activity and _ALLOW_PATTERN.search(folded)
    if dangerous_policy_claim:
        supported = any(
            _supports_dangerous_policy_permission(content)
            for content, _citation in sources
        )
        if not supported:
            raise ValidationError(UNVERIFIED_POLICY_REFUSAL)

    if policy_notice:
        supported = any(_supports_policy_claim(folded, content) for content, _citation in sources)
        if not supported:
            raise ValidationError(UNVERIFIED_POLICY_REFUSAL)

    if sensitive_notice:
        supported = any(
            _SENSITIVE_PUBLIC_HEALTH_OR_SAFETY_PATTERN.search(content)
            and _supports_policy_claim(folded, content)
            for content, _citation in sources
        )
        if not supported:
            raise ValidationError(UNVERIFIED_POLICY_REFUSAL)


def _replace(pattern: re.Pattern[str], text: str, replacement: str) -> tuple[str, int]:
    return pattern.subn(replacement, text)


def redact_secrets(text: str) -> tuple[str, int]:
    """Remove credentials and signed URLs without treating ordinary links as safe."""
    redacted = str(text)
    count = 0
    for pattern in _SECRET_PATTERNS:
        redacted, matches = _replace(pattern, redacted, "[redacted-secret]")
        count += matches
    redacted, matches = _replace(_URL_PATTERN, redacted, "[redacted-url]")
    return redacted, count + matches


def sanitize_user_text(text: str) -> InputSafetyResult:
    """Validate intent-like attacks and minimize personal data sent to providers."""
    value = str(text).strip()
    if any(pattern.search(value) for pattern in _PROMPT_INJECTION_PATTERNS):
        raise ValidationError(SAFE_REFUSAL)
    if any(pattern.search(value) for pattern in _HARMFUL_REQUEST_PATTERNS):
        raise ValidationError(SAFE_REFUSAL)
    if any(pattern.search(value) for pattern in _RESOURCE_EXHAUSTION_PATTERNS):
        raise ValidationError(SAFE_REFUSAL)
    if any(pattern.search(_fold(value)) for pattern in _UNVERIFIED_OR_DANGEROUS_POLICY_INPUT_PATTERNS):
        raise ValidationError(UNVERIFIED_POLICY_REFUSAL)

    value, count = redact_secrets(value)
    for pattern, replacement in (
        (_EMAIL_PATTERN, "[redacted-email]"),
        (_VI_PHONE_PATTERN, "[redacted-phone]"),
        (_IDENTITY_PATTERN, "[redacted-identity]"),
    ):
        value, matches = _replace(pattern, value, replacement)
        count += matches
    return InputSafetyResult(safe_text=value, redactions=count)


def sanitize_model_output(text: str, *, max_chars: int = 8000) -> str:
    """Fail closed on prompt leakage/unsafe instructions and strip credentials."""
    value = str(text).strip()
    if not value:
        return SAFE_OUTPUT_FALLBACK
    if any(pattern.search(_fold(value)) for pattern in _UNSAFE_POLICY_OUTPUT_PATTERNS):
        return UNVERIFIED_POLICY_REFUSAL
    if any(pattern.search(value) for pattern in (*_OUTPUT_LEAK_PATTERNS, *_HARMFUL_REQUEST_PATTERNS)):
        return SAFE_OUTPUT_FALLBACK
    value, _ = redact_secrets(value)
    if len(value) > max_chars:
        value = value[: max_chars - 1].rstrip() + "…"
    return value
