from typing import Any, Protocol

from app.storage import load_data, save_data

IssueData = dict[str, Any]


class IssueRepository(Protocol):
    def list_all(self) -> list[IssueData]: ...

    def get(self, issue_id: str) -> IssueData | None: ...

    def create(self, issue: IssueData) -> IssueData: ...

    def update(self, issue_id: str, changes: IssueData) -> IssueData | None: ...

    def delete(self, issue_id: str) -> bool: ...


class JsonIssueRepository:
    """Persist issue records in the application's JSON data file."""

    def list_all(self) -> list[IssueData]:
        return load_data()

    def get(self, issue_id: str) -> IssueData | None:
        return next(
            (issue for issue in self.list_all() if issue["id"] == issue_id),
            None,
        )

    def create(self, issue: IssueData) -> IssueData:
        issues = self.list_all()
        issues.append(issue)
        save_data(issues)
        return issue

    def update(self, issue_id: str, changes: IssueData) -> IssueData | None:
        issues = self.list_all()
        for index, issue in enumerate(issues):
            if issue["id"] == issue_id:
                updated_issue = {**issue, **changes}
                issues[index] = updated_issue
                save_data(issues)
                return updated_issue
        return None

    def delete(self, issue_id: str) -> bool:
        issues = self.list_all()
        for index, issue in enumerate(issues):
            if issue["id"] == issue_id:
                issues.pop(index)
                save_data(issues)
                return True
        return False
