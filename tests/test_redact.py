"""Fixtures are assembled at runtime so secret scanners don't flag this file."""

from agentproof.redact import redact

DASHES = "-" * 5


def test_env_values_of_secret_names_are_masked():
    env = {"PULSE_DB_PASSWORD": "not-a-real-pass-123", "PULSE_REGION": "eu-test-1"}
    out = redact("connecting with not-a-real-pass-123 in eu-test-1", env)
    assert "not-a-real-pass-123" not in out
    assert "***REDACTED:PULSE_DB_PASSWORD***" in out
    assert "eu-test-1" in out  # not a secret name


def test_private_key_block():
    block = f"{DASHES}BEGIN OPENSSH PRIVATE KEY{DASHES}\nAAAA\n{DASHES}END OPENSSH PRIVATE KEY{DASHES}"
    assert "AAAA" not in redact(f"before\n{block}\nafter", {})


def test_bearer_and_key_value_and_url_credentials():
    token = "x" * 24
    text = f"Authorization: Bearer {token}\npassword={token}\npostgres://app:{token}@db.example.com/pulse"
    out = redact(text, {})
    assert token not in out
    assert "db.example.com/pulse" in out


def test_common_token_shapes():
    gh = "ghp" + "_" + "A" * 36
    jwt = ".".join(["eyJ" + "a" * 12, "b" * 12, "c" * 12])
    out = redact(f"{gh} {jwt}", {})
    assert gh not in out and jwt not in out


def test_short_values_are_not_masked_everywhere():
    assert redact("abc", {"X_TOKEN": "abc"}) == "abc"
