from datetime import UTC, datetime
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
        owner_id: str,
        issue_status: IssueStatus | None = None,
        priority: IssuePriority | None = None,
        search: str | None = None,
        sort_by: IssueSortField = IssueSortField.created_at,
        sort_direction: SortDirection = SortDirection.desc,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, object]:
        issues, total = self.repository.list_page(
            owner_id=owner_id,
            issue_status=issue_status,
            priority=priority,
            search=search,
            sort_by=sort_by,
            sort_direction=sort_direction,
            limit=limit,
            offset=offset,
        )

        return {
            "items": issues,
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    def get_issue(self, issue_id: str, owner_id: str) -> IssueData:
        issue = self.repository.get(issue_id, owner_id)
        if issue is None:
            raise IssueNotFoundError
        return issue

    def create_issue(self, payload: IssueCreate, owner_id: str) -> IssueData:
        now = datetime.now(UTC).isoformat()
        issue: IssueData = {
            "id": str(uuid4()),
            "owner_id": owner_id,
            **payload.model_dump(mode="json"),
            "status": IssueStatus.open.value,
            "created_at": now,
            "updated_at": now,
        }
        return self.repository.create(issue)

    def update_issue(
        self, issue_id: str, payload: IssueUpdate, owner_id: str
    ) -> IssueData:
        changes = payload.model_dump(exclude_none=True, mode="json")
        changes["updated_at"] = datetime.now(UTC).isoformat()
        issue = self.repository.update(issue_id, owner_id, changes)
        if issue is None:
            raise IssueNotFoundError
        return issue

    def delete_issue(self, issue_id: str, owner_id: str) -> None:
        if not self.repository.delete(issue_id, owner_id):
            raise IssueNotFoundError
