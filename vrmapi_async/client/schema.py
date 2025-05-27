from pydantic import BaseModel, Field


class LoginResponse(BaseModel):
    """Response model for successful login."""

    token: str
    id_user: int = Field(..., alias="idUser")
