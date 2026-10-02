from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.auth_schema import Token, UserOut, UserRegister
from app.database import get_db
from app.dependencies import CurrentUser
from app.repositories.user_repository import UserRepository
from app.security import create_access_token
from app.services import (
    AuthService,
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
)

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


def get_auth_service(session: Annotated[Session, Depends(get_db)]) -> AuthService:
    return AuthService(UserRepository(session))


AuthServiceDependency = Annotated[AuthService, Depends(get_auth_service)]


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, service: AuthServiceDependency):
    try:
        return service.register(payload)
    except EmailAlreadyRegisteredError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        ) from error


@router.post("/token", response_model=Token)
def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: AuthServiceDependency,
):
    try:
        user = service.authenticate(form.username, form.password)
    except InvalidCredentialsError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error
    return Token(access_token=create_access_token(user["id"]))


@router.get("/me", response_model=UserOut)
def me(current_user: CurrentUser):
    return current_user
