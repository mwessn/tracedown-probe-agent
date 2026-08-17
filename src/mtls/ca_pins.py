"""Trust-anchor pinning for the CA bundle.

The scheduler hands the agent a CA trust bundle at bootstrap and, again, on
every renewal.  Blindly overwriting the stored CA with whatever a renewal
response contains lets an on-path attacker replace the trust anchor and then
present a certificate of their own.  To prevent that:

* At bootstrap (trust-on-first-use) the agent records the SHA-256 fingerprints
  of every CA in the bundle it received — the pin set.
* On renewal the agent recomputes the fingerprints of the *new* bundle and
  accepts it only if it still contains at least one pinned CA.  A legitimate CA
  rotation is make-before-break (the new bundle carries both the old and the
  new CA), so continuity holds; a wholesale swap to an attacker CA breaks it and
  is refused.

The pin set is then advanced to the new bundle's fingerprints, so once an old
CA finally expires and drops out of the bundle the pin follows it forward.
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import serialization

log = logging.getLogger(__name__)


def ca_fingerprints(ca_bundle_pem: str) -> set[str]:
    """Return the SHA-256 fingerprints (hex) of every certificate in a PEM bundle."""
    try:
        certs = x509.load_pem_x509_certificates(ca_bundle_pem.encode("utf-8"))
    except Exception as exc:  # noqa: BLE001 — malformed bundle → no usable pins
        log.warning("could not parse CA bundle for pinning: %s", exc)
        return set()
    return {
        hashlib.sha256(c.public_bytes(serialization.Encoding.DER)).hexdigest()
        for c in certs
    }


def read_pins(pins_path: Path) -> set[str]:
    """Load the persisted pin set; empty when none has been recorded yet."""
    if not pins_path.exists():
        return set()
    return {
        line.strip()
        for line in pins_path.read_text().splitlines()
        if line.strip()
    }


def write_pins(pins_path: Path, fingerprints: set[str]) -> None:
    """Persist the pin set (one fingerprint per line)."""
    pins_path.parent.mkdir(parents=True, exist_ok=True)
    pins_path.write_text("".join(f"{fp}\n" for fp in sorted(fingerprints)))


def bundle_preserves_pins(new_bundle_pem: str, pinned: set[str]) -> bool:
    """True if [new_bundle_pem] still contains at least one pinned CA.

    With no pins recorded yet (first-ever bootstrap), continuity is vacuously
    satisfied — the caller records pins at that point.
    """
    if not pinned:
        return True
    return not ca_fingerprints(new_bundle_pem).isdisjoint(pinned)
