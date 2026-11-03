#!/usr/bin/env python3
"""Unit checks for opaque credential redaction. Synthetic values only."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "resources"))

import dsh_session_reader as reader  # noqa: E402

BEARER = "VALIDATOR_OPAQUE_CREDENTIAL_authorization_bearer_text_0123456789"
BASIC = "VALIDATOR_OPAQUE_CREDENTIAL_authorization_basic_text_0123456789"
API_JSON = "VALIDATOR_OPAQUE_CREDENTIAL_api_key_json_0123456789"
APIKEY = "OPAQUE_APIKEY_VALUE_0123456789"
API_KEY = "OPAQUE_API_KEY_VALUE_0123456789"
ACCESS = "OPAQUE_ACCESS_TOKEN_VALUE_0123456789"
SECRET = "OPAQUE_SECRET_VALUE_0123456789"
AUTHZ = "OPAQUE_AUTHZ_VALUE_0123456789"
CLIENT = "OPAQUE_CLIENT_SECRET_VALUE_0123456789"
PASSWORD = "OPAQUE_PASSWORD_VALUE_0123456789"
ASSIGN = "OPAQUE_ASSIGN_VALUE_0123456789"

TOKENS = [BEARER, BASIC, API_JSON, APIKEY, API_KEY, ACCESS, SECRET, AUTHZ, CLIENT, PASSWORD, ASSIGN]


def expect_hidden(label: str, raw: str, rendered: str) -> None:
    leaked = [token for token in TOKENS if token in rendered]
    if leaked:
        raise SystemExit(f"{label} leaked {leaked}: {rendered}")
    if "[REDACTED]" not in rendered:
        raise SystemExit(f"{label} did not redact: {rendered}")


def main() -> None:
    patterns = reader._apply_secret_patterns
    expect_hidden(
        "authorization bearer",
        f"Authorization: Bearer {BEARER}",
        patterns(f"Authorization: Bearer {BEARER}"),
    )
    if patterns(f"Authorization: Bearer {BEARER}") != "Authorization: [REDACTED]":
        raise SystemExit(patterns(f"Authorization: Bearer {BEARER}"))
    if patterns(f"Authorization: Basic {BASIC}") != "Authorization: [REDACTED]":
        raise SystemExit(patterns(f"Authorization: Basic {BASIC}"))
    if patterns(f"Bearer {BEARER}") != "Bearer [REDACTED]":
        raise SystemExit(patterns(f"Bearer {BEARER}"))
    if patterns(f"Basic {BASIC}") != "Basic [REDACTED]":
        raise SystemExit(patterns(f"Basic {BASIC}"))
    if patterns(f"OPENAI_API_KEY={ASSIGN}") != "OPENAI_API_KEY=[REDACTED]":
        raise SystemExit(patterns(f"OPENAI_API_KEY={ASSIGN}"))
    if patterns(f"apiKey={APIKEY}") != "apiKey=[REDACTED]":
        raise SystemExit(patterns(f"apiKey={APIKEY}"))

    quoted = {
        "apiKey": APIKEY,
        "api_key": API_KEY,
        "OPENAI_API_KEY": API_JSON,
        "access_token": ACCESS,
        "secret": SECRET,
        "authorization": f"Bearer {AUTHZ}",
        "client_secret": CLIENT,
        "password": PASSWORD,
    }
    for key, token in quoted.items():
        for raw in (
            f'{{"{key}":"{token}"}}',
            f'{{"{key}": "{token}"}}',
            "{'" + key + "': '" + token + "'}",
        ):
            expect_hidden(f"pattern {key}", raw, patterns(raw))
            expect_hidden(f"text {key}", raw, reader._redact_text(raw))

    escaped = '{\\"OPENAI_API_KEY\\":\\"' + API_JSON + '\\"}'
    expect_hidden("escaped json key", escaped, patterns(escaped))
    # _json_preview dumps the inner JSON with a space after the colon, then escapes it.
    nested = json.dumps({"command": json.dumps({"OPENAI_API_KEY": API_JSON})})
    expect_hidden("nested tool json", nested, reader._redact_text(nested))
    expect_hidden("nested tool patterns", nested, patterns(nested))

    structured = {
        "apiKey": APIKEY,
        "api_key": API_KEY,
        "access_token": ACCESS,
        "secret": SECRET,
        "authorization": f"Bearer {AUTHZ}",
        "client_secret": CLIENT,
        "password": PASSWORD,
        "command": f"Authorization: Basic {BASIC}",
        "note": "tokenizer=bert token_count=3",
    }
    redacted = reader._redact_output(structured)
    for key in ("apiKey", "api_key", "access_token", "secret", "authorization", "client_secret", "password"):
        if redacted[key] != "[REDACTED]":
            raise SystemExit(f"dict {key} -> {redacted[key]!r}")
    if BASIC in redacted["command"] or "Basic " + BASIC in redacted["command"]:
        raise SystemExit(redacted["command"])
    if redacted["note"] != structured["note"]:
        raise SystemExit(f"benign text changed: {redacted['note']}")
    if any(token in str(redacted) for token in TOKENS):
        raise SystemExit(f"dict walk leaked: {redacted}")

    print("ok")


if __name__ == "__main__":
    main()
