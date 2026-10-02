from uuid import uuid4

from app.auth_schema import UserRegister
from app.repositories.user_repository import UserData, UserRepository
from app.security import hash_password, verify_password


class EmailAlreadyRegisteredError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class AuthService:
    def __init__(self, repository: UserRepository) -> None:
        self.repository = repository

    def register(self, payload: UserRegister) -> UserData:
        email = payload.email.lower()
        if self.repository.get_by_email(email) is not None:
            raise EmailAlreadyRegisteredError

        user = self.repository.create(
            {
                "id": str(uuid4()),
                "email": email,
                "hashed_password": hash_password(payload.password),
                "is_active": True,
            }
        )
        if user is None:
            raise EmailAlreadyRegisteredError
        return user

    def authenticate(self, email: str, password: str) -> UserData:
        user = self.repository.get_by_email(email.lower())
        if (
            user is None
            or not user["is_active"]
            or not verify_password(password, user["hashed_password"])
        ):
            raise InvalidCredentialsError
        return user
