from datetime import datetime, timezone
from uuid import uuid4

from app.repositories.issue_repository import IssueData, IssueRepository
from app.schema import (
    IssueCreate,
    IssuePriority,
    IssueSortField,
    IssueStatus,
    IssueUpdate,
    SortDirection,
)


class IssueNotFoundError(Exception):
    """Raised when an issue does not exist."""


class IssueService:
    def __init__(self, repository: IssueRepository) -> None:
        self.repository = repository

    def list_issues(
        self,
        *,
        issue_status: IssueStatus | None = None,
        priority: IssuePriority | None = None,
        search: str | None = None,
        sort_by: IssueSortField = IssueSortField.created_at,
        sort_direction: SortDirection = SortDirection.desc,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, object]:
        issues = self.repository.list_all()

        if issue_status is not None:
            issues = [issue for issue in issues if issue["status"] == issue_status.value]
        if priority is not None:
            issues = [issue for issue in issues if issue["priority"] == priority.value]
        if search:
            query = search.casefold().strip()
            issues = [
                issue
                for issue in issues
                if query in issue["title"].casefold()
                or query in issue["description"].casefold()
            ]

        priority_rank = {"low": 1, "medium": 2, "high": 3}

        def sort_value(issue: IssueData):
            value = issue[sort_by.value]
            if sort_by is IssueSortField.priority:
                return priority_rank[value]
            if isinstance(value, str):
                return value.casefold()
            return value

        issues.sort(
            key=sort_value,
            reverse=sort_direction is SortDirection.desc,
        )
        total = len(issues)

        return {
            "items": issues[offset : offset + limit],
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    def get_issue(self, issue_id: str) -> IssueData:
        issue = self.repository.get(issue_id)
        if issue is None:
            raise IssueNotFoundError
        return issue

    def create_issue(self, payload: IssueCreate) -> IssueData:
        now = datetime.now(timezone.utc).isoformat()
        issue: IssueData = {
            "id": str(uuid4()),
            **payload.model_dump(mode="json"),
            "status": IssueStatus.open.value,
            "created_at": now,
            "updated_at": now,
        }
        return self.repository.create(issue)

    def update_issue(self, issue_id: str, payload: IssueUpdate) -> IssueData:
        changes = payload.model_dump(exclude_none=True, mode="json")
        changes["updated_at"] = datetime.now(timezone.utc).isoformat()
        issue = self.repository.update(issue_id, changes)
        if issue is None:
            raise IssueNotFoundError
        return issue

    def delete_issue(self, issue_id: str) -> None:
        if not self.repository.delete(issue_id):
            raise IssueNotFoundError
