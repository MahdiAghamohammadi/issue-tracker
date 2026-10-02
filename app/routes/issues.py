from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.repositories import JsonIssueRepository
from app.schema import (
    IssueCreate,
    IssueOut,
    IssuePageOut,
    IssuePriority,
    IssueSortField,
    IssueStatus,
    IssueUpdate,
    SortDirection,
)
from app.services import IssueNotFoundError, IssueService

router = APIRouter(prefix="/api/v1/issues", tags=["issues"])

issue_service = IssueService(JsonIssueRepository())


def get_issue_service() -> IssueService:
    return issue_service


IssueServiceDependency = Annotated[IssueService, Depends(get_issue_service)]


def not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Issue not found",
    )


@router.get("/", response_model=IssuePageOut)
def index(
    service: IssueServiceDependency,
    issue_status: IssueStatus | None = Query(default=None, alias="status"),
    priority: IssuePriority | None = None,
    search: str | None = Query(default=None, min_length=1, max_length=100),
    sort_by: IssueSortField = IssueSortField.created_at,
    sort_direction: SortDirection = SortDirection.desc,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """Return filtered, sorted, and paginated issues."""
    return service.list_issues(
        issue_status=issue_status,
        priority=priority,
        search=search,
        sort_by=sort_by,
        sort_direction=sort_direction,
        limit=limit,
        offset=offset,
    )


@router.get("/{issue_id}", response_model=IssueOut)
def get_issue(issue_id: str, service: IssueServiceDependency):
    """Return one issue by ID."""
    try:
        return service.get_issue(issue_id)
    except IssueNotFoundError as error:
        raise not_found() from error


@router.post("/", response_model=IssueOut, status_code=status.HTTP_201_CREATED)
def create_issue(payload: IssueCreate, service: IssueServiceDependency):
    """Create and persist an issue."""
    return service.create_issue(payload)


@router.patch("/{issue_id}", response_model=IssueOut)
def update_issue(
    issue_id: str,
    payload: IssueUpdate,
    service: IssueServiceDependency,
):
    """Partially update an issue."""
    try:
        return service.update_issue(issue_id, payload)
    except IssueNotFoundError as error:
        raise not_found() from error


@router.delete("/{issue_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_issue(issue_id: str, service: IssueServiceDependency):
    """Delete an issue by ID."""
    try:
        service.delete_issue(issue_id)
    except IssueNotFoundError as error:
        raise not_found() from error
