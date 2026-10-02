from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID


class IssueStatus(str, Enum):
    open = "open",
    in_progress = "in_progress",
    closed = "closed",


class IssuePriority(str, Enum):
    low = "low",
    medium = "medium",
    high = "high"


class IssueSortField(str, Enum):
    created_at = "created_at"
    updated_at = "updated_at"
    title = "title"
    priority = "priority"
    status = "status"


class SortDirection(str, Enum):
    asc = "asc"
    desc = "desc"


class IssueCreate(BaseModel):
    title: str = Field(min_length=3, max_length=100)
    description: str = Field(min_length=5, max_length=1000)
    priority: IssuePriority = IssuePriority.medium


class IssueUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=3, max_length=100)
    description: Optional[str] = Field(default=None, min_length=5, max_length=1000)
    priority: Optional[IssuePriority] = None
    status: Optional[IssueStatus] = None


class IssueOut(BaseModel):
    id: UUID
    title: str
    description: str
    priority: IssuePriority
    status: IssueStatus
    created_at: datetime
    updated_at: datetime


class IssuePageOut(BaseModel):
    items: list[IssueOut]
    total: int
    limit: int
    offset: int
