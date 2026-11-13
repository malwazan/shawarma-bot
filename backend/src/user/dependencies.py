from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from src.models import User


def get_current_user(request: Request) -> User:
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    return user


# Use in any endpoint that requires a logged-in user: `user: CurrentUser`
CurrentUser = Annotated[User, Depends(get_current_user)]
