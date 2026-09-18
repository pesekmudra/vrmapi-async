# --- vrmapi_async/client.py
"""Main asynchronous client for the Victron VRM API."""

import logging
from typing import Optional, Dict, Any, Type
import httpx

from vrmapi_async.exceptions import VRMAuthenticationError, VRMAPIRequestError
from vrmapi_async.client.schema import LoginResponse
from vrmapi_async.routes import VRMRoutes
from vrmapi_async.client.users.api import UsersNamespace
from vrmapi_async.client.installations.api import InstallationsNamespace

logger = logging.getLogger(__name__)

DEMO_USER_ID = 22
DEMO_SITE_ID = 151734


class VRMAsyncAPI:
    """Asynchronous Python client for the Victron VRM API."""

    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        demo: bool = False,
        token: Optional[str] = None,
        user_id_for_token: Optional[int] = None,
        base_url: str = "https://vrmapi.victronenergy.com/v2",
        headers: Optional[Dict[str, str]] = None,
        routes_cls: Type[VRMRoutes] = VRMRoutes,
    ):
        """
        Initialise the VRM API client. You can authenticate via 3 different methods

        1. Credentials: pass `username` and `password`.
        2. Demo: set `demo=True` to use the demo account. This is mostly for testing purposes.
        3. Token: pass `token` and `user_id_for_token` to use a pre-configured API token.

        :param username: Optional VRM portal username to use for credentials auth.
        :param password: Optional VRM portal password to use for credentials auth.
        :param demo: Set to True to use the demo account.
        :token: Optional pre-configured API token for authentication.
        :user_id_for_token: Optional user ID associated with the token. Required if using a token.
        :param base_url: The base URL for the VRM API.
        :param headers: Optional dictionary of global headers for all requests.
        :routes_cls: Optional custom routes class to use for API endpoints if you want to override the default routes.
        """
        auth_methods = sum(
            [
                1 if (username and password) else 0,
                1 if demo else 0,
                1 if (token and user_id_for_token is not None) else 0,
            ]
        )

        if auth_methods == 0:
            raise ValueError(
                "No authentication method provided. Please provide (username/password), demo=True, or (token/user_id_for_token)."
            )
        if auth_methods > 1:
            raise ValueError(
                "Multiple authentication methods provided. Please provide only one: (username/password), demo=True, or (token/user_id_for_token)."
            )

        if (token and not user_id_for_token) or (not token and user_id_for_token):
            raise ValueError("To properly use token authentication, both 'token' and 'user_id_for_token' must be provided.")

        if (username and not password) or (not username and password):
            raise ValueError("To properly use credentials authentication, both 'username' and 'password' must be provided.")

        self.username = username
        self.password = password
        self.is_demo = demo
        self._pre_auth_token = token
        self._pre_auth_user_id = user_id_for_token

        self.user_id: Optional[int] = None
        self._auth_token: Optional[str] = None

        self.global_headers = {"Content-Type": "application/json"}
        self.routes = routes_cls()

        self._client: httpx.AsyncClient = httpx.AsyncClient(base_url=base_url)

        if headers:
            self.global_headers.update(headers)

        if self._pre_auth_token:
            self._auth_mode = "token"
        elif self.is_demo:
            self._auth_mode = "demo"
        else:
            self._auth_mode = "login"

        self.users = UsersNamespace(self._request, self.routes)
        self.installations = InstallationsNamespace(self._request, self.routes)

    async def _login(self) -> None:
        """Logs in using username and password."""
        logger.info(f"Attempting to log in with username {self.username}")
        try:
            response = await self._client.post(
                self.routes.AUTH_LOGIN,
                json={"username": self.username, "password": self.password},
            )
            response.raise_for_status()  # Raises HTTPStatusError for 4xx/5xx
            data = response.json()
            login_data = LoginResponse(**data)
            self._auth_token = login_data.token
            self.user_id = login_data.id_user
            logger.info(f"Successfully logged in as user {self.user_id}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (401, 403):
                raise VRMAuthenticationError(
                    "Authentication failed: Check credentials."
                ) from e
            else:
                raise VRMAPIRequestError(
                    f"Login failed: {e.response.text}",
                    e.response.status_code,
                    e.response.text,
                ) from e
        except Exception as e:
            raise VRMAPIRequestError(
                f"An unexpected error occurred during login: {e}"
            ) from e

    async def _logout(self) -> None:
        logger.info(f"Attempting to log out user {self.username}")
        if not self._auth_token:
            raise VRMAuthenticationError("No active session to log out from. Exiting.")

        if self._auth_mode == "token":
            raise VRMAuthenticationError("Cannot log out when using token authentication. To invalidate the token, you must call the revoke endpoint instead.")

        try:
            response = await self._client.post(
                self.routes.AUTH_LOGOUT,
                headers={"X-Authorization": "Bearer " + self._auth_token},
            )
            response.raise_for_status()
            logger.info(f"Successfully logged out user {self.username}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise VRMAuthenticationError(
                    "Already logged out or session expired."
                ) from e
            else:
                raise VRMAPIRequestError(
                    f"Logout failed: {e.response.text}",
                    e.response.status_code,
                    e.response.text,
                ) from e
        except Exception as e:
            raise VRMAPIRequestError(
                f"An unexpected error occurred during logout: {e}"
            ) from e

    async def _login_as_demo(self) -> None:
        """Logs in using the demo account."""
        logger.debug("Attempting to log in as demo.")
        try:
            response = await self._client.get(self.routes.AUTH_DEMO)
            response.raise_for_status()
            data = response.json()
            data["idUser"] = DEMO_USER_ID  # Ensure demo user ID is set
            login_data = LoginResponse(**data)
            self._auth_token = login_data.token
            # self.user_id = login_data.id_user  # TODO: Demo user might not have a useful ID
            logger.info("Successfully logged in as demo user.")
        except httpx.HTTPStatusError as e:
            raise VRMAPIRequestError(
                f"Demo login failed: {e.response.text}",
                e.response.status_code,
                e.response.text,
            ) from e
        except Exception as e:
            raise VRMAPIRequestError(
                f"An unexpected error occurred during demo login: {e}"
            ) from e

    async def connect(self) -> None:
        """Establishes connection and authenticates to the API."""
        logger.debug(f"Connecting to VRM API with auth mode: {self._auth_mode}")
        if self._auth_mode == "token":
            self._auth_token = self._pre_auth_token
            self.user_id = self._pre_auth_user_id
            logger.info(f"Using pre-configured API token for user {self.user_id}")
        elif self._auth_mode == "demo":
            await self._login_as_demo()
        else:
            await self._login()

    async def disconnect(self) -> None:
        """Logs out (if applicable) and closes the HTTP client session."""
        logger.debug("Attempting to disconnect from VRM API")
        if (
            self._auth_mode == "login" or self._auth_mode == "demo"
        ) and self._auth_token:
            await self._logout()

        self._auth_token = None
        self.user_id = None
        if not self._client.is_closed:
            await self._client.aclose()

    async def __aenter__(self) -> "VRMAsyncAPI":
        """Async context manager entry: connects and returns self."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit: closes the client."""
        await self.disconnect()

    async def _request(
        self,
        method: str,
        url: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        headers: Optional[Dict[str, str]] = None, 
    ) -> Dict[str, Any]:
        """Internal wrapper to make authenticated API requests."""
        if not self._auth_token:
            raise VRMAuthenticationError("Not logged in. Call connect() first.")

        request_headers = self.global_headers.copy()
        request_headers["X-Authorization"] = ("Token " if self._auth_mode == "token" else "Bearer ") + self._auth_token

        if headers:
            request_headers.update(headers)

        logger.debug(
            f"Sending {method} request to {url} with params {params} and headers {request_headers}"
        )

        try:
            response = await self._client.request(
                method, url, headers=request_headers, params=params, json=json_data
            )
            response.raise_for_status()
            json_response = response.json()

            if isinstance(json_response, dict) and not json_response.get(
                "success", True
            ):
                raise VRMAPIRequestError(
                    f"API indicated failure: {json_response.get('errors', 'Unknown error')}",
                    response.status_code,
                    response.text,
                )
            return json_response

        except httpx.HTTPStatusError as e:
            raise VRMAPIRequestError(
                f"API request failed: {e.response.text}",
                e.response.status_code,
                e.response.text,
            ) from e
        except Exception as e:
            raise VRMAPIRequestError(
                f"An unexpected error occurred during request: {e}"
            ) from e
