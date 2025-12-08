from __future__ import annotations
"""Connectivity helpers for IMAP/SMTP/POP3 testing and folder discovery."""
import asyncio
import poplib
import ssl
from typing import Dict, List, Optional
import aiosmtplib
import aioimaplib


def _validate_connection_params(host: str, port: int, username: str, password: str) -> None:
    """Validate connection parameters before attempting connection."""
    if not host or not host.strip():
        raise ValueError("Host cannot be empty")
    if not isinstance(port, int) or port <= 0 or port > 65535:
        raise ValueError(f"Invalid port: {port}")
    if not username or not username.strip():
        raise ValueError("Username cannot be empty")
    if not password:
        raise ValueError("Password cannot be empty")


async def test_smtp_connection(host: str, port: int, security: str, username: str, password: str, timeout: float = 15.0) -> Dict[str, str]:
    # Validate inputs first
    _validate_connection_params(host, port, username, password)
    host = host.strip()
    
    security = security.lower()
    start_tls = security == "starttls"
    use_tls = security == "ssl"

    smtp = aiosmtplib.SMTP(hostname=host, port=port, start_tls=start_tls, use_tls=use_tls, timeout=timeout)
    await smtp.connect()
    try:
        await smtp.ehlo()
        await smtp.login(username, password)
        return {"status": "ok", "message": "SMTP login succeeded"}
    finally:
        try:
            await smtp.quit()
        except Exception:
            pass


async def test_imap_connection(host: str, port: int, security: str, username: str, password: str, timeout: float = 15.0) -> Dict[str, str]:
    # Validate inputs first
    _validate_connection_params(host, port, username, password)
    host = host.strip()
    
    security = security.lower()
    if security == "ssl":
        # Create SSL context with server_hostname for proper SSL handshake
        ssl_context = ssl.create_default_context()
        imap = aioimaplib.IMAP4_SSL(host=host, port=port, timeout=timeout, ssl_context=ssl_context)
    else:
        imap = aioimaplib.IMAP4(host=host, port=port, timeout=timeout)
    await imap.wait_hello_from_server()
    if security == "starttls":
        ssl_context = ssl.create_default_context()
        await imap.starttls(ssl_context=ssl_context)
    await imap.login(username, password)
    try:
        typ, data = await imap.capability()
        capabilities = data[0].decode() if data else ""
    except Exception:
        capabilities = ""
    await imap.logout()
    return {"status": "ok", "message": "IMAP login succeeded", "capabilities": capabilities}


async def list_imap_folders(host: str, port: int, security: str, username: str, password: str, timeout: float = 20.0) -> List[str]:
    # Validate inputs first
    _validate_connection_params(host, port, username, password)
    host = host.strip()
    
    security = security.lower()
    if security == "ssl":
        # Create SSL context with server_hostname for proper SSL handshake
        ssl_context = ssl.create_default_context()
        imap = aioimaplib.IMAP4_SSL(host=host, port=port, timeout=timeout, ssl_context=ssl_context)
    else:
        imap = aioimaplib.IMAP4(host=host, port=port, timeout=timeout)
    await imap.wait_hello_from_server()
    if security == "starttls":
        ssl_context = ssl.create_default_context()
        await imap.starttls(ssl_context=ssl_context)
    await imap.login(username, password)
    typ, mailboxes = await imap.list()
    folders: List[str] = []
    if mailboxes:
        for raw in mailboxes:
            try:
                decoded = raw.decode()
                parts = decoded.split(' "')
                folder = parts[-1].strip('"') if parts else decoded
                folders.append(folder)
            except Exception:
                continue
    await imap.logout()
    return folders


async def test_pop3_connection(host: str, port: int, security: str, username: str, password: str, timeout: float = 15.0) -> Dict[str, str]:
    """Test POP3 connection (sync, run in executor for async compat)."""
    # Validate inputs first
    _validate_connection_params(host, port, username, password)
    host = host.strip()
    
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _sync_pop3_test, host, port, security, username, password, timeout)


def _sync_pop3_test(host: str, port: int, security: str, username: str, password: str, timeout: float) -> Dict[str, str]:
    security = security.lower()
    if security == "ssl":
        pop = poplib.POP3_SSL(host, port, timeout=timeout)
    else:
        pop = poplib.POP3(host, port, timeout=timeout)
        if security == "starttls":
            context = ssl.create_default_context()
            pop.stls(context=context)
    pop.user(username)
    pop.pass_(password)
    stat = pop.stat()
    pop.quit()
    return {"status": "ok", "message": f"POP3 login succeeded. {stat[0]} messages, {stat[1]} bytes"}
