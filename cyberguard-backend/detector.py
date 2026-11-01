"""
Risk scoring engine.

Har incoming request 4 tarah ke checks se guzarta hai, har check kuch
points add karta hai (0-100 tak), phir total score se Low / Medium / High
risk level decide hota hai.

    Low     : 0  - 30
    Medium  : 31 - 60
    High    : 61 - 100
"""

import re
from datetime import datetime, timedelta, timezone
from urllib.parse import unquote_plus
from sqlalchemy.orm import Session

from models import RequestLog

SQLI_PATTERNS = [
    r"\bunion\b.{0,20}\bselect\b",
    r"\bor\b\s+['\"]?1['\"]?\s*=\s*['\"]?1",
    r"'\s*or\s*'?1'?\s*=\s*'?1",
    r"--\s",
    r";\s*drop\b\s+table\b",
    r"\bselect\b.{0,30}\bfrom\b",
    r"\bsleep\(\d+\)",
]

XSS_PATTERNS = [
    r"<script",
    r"onerror\s*=",
    r"onload\s*=",
    r"javascript:",
    r"<img[^>]+src",
]

PATH_TRAVERSAL_PATTERNS = [
    r"\.\./",
    r"\.\.\\",
    r"/etc/passwd",
    r"boot\.ini",
]

CMD_INJECTION_PATTERNS = [
    r";\s*(ls|cat|whoami|rm|wget|curl)\b",
    r"\|\s*nc\b",
    r"`.*`",
]

SUSPICIOUS_PATHS = [
    "/admin", "/.env", "/wp-login.php", "/.git",
    "/config", "/backup", "/phpmyadmin",
]

SCANNER_UA_KEYWORDS = [
    "sqlmap", "nikto", "nmap", "masscan", "acunetix", "nessus", "wpscan",
]


def _matches_any(patterns, text: str) -> bool:
    text_lower = text.lower()
    return any(re.search(p, text_lower) for p in patterns)


def get_recent_request_count(db: Session, ip: str, seconds: int = 60) -> int:
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=seconds)
    return (
        db.query(RequestLog)
        .filter(RequestLog.ip == ip, RequestLog.timestamp >= cutoff)
        .count()
    )


def analyze_request(
    db: Session,
    ip: str,
    method: str,
    path: str,
    query_string: str,
    user_agent: str,
    sql_injection_suspected: bool = False,
):
    score = 0
    reasons = []

    combined_text = f"{path} {unquote_plus(query_string or '')}"

    recent_count = get_recent_request_count(db, ip)
    request_count = recent_count + 1
    if request_count > 50:
        score += 65
        reasons.append(f"High request rate ({request_count} reqs/60s)")
    elif request_count > 20:
        score += 35
        reasons.append(f"Elevated request rate ({request_count} reqs/60s)")
    elif request_count > 10:
        score += 15
        reasons.append(f"Above-normal request rate ({request_count} reqs/60s)")

    if sql_injection_suspected or _matches_any(SQLI_PATTERNS, combined_text):
        score += 70
        reasons.append("Possible SQL Injection pattern")

    if _matches_any(XSS_PATTERNS, combined_text):
        score += 45
        reasons.append("Possible XSS pattern")

    if _matches_any(PATH_TRAVERSAL_PATTERNS, combined_text):
        score += 40
        reasons.append("Possible Path Traversal pattern")

    if _matches_any(CMD_INJECTION_PATTERNS, combined_text):
        score += 50
        reasons.append("Possible Command Injection pattern")

    if any(sp in path.lower() for sp in SUSPICIOUS_PATHS):
        score += 35
        reasons.append("Access attempt to sensitive path")

    ua_lower = (user_agent or "").lower()
    if not ua_lower:
        score += 10
        reasons.append("Missing User-Agent header")
    elif any(k in ua_lower for k in SCANNER_UA_KEYWORDS):
        score += 50
        reasons.append("Known scanner-tool User-Agent")

    score = min(score, 100)

    if score >= 61:
        level = "High"
    elif score >= 31:
        level = "Medium"
    else:
        level = "Low"

    return score, level, reasons
