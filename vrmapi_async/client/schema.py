from pydantic import Field

from vrmapi_async.client.base.schema import BaseResponseModel


class LoginResponse(BaseResponseModel):
    """Response model for successful login."""

    # -- DEFINED BY VRMAPI DOCS --
    token: str
    id_user: int = Field(..., alias="idUser")
    verification_mode: str
    verification_sent: bool
    # -- UNDOCUMENTED --
    status: str
