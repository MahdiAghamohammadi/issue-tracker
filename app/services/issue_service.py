from datetime import datetime, timezone
from uuid import uuid4

from app.repositories.issue_repository import IssueData, IssueRepository
from app.schema import IssueCreate, IssueStatus, IssueUpdate


class IssueNotFoundError(Exception):
    """Raised when an issue does not exist."""


class IssueService:
    def __init__(self, repository: IssueRepository) -> None:
        self.repository = repository

    def list_issues(self) -> list[IssueData]:
        return self.repository.list_all()

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
