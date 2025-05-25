# --- vrmapi_async/exceptions.py
"""Custom exceptions for the VRM API client."""


class VRMAPIError(Exception):
    """Base exception class for VRM API errors."""

    pass


class VRMAuthenticationError(VRMAPIError):
    """Raised when authentication fails."""

    pass


class VRMAPIRequestError(VRMAPIError):
    """Raised when an API request fails for reasons other than auth."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_text: str | None = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text

    def __str__(self) -> str:
        parts = [super().__str__()]
        if self.status_code:
            parts.append(f"Status Code: {self.status_code}")
        if self.response_text:
            parts.append(f"Response: {self.response_text}")
        return " - ".join(parts)
