"""SpiderGPT Payment & Webhook Cryptographic Verification.

Verifies incoming webhook signatures for Razorpay and Stripe with constant-time comparisons.
"""
import hmac
import hashlib
import time
from typing import Optional
from backend.app.core.logging import logger


def verify_razorpay_signature(payload_body: bytes, signature: str, secret: str) -> bool:
    """Verifies Razorpay HMAC-SHA256 webhook signature."""
    if not signature or not secret:
        return False
    try:
        expected = hmac.new(
            secret.encode("utf-8"),
            payload_body,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)
    except Exception as e:
        logger.error("Error verifying Razorpay webhook signature: %s", str(e))
        return False


def verify_stripe_signature(
    payload_body: bytes,
    sig_header: str,
    secret: str,
    tolerance: int = 300,
) -> bool:
    """Verifies Stripe webhook signature (v1 header with timestamp checking)."""
    if not sig_header or not secret:
        return False
    try:
        parts = dict(item.strip().split("=", 1) for item in sig_header.split(",") if "=" in item)
        timestamp = parts.get("t")
        expected_sig = parts.get("v1")
        if not timestamp or not expected_sig:
            return False

        # Tolerance check
        now = int(time.time())
        if abs(now - int(timestamp)) > tolerance:
            logger.warning("Stripe webhook timestamp drift exceeded tolerance.")
            return False

        signed_payload = f"{timestamp}.".encode("utf-8") + payload_body
        computed_sig = hmac.new(
            secret.encode("utf-8"),
            signed_payload,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(computed_sig, expected_sig)
    except Exception as e:
        logger.error("Error verifying Stripe webhook signature: %s", str(e))
        return False
