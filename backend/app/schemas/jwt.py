from pydantic import BaseModel


class Token(BaseModel):
    """
    JWT token response schema
    """

    access_token: str
    token_type: str
    next_url: str


class TokenData(BaseModel):
    """
    JWT token payload data schema
    """

    username: str | None = None
    exp: int | None = None
    iat: int | None = None
    aud: str | None = None
    iss: str | None = None
    mfa_provided: bool | None = None
