import datetime as dt

from conftest import REPO

from agentproof import envcheck
from agentproof.bootstrap import init
from agentproof.cli import main
from agentproof.validate import validate


def test_init_creates_a_valid_project_and_never_overwrites(tmp_path):
    (tmp_path / "AGENTS.md").write_text("# mine\n", encoding="utf-8")
    created, skipped = init(tmp_path)
    assert "PROTOCOL.md" in created
    assert "AGENTS.md" in skipped
    assert (tmp_path / "AGENTS.md").read_text(encoding="utf-8") == "# mine\n"
    assert "](docs/agentproof/" in (tmp_path / "PROTOCOL.md").read_text(encoding="utf-8")
    assert (tmp_path / "templates" / "task.md").is_file()
    assert (tmp_path / ".claude" / "settings.json").is_file()
    assert [i for i in validate(tmp_path) if i.level == "error"] == []


def test_init_then_new_task_then_validate(tmp_path, capsys):
    init(tmp_path)
    assert (
        main(
            ["--root", str(tmp_path), "new-task", "web-fix-login", "--product", "web", "--date", "2026-09-14"]
        )
        == 0
    )
    assert main(["--root", str(tmp_path), "validate", "--today", "2026-09-14"]) == 0
    assert "TASK-20260914-01-web-fix-login" in (tmp_path / "tasks" / "README.md").read_text(encoding="utf-8")


def test_env_check_reports_names_only(tmp_path):
    (tmp_path / ".env.example").write_text("APP_TOKEN=changeme\nAPP_REGION=changeme\n", encoding="utf-8")
    (tmp_path / ".env.lab").write_text("APP_TOKEN=value-from-vault\n", encoding="utf-8")
    rows = dict(envcheck.check(tmp_path, environ={"AGENTPROOF_ENV": "lab"}))
    assert rows == {"APP_TOKEN": True, "APP_REGION": False}


def test_example_portfolio_validates():
    root = REPO / "examples" / "portfolio"
    issues = validate(root, today=dt.date(2026, 10, 20))
    assert [str(i) for i in issues if i.level == "error"] == []
