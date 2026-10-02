from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.user_repository import UserData, UserRepository
from app.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


def authentication_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[Session, Depends(get_db)],
) -> UserData:
    try:
        user_id = decode_access_token(token)
    except jwt.InvalidTokenError as error:
        raise authentication_error() from error

    user = UserRepository(session).get_by_id(user_id)
    if user is None or not user["is_active"]:
        raise authentication_error()
    return user


CurrentUser = Annotated[UserData, Depends(get_current_user)]
