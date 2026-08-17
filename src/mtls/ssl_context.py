"""SSL context builders for mTLS.

``build_server_context`` — used by uvicorn to serve HTTPS and require
client certificates (mutual TLS).

``build_client_context`` — used by httpx when the agent calls the
scheduler (e.g. during bootstrap or result submission).
"""

from __future__ import annotations

import ssl
from pathlib import Path

from config import AgentSettings


def build_server_context(settings: AgentSettings) -> ssl.SSLContext:
    """Build an SSL context for the uvicorn HTTPS server.

    Requires the client to present a valid certificate signed by our CA
    (mutual TLS). Crucially, a ``PROTOCOL_TLS_SERVER`` context verifies the
    client certificate for the *TLS client* purpose, so OpenSSL rejects a peer
    whose EKU is ``serverAuth``-only ("unsuitable certificate purpose"). Agent
    certificates are issued ``serverAuth``-only and only the scheduler holds a
    ``clientAuth`` certificate — so this is what pins inbound access to the
    scheduler: one agent can never use its own certificate to dial another
    agent's ``/probe`` endpoint.
    """
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    ctx.load_cert_chain(
        certfile=settings.cert_path,
        keyfile=settings.key_path,
    )
    ctx.load_verify_locations(cafile=settings.ca_cert_path)
    ctx.verify_mode = ssl.CERT_REQUIRED
    ctx.check_hostname = False
    return ctx


def build_client_context(settings: AgentSettings) -> ssl.SSLContext:
    """Build an SSL context for outbound HTTPS calls (e.g. to scheduler).

    Presents our agent certificate and verifies the peer's CA.
    """
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    ctx.load_cert_chain(
        certfile=settings.cert_path,
        keyfile=settings.key_path,
    )
    ctx.load_verify_locations(cafile=settings.ca_cert_path)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_REQUIRED
    return ctx


def certs_exist(settings: AgentSettings) -> bool:
    """Return True if all three certificate files exist on disk."""
    return (
        Path(settings.ca_cert_path).exists()
        and Path(settings.cert_path).exists()
        and Path(settings.key_path).exists()
    )
