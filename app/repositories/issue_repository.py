from typing import Any, Protocol

from app.schema import (
    IssuePriority,
    IssueSortField,
    IssueStatus,
    SortDirection,
)
from app.storage import load_data, save_data

IssueData = dict[str, Any]


class IssueRepository(Protocol):
    def list_page(
        self,
        *,
        owner_id: str,
        issue_status: IssueStatus | None,
        priority: IssuePriority | None,
        search: str | None,
        sort_by: IssueSortField,
        sort_direction: SortDirection,
        limit: int,
        offset: int,
    ) -> tuple[list[IssueData], int]: ...

    def get(self, issue_id: str, owner_id: str) -> IssueData | None: ...

    def create(self, issue: IssueData) -> IssueData: ...

    def update(
        self, issue_id: str, owner_id: str, changes: IssueData
    ) -> IssueData | None: ...

    def delete(self, issue_id: str, owner_id: str) -> bool: ...


class JsonIssueRepository:
    """Persist issue records in the application's JSON data file."""

    def list_all(self) -> list[IssueData]:
        return load_data()

    def list_page(
        self,
        *,
        owner_id: str,
        issue_status: IssueStatus | None,
        priority: IssuePriority | None,
        search: str | None,
        sort_by: IssueSortField,
        sort_direction: SortDirection,
        limit: int,
        offset: int,
    ) -> tuple[list[IssueData], int]:
        issues = [
            issue for issue in self.list_all() if issue.get("owner_id") == owner_id
        ]
        if issue_status is not None:
            issues = [
                issue for issue in issues if issue["status"] == issue_status.value
            ]
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
        return issues[offset : offset + limit], len(issues)

    def get(self, issue_id: str, owner_id: str) -> IssueData | None:
        return next(
            (
                issue
                for issue in self.list_all()
                if issue["id"] == issue_id and issue.get("owner_id") == owner_id
            ),
            None,
        )

    def create(self, issue: IssueData) -> IssueData:
        issues = self.list_all()
        issues.append(issue)
        save_data(issues)
        return issue

    def update(
        self, issue_id: str, owner_id: str, changes: IssueData
    ) -> IssueData | None:
        issues = self.list_all()
        for index, issue in enumerate(issues):
            if issue["id"] == issue_id and issue.get("owner_id") == owner_id:
                updated_issue = {**issue, **changes}
                issues[index] = updated_issue
                save_data(issues)
                return updated_issue
        return None

    def delete(self, issue_id: str, owner_id: str) -> bool:
        issues = self.list_all()
        for index, issue in enumerate(issues):
            if issue["id"] == issue_id and issue.get("owner_id") == owner_id:
                issues.pop(index)
                save_data(issues)
                return True
        return False
