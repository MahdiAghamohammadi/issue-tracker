from datetime import datetime
from uuid import UUID

from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session

from app.models import Issue
from app.repositories.issue_repository import IssueData
from app.schema import (
    IssuePriority,
    IssueSortField,
    IssueStatus,
    SortDirection,
)


class SQLAlchemyIssueRepository:
    """Persist issue records in PostgreSQL through SQLAlchemy."""

    def __init__(self, session: Session) -> None:
        self.session = session

    @staticmethod
    def _to_dict(issue: Issue) -> IssueData:
        return {
            "id": str(issue.id),
            "owner_id": str(issue.owner_id) if issue.owner_id is not None else None,
            "title": issue.title,
            "description": issue.description,
            "priority": issue.priority.value,
            "status": issue.status.value,
            "created_at": issue.created_at,
            "updated_at": issue.updated_at,
        }

    @staticmethod
    def _parse_id(issue_id: str) -> UUID | None:
        try:
            return UUID(issue_id)
        except ValueError:
            return None

    @staticmethod
    def _parse_datetime(value: object) -> object:
        if isinstance(value, str):
            return datetime.fromisoformat(value)
        return value

    def list_all(self) -> list[IssueData]:
        issues = self.session.scalars(select(Issue)).all()
        return [self._to_dict(issue) for issue in issues]

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
        parsed_owner_id = UUID(owner_id)
        filters = [Issue.owner_id == parsed_owner_id]
        if issue_status is not None:
            filters.append(Issue.status == issue_status)
        if priority is not None:
            filters.append(Issue.priority == priority)
        if search:
            query = search.strip()
            filters.append(
                or_(
                    Issue.title.icontains(query, autoescape=True),
                    Issue.description.icontains(query, autoescape=True),
                )
            )

        sort_columns = {
            IssueSortField.created_at: Issue.created_at,
            IssueSortField.updated_at: Issue.updated_at,
            IssueSortField.title: func.lower(Issue.title),
            IssueSortField.priority: case(
                (Issue.priority == IssuePriority.low, 1),
                (Issue.priority == IssuePriority.medium, 2),
                (Issue.priority == IssuePriority.high, 3),
            ),
            IssueSortField.status: Issue.status,
        }
        sort_column = sort_columns[sort_by]
        ordering = (
            sort_column.desc()
            if sort_direction is SortDirection.desc
            else sort_column.asc()
        )

        total = self.session.scalar(
            select(func.count()).select_from(Issue).where(*filters)
        )
        statement = (
            select(Issue)
            .where(*filters)
            .order_by(ordering, Issue.id.asc())
            .limit(limit)
            .offset(offset)
        )
        issues = self.session.scalars(statement).all()
        return [self._to_dict(issue) for issue in issues], total or 0

    def get(self, issue_id: str, owner_id: str) -> IssueData | None:
        parsed_id = self._parse_id(issue_id)
        if parsed_id is None:
            return None
        issue = self.session.scalar(
            select(Issue).where(
                Issue.id == parsed_id,
                Issue.owner_id == UUID(owner_id),
            )
        )
        return self._to_dict(issue) if issue is not None else None

    def create(self, issue: IssueData) -> IssueData:
        model = Issue(
            **{
                **issue,
                "id": UUID(issue["id"]),
                "owner_id": UUID(issue["owner_id"]),
                "created_at": self._parse_datetime(issue["created_at"]),
                "updated_at": self._parse_datetime(issue["updated_at"]),
            }
        )
        self.session.add(model)
        self.session.commit()
        self.session.refresh(model)
        return self._to_dict(model)

    def update(
        self, issue_id: str, owner_id: str, changes: IssueData
    ) -> IssueData | None:
        parsed_id = self._parse_id(issue_id)
        if parsed_id is None:
            return None
        issue = self.session.scalar(
            select(Issue).where(
                Issue.id == parsed_id,
                Issue.owner_id == UUID(owner_id),
            )
        )
        if issue is None:
            return None

        for field, value in changes.items():
            if field in {"created_at", "updated_at"}:
                value = self._parse_datetime(value)
            setattr(issue, field, value)

        self.session.commit()
        self.session.refresh(issue)
        return self._to_dict(issue)

    def delete(self, issue_id: str, owner_id: str) -> bool:
        parsed_id = self._parse_id(issue_id)
        if parsed_id is None:
            return False
        issue = self.session.scalar(
            select(Issue).where(
                Issue.id == parsed_id,
                Issue.owner_id == UUID(owner_id),
            )
        )
        if issue is None:
            return False
        self.session.delete(issue)
        self.session.commit()
        return True
