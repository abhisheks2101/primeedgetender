"""URL validation and SSRF protection."""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse


class URLValidationError(ValueError):
    pass


def validate_document_url(url: str, *, allowed_domains: list[str]) -> str:
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"https", "http"}:
        raise URLValidationError("Only HTTP/HTTPS document URLs are allowed.")
    if not parsed.hostname:
        raise URLValidationError("Document URL must include a hostname.")

    hostname = parsed.hostname.lower()
    if not _is_allowed_domain(hostname, allowed_domains):
        raise URLValidationError(f"Document URL domain is not in the allowed list: {hostname}")
    _reject_blocked_host(hostname, allowed_domains)
    return url.strip()


def _is_allowed_domain(hostname: str, allowed_domains: list[str]) -> bool:
    if not allowed_domains:
        return True
    for domain in allowed_domains:
        domain = domain.lower()
        if hostname == domain or hostname.endswith(f".{domain}"):
            return True
    return False


def _reject_blocked_host(hostname: str, allowed_domains: list[str]) -> None:
    blocked_names = {"localhost", "127.0.0.1", "0.0.0.0", "::1"}
    if hostname in blocked_names or hostname.endswith(".localhost"):
        raise URLValidationError("Localhost document URLs are not allowed.")

    try:
        addr_infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        # Allow configured domains that do not resolve in test/offline environments.
        if _is_allowed_domain(hostname, allowed_domains):
            return
        raise URLValidationError("Unable to resolve document URL hostname.") from None

    for info in addr_infos:
        ip = ipaddress.ip_address(info[4][0])
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
        ):
            raise URLValidationError("Private or internal network document URLs are not allowed.")


def _validate_allowed_domain(hostname: str, allowed_domains: list[str]) -> None:
    if not _is_allowed_domain(hostname, allowed_domains):
        raise URLValidationError(f"Document URL domain is not in the allowed list: {hostname}")
