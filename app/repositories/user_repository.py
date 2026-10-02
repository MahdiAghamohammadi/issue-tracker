from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import User

UserData = dict[str, Any]


class UserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    @staticmethod
    def _to_dict(user: User) -> UserData:
        return {
            "id": str(user.id),
            "email": user.email,
            "hashed_password": user.hashed_password,
            "is_active": user.is_active,
        }

    def get_by_id(self, user_id: str) -> UserData | None:
        try:
            parsed_id = UUID(user_id)
        except ValueError:
            return None
        user = self.session.get(User, parsed_id)
        return self._to_dict(user) if user is not None else None

    def get_by_email(self, email: str) -> UserData | None:
        user = self.session.scalar(select(User).where(User.email == email))
        return self._to_dict(user) if user is not None else None

    def create(self, user: UserData) -> UserData | None:
        model = User(
            id=UUID(user["id"]),
            email=user["email"],
            hashed_password=user["hashed_password"],
            is_active=user["is_active"],
        )
        self.session.add(model)
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            return None
        self.session.refresh(model)
        return self._to_dict(model)
