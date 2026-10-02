from pathlib import Path

from app import storage
from app.repositories.issue_repository import JsonIssueRepository
from app.schema import IssuePriority, IssueSortField, IssueStatus, SortDirection


def issue_data(
    issue_id: str,
    owner_id: str,
    title: str,
    priority: str = "medium",
) -> dict[str, object]:
    return {
        "id": issue_id,
        "owner_id": owner_id,
        "title": title,
        "description": f"Description for {title}",
        "priority": priority,
        "status": "open",
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-01T00:00:00+00:00",
    }


def configure_storage(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(storage, "DATA_DIR", tmp_path)
    monkeypatch.setattr(storage, "DATA_FILE", tmp_path / "issues.json")


def test_json_repository_crud(monkeypatch, tmp_path: Path) -> None:
    configure_storage(monkeypatch, tmp_path)
    repository = JsonIssueRepository()
    issue = issue_data("issue-1", "owner-1", "Unicode café")

    assert repository.list_all() == []
    assert repository.create(issue) == issue
    assert repository.get("issue-1", "owner-1") == issue
    assert repository.get("issue-1", "owner-2") is None

    updated = repository.update(
        "issue-1", "owner-1", {"status": "closed", "title": "Updated title"}
    )
    assert updated is not None
    assert updated["status"] == "closed"
    assert repository.update("missing", "owner-1", {"status": "closed"}) is None

    assert not repository.delete("issue-1", "owner-2")
    assert repository.delete("issue-1", "owner-1")
    assert not repository.delete("issue-1", "owner-1")
    assert repository.list_all() == []
    assert list(tmp_path.glob("tmp*")) == []


def test_json_repository_filter_sort_and_paginate(monkeypatch, tmp_path: Path) -> None:
    configure_storage(monkeypatch, tmp_path)
    repository = JsonIssueRepository()
    repository.create(issue_data("1", "owner-1", "Login audit", "medium"))
    repository.create(issue_data("2", "owner-1", "Login failure", "high"))
    repository.create(issue_data("3", "owner-1", "Dark mode", "low"))
    repository.create(issue_data("4", "owner-2", "Private login", "high"))

    items, total = repository.list_page(
        owner_id="owner-1",
        issue_status=IssueStatus.open,
        priority=None,
        search="LOGIN",
        sort_by=IssueSortField.priority,
        sort_direction=SortDirection.desc,
        limit=1,
        offset=0,
    )
    low_priority_items, low_priority_total = repository.list_page(
        owner_id="owner-1",
        issue_status=None,
        priority=IssuePriority.low,
        search=None,
        sort_by=IssueSortField.title,
        sort_direction=SortDirection.asc,
        limit=20,
        offset=0,
    )

    assert total == 2
    assert [item["title"] for item in items] == ["Login failure"]
    assert low_priority_total == 1
    assert low_priority_items[0]["title"] == "Dark mode"


def test_storage_reads_an_empty_file(monkeypatch, tmp_path: Path) -> None:
    configure_storage(monkeypatch, tmp_path)
    storage.DATA_FILE.touch()

    assert storage.load_data() == []
