from uuid import uuid4

from sqlalchemy.orm import Session, sessionmaker

from app.repositories.user_repository import UserRepository
from app.security import hash_password


def test_user_repository_handles_invalid_id_and_unique_email(
    session_factory: sessionmaker[Session],
) -> None:
    user_id = str(uuid4())
    user = {
        "id": user_id,
        "email": "unique@example.com",
        "hashed_password": hash_password("strong-password"),
        "is_active": True,
    }

    with session_factory() as session:
        repository = UserRepository(session)
        assert repository.get_by_id("not-a-uuid") is None
        assert repository.create(user) is not None
        assert repository.get_by_id(user_id)["email"] == "unique@example.com"
        assert repository.create({**user, "id": str(uuid4())}) is None
