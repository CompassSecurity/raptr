from pydantic import BaseModel, ConfigDict, Field


class OTP(BaseModel):
    """
    OTP Schema
    """

    otp: str = Field(
        ...,
        pattern=r"^\d{6}$",
        min_length=6,
        max_length=6,
        description="6-digit OTP code",
    )

    model_config = ConfigDict(
        json_schema_extra={"example": {"otp": "123456"}},
    )
