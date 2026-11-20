"""Command line: agentproof <command>."""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

from agentproof import __version__, bootstrap, envcheck, inventory, journal, ledger, redact, tasks, validate


def _root(args: argparse.Namespace) -> Path:
    return Path(args.root).resolve()


def cmd_init(args: argparse.Namespace) -> int:
    created, skipped = bootstrap.init(Path(args.target))
    for path in created:
        print(f"created  {path}")
    for path in skipped:
        print(f"kept     {path} (already exists)")
    hint = bootstrap.merge_hint(skipped)
    if hint:
        print("\n" + hint)
    print("\nNext: write knowledge/<product>/00-overview.md, then `agentproof new-task <slug>`.")
    return 0


def cmd_new_task(args: argparse.Namespace) -> int:
    today = dt.date.fromisoformat(args.date) if args.date else None
    try:
        folder = tasks.new_task(
            _root(args),
            args.slug,
            title=args.title,
            product=args.product,
            tier=args.tier,
            owner=args.owner,
            today=today,
        )
    except (ValueError, FileExistsError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    ledger.write(_root(args))
    print(f"created {folder.relative_to(_root(args)).as_posix()}/task.md (status: draft)")
    print("Fill in the contract, then set status: ready. Tier 2 needs the Approvals section first.")
    return 0


def cmd_ledger(args: argparse.Namespace) -> int:
    root = _root(args)
    if args.check:
        if ledger.is_current(root):
            print("ledger is current")
            return 0
        print("ledger is out of date: run `agentproof ledger`", file=sys.stderr)
        return 1
    path = ledger.write(root)
    print(f"wrote {path.relative_to(root).as_posix()} ({len(tasks.discover(root))} tasks)")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    today = dt.date.fromisoformat(args.today) if args.today else None
    issues = validate.validate(
        _root(args), today=today, stale_days=args.stale_days, max_doc_age=args.max_doc_age
    )
    for issue in sorted(issues, key=lambda i: (i.level != "error", i.path)):
        print(issue)
    errors = sum(1 for i in issues if i.level == "error")
    warnings = len(issues) - errors
    print(f"\n{errors} error(s), {warnings} warning(s)")
    if errors or (args.strict and warnings):
        return 1
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    cmd = list(args.command)
    if cmd and cmd[0] == "--":
        cmd = cmd[1:]
    try:
        result = journal.run(
            _root(args), cmd, task_id=args.task, mutating=args.mutating, host=args.host, timeout=args.timeout
        )
    except (journal.ProtocolError, LookupError, ValueError) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 3
    sys.stdout.write(redact.redact(result.stdout))
    sys.stderr.write(redact.redact(result.stderr))
    return result.exit_code


def cmd_redact(_args: argparse.Namespace) -> int:
    sys.stdout.write(redact.redact(sys.stdin.read()))
    return 0


def cmd_env_check(args: argparse.Namespace) -> int:
    rows = envcheck.check(_root(args))
    if not rows:
        print("no .env.example found, or it declares no variables")
        return 1
    width = max(len(name) for name, _ in rows)
    for name, is_set in rows:
        print(f"{name:<{width}}  {'set' if is_set else 'UNSET'}")
    return 0 if all(is_set for _, is_set in rows) else 1


def cmd_fingerprint(args: argparse.Namespace) -> int:
    try:
        result = inventory.fingerprint(_root(args), args.host)
    except LookupError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if result.could_not_check:
        print(f"COULD NOT CHECK {result.alias}: {result.detail}. Treat as a mismatch: stop.")
        return 2
    if result.ok:
        print(f"OK {result.alias}: {result.observed}")
        return 0
    print(
        f"MISMATCH {result.alias}: expected {result.expected!r}, observed {redact.redact(result.observed or '')!r}"
    )
    print("Stop. Do not change this target until the human has looked at it.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agentproof", description="A protocol for AI coding agents.")
    parser.add_argument("--version", action="version", version=f"agentproof {__version__}")
    parser.add_argument("--root", default=".", help="project root (default: current directory)")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init", help="add the protocol to a project (never overwrites)")
    p.add_argument("target", nargs="?", default=".")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("new-task", help="scaffold tasks/TASK-YYYYMMDD-NN-slug/")
    p.add_argument("slug")
    p.add_argument("--title")
    p.add_argument("--product", default="general")
    p.add_argument("--tier", type=int, default=1, choices=[0, 1, 2])
    p.add_argument("--owner", default="unassigned")
    p.add_argument("--date", help=argparse.SUPPRESS)
    p.set_defaults(func=cmd_new_task)

    p = sub.add_parser("ledger", help="regenerate tasks/README.md from task front matter")
    p.add_argument("--check", action="store_true", help="fail if the ledger is out of date")
    p.set_defaults(func=cmd_ledger)

    p = sub.add_parser("validate", help="check tasks, ledger, knowledge docs and inventory")
    p.add_argument("--stale-days", type=int, default=14)
    p.add_argument("--max-doc-age", type=int, default=90)
    p.add_argument("--strict", action="store_true", help="warnings fail too")
    p.add_argument("--today", help=argparse.SUPPRESS)
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("run", help="run a command and journal it into the task's evidence")
    p.add_argument("--task", help="task id (required for --mutating)")
    p.add_argument("--mutating", action="store_true", help="the command changes something")
    p.add_argument("--host", help="inventory alias the command targets (enables the production gate)")
    p.add_argument("--timeout", type=int, default=900)
    p.add_argument("command", nargs=argparse.REMAINDER)
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("redact", help="mask secrets in stdin")
    p.set_defaults(func=cmd_redact)

    p = sub.add_parser("env-check", help="which variables from .env.example are set (names only)")
    p.set_defaults(func=cmd_env_check)

    p = sub.add_parser("fingerprint", help="check a host's identity against inventory/hosts.yaml")
    p.add_argument("host")
    p.set_defaults(func=cmd_fingerprint)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
