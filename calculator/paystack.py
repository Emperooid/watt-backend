"""Thin wrapper around the Paystack REST API.

Uses the redirect-based "Initialize Transaction" flow: we create the
transaction server-side and hand the browser a hosted checkout URL, so the
frontend never needs the Paystack public key or any client-side SDK.
"""

import os

import requests

PAYSTACK_BASE_URL = "https://api.paystack.co"


class PaystackError(Exception):
    pass


def _secret_key() -> str:
    key = os.environ.get("PAYSTACK_SECRET_KEY", "").strip()
    if not key:
        raise PaystackError("PAYSTACK_SECRET_KEY is not configured.")
    return key


def _headers() -> dict:
    return {"Authorization": f"Bearer {_secret_key()}", "Content-Type": "application/json"}


def initialize_transaction(*, email: str, amount_kobo: int, reference: str, callback_url: str) -> dict:
    res = requests.post(
        f"{PAYSTACK_BASE_URL}/transaction/initialize",
        headers=_headers(),
        json={
            "email": email,
            "amount": amount_kobo,
            "reference": reference,
            "callback_url": callback_url,
            "currency": "NGN",
        },
        timeout=15,
    )
    data = res.json()
    if not res.ok or not data.get("status"):
        raise PaystackError(data.get("message", "Failed to initialize payment."))
    return data["data"]  # {authorization_url, access_code, reference}


def verify_transaction(reference: str) -> dict:
    res = requests.get(
        f"{PAYSTACK_BASE_URL}/transaction/verify/{reference}",
        headers=_headers(),
        timeout=15,
    )
    data = res.json()
    if not res.ok or not data.get("status"):
        raise PaystackError(data.get("message", "Failed to verify payment."))
    return data["data"]  # {status, amount, reference, customer: {email}, ...}
