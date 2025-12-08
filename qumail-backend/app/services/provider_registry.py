from __future__ import annotations
"""Email provider registry and detection for IMAP/SMTP settings.

This module provides a small in-memory registry of popular providers and
manual override support. It keeps logic isolated so routes can stay thin.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional
import re


@dataclass(frozen=True)
class ProviderSettings:
    name: str
    domains: List[str]
    smtp_host: str
    smtp_port: int
    smtp_security: str  # "ssl" | "starttls"
    imap_host: str
    imap_port: int
    imap_security: str  # "ssl" | "starttls"
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, str]:
        return {
            "name": self.name,
            "domains": self.domains,
            "smtp_host": self.smtp_host,
            "smtp_port": self.smtp_port,
            "smtp_security": self.smtp_security,
            "imap_host": self.imap_host,
            "imap_port": self.imap_port,
            "imap_security": self.imap_security,
            "notes": self.notes or "",
        }


# Preset providers with conservative defaults. Ports/security match
# the user specification where given, otherwise common secure choices.
PROVIDERS: List[ProviderSettings] = [
    ProviderSettings(
        name="Gmail",
        domains=["gmail.com"],
        smtp_host="smtp.gmail.com",
        smtp_port=587,
        smtp_security="starttls",
        imap_host="imap.gmail.com",
        imap_port=993,
        imap_security="ssl",
        notes="Requires app password when 2FA is enabled",
    ),
    ProviderSettings(
        name="Yahoo",
        domains=["yahoo.com", "yahoo.co.in"],
        smtp_host="smtp.mail.yahoo.com",
        smtp_port=587,
        smtp_security="starttls",
        imap_host="imap.mail.yahoo.com",
        imap_port=993,
        imap_security="ssl",
        notes="Often needs app password",
    ),
    ProviderSettings(
        name="Outlook",
        domains=["outlook.com", "hotmail.com", "office365.com"],
        smtp_host="smtp-mail.outlook.com",
        smtp_port=587,
        smtp_security="starttls",
        imap_host="outlook.office365.com",
        imap_port=993,
        imap_security="ssl",
        notes="Supports OAuth2",
    ),
    ProviderSettings(
        name="Rediffmail",
        domains=["rediffmail.com"],
        smtp_host="smtp.rediffmail.com",
        smtp_port=465,
        smtp_security="ssl",
        imap_host="pop.rediffmail.com",
        imap_port=995,
        imap_security="ssl",
        notes="Uses POP3 (not IMAP). POP3 on port 995 SSL.",
    ),
    ProviderSettings(
        name="Zoho",
        domains=["zoho.com"],
        smtp_host="smtp.zoho.com",
        smtp_port=465,
        smtp_security="ssl",
        imap_host="imap.zoho.com",
        imap_port=993,
        imap_security="ssl",
        notes="May require app password",
    ),
    ProviderSettings(
        name="ProtonMail (Bridge)",
        domains=["protonmail.com"],
        smtp_host="127.0.0.1",
        smtp_port=1025,
        smtp_security="starttls",
        imap_host="127.0.0.1",
        imap_port=1143,
        imap_security="starttls",
        notes="Requires ProtonMail Bridge app",
    ),
    ProviderSettings(
        name="iCloud",
        domains=["icloud.com", "me.com"],
        smtp_host="smtp.mail.me.com",
        smtp_port=587,
        smtp_security="starttls",
        imap_host="imap.mail.me.com",
        imap_port=993,
        imap_security="ssl",
        notes="Needs app-specific password",
    ),
    ProviderSettings(
        name="AOL",
        domains=["aol.com"],
        smtp_host="smtp.aol.com",
        smtp_port=587,
        smtp_security="starttls",
        imap_host="imap.aol.com",
        imap_port=993,
        imap_security="ssl",
        notes="Needs app password",
    ),
    ProviderSettings(
        name="GMX",
        domains=["gmx.com", "gmx.net"],
        smtp_host="mail.gmx.com",
        smtp_port=587,
        smtp_security="starttls",
        imap_host="imap.gmx.com",
        imap_port=993,
        imap_security="ssl",
        notes="",
    ),
]


def detect_provider(email: str) -> Dict[str, str]:
    """Detect provider settings based on email domain.

    Returns dict with mode:
    - preset: matched a known provider
    - manual: no preset found; caller should collect full settings
    """
    domain = email.split("@")[-1].lower().strip()
    for provider in PROVIDERS:
        for pat in provider.domains:
            if _domain_matches(domain, pat):
                return {
                    "mode": "preset",
                    "provider": provider.name,
                    "settings": provider.to_dict(),
                }
    return {
        "mode": "manual",
        "provider": "Custom",
        "settings": None,
    }


def list_providers() -> List[Dict[str, str]]:
    return [p.to_dict() for p in PROVIDERS]


def _domain_matches(domain: str, pattern: str) -> bool:
    if pattern == "*":
        return True
    return domain == pattern or domain.endswith(f".{pattern}") or bool(re.fullmatch(pattern, domain))
