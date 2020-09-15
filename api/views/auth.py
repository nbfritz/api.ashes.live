import uuid
import logging

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from api import db
from api.depends import AUTH_RESPONSES, get_session, anonymous_required
from api.environment import settings
from api.exceptions import (
    APIException,
    CredentialsException,
    BannedUserException,
    NotFoundException,
)
from api.models import User
from api.services.user import access_token_for_user
from api.schemas import DetailResponse, auth as schema
from api.schemas.user import UserEmailIn
from api.utils.auth import verify_password
from api.utils.email import send_message


logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/token",
    response_model=schema.AuthTokenOut,
    responses=AUTH_RESPONSES,
)
def log_in(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: db.Session = Depends(get_session),
    _=Depends(anonymous_required),
):
    """Log a user in and return a JWT authentication token to authenticate future requests.

    **Please note:** Only username and password are currently in use, and `username` must be the
    user's registered email. You can ignore the other form fields.
    """
    email = form_data.username.lower()
    user = session.query(User).filter(User.email == email).first()
    if not user or not verify_password(form_data.password, user.password):
        raise CredentialsException(
            detail="Incorrect username or password",
        )
    if user.is_banned:
        raise BannedUserException()
    access_token = access_token_for_user(user)
    return {"access_token": access_token, "token_type": "bearer"}


@router.post(
    "/reset",
    response_model=DetailResponse,
    responses={
        404: {"model": DetailResponse, "description": "Email has not been registered."},
        **AUTH_RESPONSES,
    },
)
def reset_password(
    data: UserEmailIn,
    session: db.Session = Depends(get_session),
    _=Depends(anonymous_required),
):
    """Request a reset password link for the given email."""
    email = data.email.lower()
    user: User = session.query(User).filter(User.email == email).first()
    if user.is_banned:
        raise BannedUserException()
    if not user:
        raise NotFoundException(detail="No account found for email.")
    user.reset_uuid = uuid.uuid4()
    session.commit()
    if not send_message(
        recipient=user.email,
        template_id=settings.sendgrid_reset_template,
        data={"reset_token": user.reset_uuid, "email": user.email},
    ):
        if settings.debug:
            logger.debug(f"RESET TOKEN FOR {email}: {user.reset_uuid}")
        raise APIException(
            detail="Unable to send password reset email; please contact the site owner."
        )
    return {"detail": "A link to reset your password has been sent to your email!"}
