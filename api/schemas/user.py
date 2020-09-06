from typing import Optional

from pydantic import BaseModel, Field, EmailStr


class UserEmailIn(BaseModel):
    """Email to which an invite should be sent"""

    email: EmailStr


class UserPublicOut(BaseModel):
    """Public user information"""

    username: str
    badge: str
    description: Optional[str]

    class Config:
        orm_mode = True


class UserSelfOut(UserPublicOut):
    """Private user information"""

    email: str
    reset_uuid: Optional[str]
    newsletter_opt_in: bool
    email_subscriptions: bool
    exclude_subscriptions: bool
    colorize_icons: bool


class UserSelfIn(BaseModel):
    """Patch private user information"""

    username: str = Field(
        None, description="How you wish to be known around the site.", max_length=42
    )
    description: str = Field(
        None, description="Supports card codes and star formatting."
    )
    newsletter_opt_in: bool = False
    email_subscriptions: bool = False
    exclude_subscriptions: bool = False
    colorize_icons: bool = False


class UserModerationIn(BaseModel):
    """Moderate a user"""

    username: str = None
    description: str = None
    is_banned: bool = False
    moderation_notes: str = Field(
        ...,
        description="Required notes about what and why moderation actions were taken. May be exposed to the moderated user.",
    )


class UserModerationOut(BaseModel):
    """Response after moderating a user"""

    username: str
    description: Optional[str]
    is_banned: bool
    moderation_notes: str

    class Config:
        orm_mode = True
