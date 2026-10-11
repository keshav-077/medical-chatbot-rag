"""Agent-step safety checks for bloom.

Amazon Bedrock Guardrails ``InvokeGuardrailChecks`` is detect-only: each
call returns severity or confidence scores, and this module decides whether
to block, redact, or allow. It does not create a guardrail resource.

Checks by step:
- user input: prompt attack, content filters, sensitive information
- retrieved context and tool output: prompt attack and sensitive information
- model output: content filters and sensitive information

Content filters are not applied to library or tool text. Medical sources
describe illness and injury, and a content hit there would drop legitimate
answers. Violence and insults on user input are logged only, so injury and
distress descriptions still reach the emergency screen and the model.

When Bedrock is not configured, or the API call fails, local patterns still
catch obvious prompt attacks and redact identifiers. Local mode does not
score hate, violence, sexual content, insults, or misconduct.
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
import threading
from collections import OrderedDict
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

PROMPT_BLOCK_SCORE = 0.6
CONTENT_BLOCK_SCORE = 0.8
PII_REDACT_SCORE = 0.6

_INPUT_CONTENT_BLOCK = frozenset({"HATE", "SEXUAL", "MISCONDUCT"})
_OUTPUT_CONTENT_BLOCK = frozenset({"HATE", "SEXUAL", "MISCONDUCT", "VIOLENCE", "INSULTS"})

_CHUNK = 8000
_OVERLAP = 200

USER_BLOCKED_REPLY = (
    "I can't help with that request. I can still explain medicines, symptoms, "
    "labs, and nearby care in general terms. If this is an emergency, call 112 or 108."
)
CONTEXT_BLOCKED_REPLY = (
    "I stopped this reply because a retrieved note or uploaded document looked "
    "like an attempt to override my instructions. Try a shorter question, or "
    "upload a report that contains only the lab values. If this is an emergency, "
    "call 112 or 108."
)
OUTPUT_BLOCKED_REPLY = (
    "I withheld that reply because it did not pass the safety check. I can still "
    "explain general health topics. If this is an emergency, call 112 or 108."
)
PII_INCOMPLETE_REPLY = (
    "I could not finish the privacy check on that text, so I did not send it on. "
    "Remove card numbers, id numbers, and passwords, then try again."
)

_CONTENT_CATEGORIES = ("HATE", "INSULTS", "SEXUAL", "VIOLENCE", "MISCONDUCT")
_ATTACK_CATEGORIES = ("JAILBREAK", "PROMPT_INJECTION", "PROMPT_LEAKAGE")
_PII_TYPES = (
    "EMAIL",
    "PHONE",
    "PASSWORD",
    "PIN",
    "AWS_ACCESS_KEY",
    "AWS_SECRET_KEY",
    "CREDIT_DEBIT_CARD_NUMBER",
    "CREDIT_DEBIT_CARD_CVV",
    "CREDIT_DEBIT_CARD_EXPIRY",
    "US_SOCIAL_SECURITY_NUMBER",
    "US_PASSPORT_NUMBER",
    "US_BANK_ACCOUNT_NUMBER",
    "US_BANK_ROUTING_NUMBER",
    "INTERNATIONAL_BANK_ACCOUNT_NUMBER",
    "UK_NATIONAL_INSURANCE_NUMBER",
)

_ATTACKS = (
    (re.compile(r"\b(?:jailbreak|DAN\s+mode)\b", re.IGNORECASE), "JAILBREAK"),
    (
        re.compile(
            r"\byou\s+are\s+now\s+(?:a\s+)?(?:unrestricted|uncensored)\b",
            re.IGNORECASE,
        ),
        "JAILBREAK",
    ),
    (
        re.compile(
            r"\b(?:ignore|disregard)\s+(?:all\s+)?(?:previous|prior|above|earlier)\s+instructions\b",
            re.IGNORECASE,
        ),
        "PROMPT_INJECTION",
    ),
    (
        re.compile(
            r"\bdo\s+not\s+follow\s+(?:your\s+|the\s+)?(?:rules|instructions|guidelines)\b",
            re.IGNORECASE,
        ),
        "PROMPT_INJECTION",
    ),
    (
        re.compile(
            r"\b(?:reveal|show|print|repeat|dump)\s+(?:me\s+)?(?:your\s+)?"
            r"(?:hidden\s+|developer\s+|system\s+)prompt\b",
            re.IGNORECASE,
        ),
        "PROMPT_LEAKAGE",
    ),
)
_EMAIL = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")
_PHONE = re.compile(r"\b(?:\+91[\s\-]?)?[6-9]\d{9}\b")
_AADHAAR = re.compile(r"\b[2-9]\d{3}\s\d{4}\s\d{4}\b")
_SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_AWS_KEY = re.compile(r"\bAKIA[0-9A-Z]{16}\b")
_CARD = re.compile(r"\b(?:\d{4}[ \-]){3}\d{1,7}\b|\b\d{13,19}\b")
_SECRETS = (
    (re.compile(r"\bsk-or-v1-[A-Za-z0-9]{20,}\b"), "PASSWORD"),
    (re.compile(r"\bsk-lf-[A-Za-z0-9\-]{20,}\b"), "PASSWORD"),
    (re.compile(r"\bgsk_[A-Za-z0-9]{20,}\b"), "PASSWORD"),
    (re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"), "PASSWORD"),
)

_disabled_reason: str | None = None
_client = None
_client_lock = threading.Lock()
_cache: OrderedDict[str, "Decision"] = OrderedDict()
_cache_lock = threading.Lock()


@dataclass
class Finding:
    kind: str
    category: str
    score: float
    source: str
    begin: int | None = None
    end: int | None = None


@dataclass
class Decision:
    action: str
    text: str
    stage: str
    source: str
    findings: list[Finding] = field(default_factory=list)
    cacheable: bool = True

    @property
    def blocked(self) -> bool:
        return self.action == "block"

    @property
    def summary(self) -> str:
        return ",".join(f"{item.category}:{item.score:.1f}" for item in self.findings)


def screen_user_text(text: str, client=None) -> Decision:
    return _screen(text, "user", client=client)


def screen_context(text: str, client=None, *, bedrock: bool = True) -> Decision:
    return _screen(text, "context", client=client, bedrock=bedrock)


def screen_output(text: str, client=None) -> Decision:
    return _screen(text, "output", client=client)


def preview_for_log(text: str) -> str:
    """Redacted text safe to put in a trace. Never the raw blocked prompt."""
    decision = screen_user_text(text or "")
    if decision.blocked:
        return "[blocked by guardrail]"
    return decision.text


def _screen(text: str, stage: str, client=None, bedrock: bool = True) -> Decision:
    body = text or ""
    if not body.strip():
        return Decision("allow", body, stage, "none", cacheable=False)

    use_api = bedrock and (client is not None or _bedrock_active())
    cache_key = None
    if client is None:
        cache_key = _cache_key(stage, body, use_api)
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached

    findings = _local_findings(body)
    source = "local" if findings else "none"
    truncated = False
    api_used = False
    if use_api:
        remote, truncated, api_used = _bedrock_findings(body, stage, client)
        if remote:
            findings.extend(remote)
            source = "mixed" if source == "local" else "bedrock"
        elif api_used:
            source = "bedrock" if source == "none" else "mixed"
    findings = _collapse(findings)

    if truncated:
        decision = Decision(
            "block",
            PII_INCOMPLETE_REPLY,
            stage,
            source if source != "none" else "bedrock",
            findings,
            cacheable=api_used or not use_api,
        )
    else:
        decision = _decide(body, stage, findings, source)
        decision.cacheable = api_used or not use_api

    if decision.action != "allow":
        logger.info(
            "guardrail stage=%s action=%s source=%s findings=%s",
            stage,
            decision.action,
            decision.source,
            decision.summary,
        )
    if cache_key and decision.cacheable:
        _cache_put(cache_key, decision)
    return decision


def _decide(text: str, stage: str, findings: list[Finding], source: str) -> Decision:
    blocked = False
    for item in findings:
        if item.kind == "prompt_attack" and item.score >= PROMPT_BLOCK_SCORE:
            blocked = True
        elif item.kind == "content" and item.score >= CONTENT_BLOCK_SCORE:
            allowed = _OUTPUT_CONTENT_BLOCK if stage == "output" else _INPUT_CONTENT_BLOCK
            if stage != "context" and item.category in allowed:
                blocked = True
    if blocked:
        if stage == "context":
            reply = CONTEXT_BLOCKED_REPLY
        elif stage == "output":
            reply = OUTPUT_BLOCKED_REPLY
        else:
            reply = USER_BLOCKED_REPLY
        return Decision("block", reply, stage, source, findings)

    spans = [
        (item.begin, item.end, item.category)
        for item in findings
        if item.kind == "pii"
        and item.score >= PII_REDACT_SCORE
        and item.begin is not None
        and item.end is not None
    ]
    redacted = _apply_redactions(text, spans)
    action = "redact" if redacted != text else "allow"
    return Decision(action, redacted, stage, source, findings)


def _apply_redactions(text: str, spans: list[tuple[int, int, str]]) -> str:
    chosen: list[tuple[int, int, str]] = []
    for begin, end, label in sorted(spans, key=lambda item: (item[0], item[1])):
        if begin < 0 or end > len(text) or begin >= end:
            continue
        if chosen and begin < chosen[-1][1]:
            continue
        chosen.append((begin, end, label))
    updated = text
    for begin, end, label in reversed(chosen):
        updated = updated[:begin] + "{" + label + "}" + updated[end:]
    return updated


def _local_findings(text: str) -> list[Finding]:
    found: list[Finding] = []
    for pattern, category in _ATTACKS:
        if pattern.search(text):
            found.append(Finding("prompt_attack", category, 0.8, "local"))
    for pattern, category, kind in (
        (_EMAIL, "EMAIL", "pii"),
        (_PHONE, "PHONE", "pii"),
        (_AADHAAR, "AADHAAR", "pii"),
        (_SSN, "US_SOCIAL_SECURITY_NUMBER", "pii"),
        (_AWS_KEY, "AWS_ACCESS_KEY", "pii"),
    ):
        for match in pattern.finditer(text):
            found.append(
                Finding(kind, category, 0.8, "local", match.start(), match.end())
            )
    for pattern, category in _SECRETS:
        for match in pattern.finditer(text):
            found.append(Finding("pii", category, 0.8, "local", match.start(), match.end()))
    for match in _CARD.finditer(text):
        digits = re.sub(r"\D", "", match.group(0))
        if 13 <= len(digits) <= 19 and _luhn(digits):
            found.append(
                Finding(
                    "pii",
                    "CREDIT_DEBIT_CARD_NUMBER",
                    0.8,
                    "local",
                    match.start(),
                    match.end(),
                )
            )
    return found


def _luhn(digits: str) -> bool:
    total = 0
    for index, char in enumerate(digits[::-1]):
        value = int(char)
        if index % 2 == 1:
            value *= 2
            if value > 9:
                value -= 9
        total += value
    return total % 10 == 0


def _checks_for(stage: str) -> dict:
    attack = {"promptAttack": {"categories": [{"category": name} for name in _ATTACK_CATEGORIES]}}
    content = {"contentFilter": {"categories": [{"category": name} for name in _CONTENT_CATEGORIES]}}
    pii = {"sensitiveInformation": {"entities": [{"type": name} for name in _PII_TYPES]}}
    if stage == "context":
        return {**attack, **pii}
    if stage == "output":
        return {**content, **pii}
    return {**content, **attack, **pii}


def _bedrock_findings(text: str, stage: str, client) -> tuple[list[Finding], bool, bool]:
    """Return findings, truncated flag, and whether the API answered."""
    runtime = client or _runtime_client()
    if runtime is None:
        return [], False, False
    checks = _checks_for(stage)
    role = "assistant" if stage == "output" else "user"
    found: list[Finding] = []
    truncated = False
    start = 0
    size = len(text)
    while start < size:
        end = min(size, start + _CHUNK)
        chunk = text[start:end]
        payload = _invoke(runtime, role, chunk, checks)
        if payload is None:
            return found, truncated, False
        found.extend(_findings_from_response(payload, start))
        sensitive = ((payload.get("results") or {}).get("sensitiveInformation") or {})
        truncated = truncated or bool(sensitive.get("truncated"))
        if end >= size:
            break
        start = end - _OVERLAP
    return found, truncated, True


def _invoke(runtime, role: str, chunk: str, checks: dict) -> dict | None:
    try:
        return runtime.invoke_guardrail_checks(
            messages=[{"role": role, "content": [{"text": chunk}]}],
            checks=checks,
        )
    except Exception as exc:
        _note_failure(exc)
        return None


def _findings_from_response(payload: dict, offset: int) -> list[Finding]:
    results = (payload or {}).get("results") or {}
    found: list[Finding] = []
    for item in ((results.get("contentFilter") or {}).get("results") or []):
        score = _num(item.get("severityScore"))
        category = str(item.get("category") or "")
        if category:
            found.append(Finding("content", category, score, "bedrock"))
    for item in ((results.get("promptAttack") or {}).get("results") or []):
        score = _num(item.get("severityScore"))
        category = str(item.get("category") or "")
        if category:
            found.append(Finding("prompt_attack", category, score, "bedrock"))
    for item in ((results.get("sensitiveInformation") or {}).get("results") or []):
        if int(item.get("messageIndex") or 0) != 0:
            continue
        if int(item.get("contentIndex") or 0) != 0:
            continue
        begin = item.get("beginOffset")
        end = item.get("endOffset")
        category = str(item.get("type") or "PII")
        if begin is None or end is None:
            continue
        found.append(
            Finding(
                "pii",
                category,
                _num(item.get("confidenceScore")),
                "bedrock",
                int(begin) + offset,
                int(end) + offset,
            )
        )
    return found


def _collapse(findings: list[Finding]) -> list[Finding]:
    best: dict[tuple[str, str], Finding] = {}
    pii: list[Finding] = []
    seen: set[tuple[str, int, int]] = set()
    for item in findings:
        if item.kind == "pii" and item.begin is not None and item.end is not None:
            key = (item.category, item.begin, item.end)
            if key in seen:
                continue
            seen.add(key)
            pii.append(item)
            continue
        slot = (item.kind, item.category)
        current = best.get(slot)
        if current is None or item.score > current.score:
            best[slot] = item
    return list(best.values()) + pii


def _num(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _bedrock_active() -> bool:
    if _disabled_reason:
        return False
    flag = os.getenv("BEDROCK_GUARDRAILS_ENABLED", "auto").strip().lower()
    if flag in {"0", "false", "no", "off"}:
        return False
    if flag in {"1", "true", "yes", "on"}:
        return True
    return bool(
        os.getenv("AWS_ACCESS_KEY_ID")
        or os.getenv("AWS_CONTAINER_CREDENTIALS_RELATIVE_URI")
        or os.getenv("AWS_WEB_IDENTITY_TOKEN_FILE")
        or os.getenv("AWS_LAMBDA_FUNCTION_NAME")
    )


def _region() -> str:
    region = os.getenv("BEDROCK_GUARDRAILS_REGION") or os.getenv("AWS_REGION") or "ap-southeast-2"
    if region.strip().lower() in {"", "auto"}:
        return "ap-southeast-2"
    return region.strip()


def _runtime_client():
    global _client
    if _client is not None:
        return _client
    with _client_lock:
        if _client is not None:
            return _client
        try:
            import boto3
            from botocore.config import Config

            _client = boto3.client(
                "bedrock-runtime",
                region_name=_region(),
                config=Config(
                    retries={"max_attempts": 2, "mode": "adaptive"},
                    connect_timeout=2,
                    read_timeout=8,
                ),
            )
        except Exception as exc:
            _note_failure(exc)
            return None
    return _client


def _note_failure(exc: Exception) -> None:
    global _disabled_reason
    code = ""
    response = getattr(exc, "response", None)
    if isinstance(response, dict):
        code = str((response.get("Error") or {}).get("Code") or "")
    if code in {"AccessDeniedException", "UnrecognizedClientException"} or isinstance(
        exc, (ImportError, AttributeError)
    ):
        if not _disabled_reason:
            _disabled_reason = code or type(exc).__name__
            logger.warning(
                "Bedrock InvokeGuardrailChecks unavailable (%s). Using local checks.",
                _disabled_reason,
            )
        return
    logger.warning(
        "Bedrock InvokeGuardrailChecks failed (%s). Using local checks.",
        code or type(exc).__name__,
    )


def _cache_key(stage: str, text: str, use_api: bool) -> str:
    digest = hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()
    return f"{stage}:{int(use_api)}:{digest}"


def _cache_get(key: str) -> Decision | None:
    with _cache_lock:
        found = _cache.get(key)
        if found is not None:
            _cache.move_to_end(key)
        return found


def _cache_put(key: str, decision: Decision) -> None:
    with _cache_lock:
        _cache[key] = decision
        _cache.move_to_end(key)
        while len(_cache) > 64:
            _cache.popitem(last=False)
