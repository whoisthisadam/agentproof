# Contributing

Thanks for your interest. Issues and pull requests are welcome.

## Before you open a pull request

```bash
pip install -e ".[dev]"
pytest
ruff check src tests
agentproof --root examples/portfolio validate
pre-commit run --all-files     # runs gitleaks
```

All four must pass. CI runs the same checks.

## What makes a good change

- **Protocol changes** (`PROTOCOL.md`) need a short ADR in `examples/portfolio/decisions/` or a clear explanation in the PR: what failed without the rule, and what the rule costs. If the rule comes from a real incident, add the story to `docs/lessons.md` with all identifying details removed.
- **Keep it short.** A rule that needs a paragraph to explain is usually two rules or none.
- **Templates and the validator move together.** If you add a required section to a template, teach `agentproof validate` about it in the same PR, with a test.
- **Every CLI bug gets a regression test.**

## Example data

Everything in `examples/` is fictional. Use `example.com` / `example.org` / `example.net` for domains, `192.0.2.0/24`, `198.51.100.0/24` or `203.0.113.0/24` for IPs, invented names, and obvious placeholders such as `changeme` or `<YOUR_TOKEN>` for secrets. Never paste real logs, hostnames or keys, even redacted.
