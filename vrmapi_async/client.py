# --- vrmapi_async/client.py
"""Main asynchronous client for the Victron VRM API."""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import httpx

from vrmapi_async.exceptions import VRMAuthenticationError, VRMAPIRequestError
from vrmapi_async.models import (
    LoginResponse,
    UserSitesResponse,
    Site,
    UserSitesExtendedResponse,
    SiteExtended,
    ConsumptionStatsResponse,
)
from vrmapi_async.utils import datetime_to_epoch
from vrmapi_async.routes import VRMPaths

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
        base_url: str = "https://vrmapi.victronenergy.com/v2",
        timeout: float = 10.0,
        headers: Optional[Dict[str, str]] = None,
    ):
        """
        Initialise the VRM API client.

        Args:
            username: VRM portal username.
            password: VRM portal password.
            demo: Set to True to use the demo account.
            base_url: The base URL for the VRM API.
            timeout: Default timeout for HTTP requests.
            headers: Optional dictionary of global headers for all requests.
        """
        if not demo and not (username and password):
            raise ValueError(
                "Username and password must be provided unless using demo mode."
            )

        self.username = username
        self.password = password
        self.is_demo = demo
        self.user_id: Optional[int] = None
        self._auth_token: Optional[str] = None
        self.global_headers = headers or {}
        self.paths = VRMPaths()

        self._client: httpx.AsyncClient = httpx.AsyncClient(
            base_url=base_url, timeout=timeout
        )

    async def _login(self) -> None:
        """Logs in using username and password."""
        logger.debug("Attempting to log in with username %s", self.username)
        try:
            response = await self._client.post(
                self.paths.AUTH_LOGIN,
                json={"username": self.username, "password": self.password},
            )
            response.raise_for_status()  # Raises HTTPStatusError for 4xx/5xx
            data = response.json()
            login_data = LoginResponse(**data)
            self._auth_token = login_data.token
            self.user_id = login_data.id_user
            logger.info("Successfully logged in as user %s", self.user_id)
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

    async def _login_as_demo(self) -> None:
        """Logs in using the demo account."""
        logger.debug("Attempting to log in as demo.")
        try:
            response = await self._client.get(self.paths.AUTH_DEMO)
            response.raise_for_status()
            data = response.json()
            data["idUser"] = DEMO_USER_ID  # Ensure demo user ID is set
            login_data = LoginResponse(**data)
            self._auth_token = login_data.token
            self.user_id = login_data.id_user  # Demo user might not have a useful ID
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
        if self.is_demo:
            await self._login_as_demo()
        else:
            await self._login()

    async def aclose(self) -> None:
        """Closes the underlying HTTP client session."""
        await self._client.aclose()

    async def __aenter__(self) -> "VRMAsyncAPI":
        """Async context manager entry: connects and returns self."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit: closes the client."""
        await self.aclose()

    async def _request(
        self,
        method: str,
        url: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Internal wrapper to make authenticated API requests."""
        if not self._auth_token:
            raise VRMAuthenticationError("Not logged in. Call connect() first.")

        request_headers = self.global_headers.copy()
        request_headers["X-Authorization"] = f"Bearer {self._auth_token}"

        logger.debug(
            "Sending %s request to %s with params %s and headers %s",
            method,
            url,
            params,
            request_headers,
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

    async def get_user_sites(self, user_id: Optional[int] = None) -> List[Site]:
        """
        Fetches the NON-EXTENDED list of sites for the user.

        Args:
            user_id: user_id of the user to fetch sites for. If None, uses the logged-in user's ID.

        Returns:
            A list of Site objects.
        """
        user_id = user_id or self.user_id
        if not user_id:
            raise VRMAuthenticationError(
                "User ID not available. Ensure you are logged in."
            )

        url = self.paths.USERS_INSTALLATIONS.format(user_id=user_id)
        response_data = await self._request("GET", url)

        sites_response = UserSitesResponse(**response_data)
        return sites_response.records

    async def get_user_sites_extended(
        self, user_id: Optional[int] = None
    ) -> List[SiteExtended]:
        """
        Fetches the EXTENDED list of sites for the user.

        Args:
            user_id: user_id of the user to fetch sites for. If None, uses the logged-in user's ID.

        Returns:
            A list of SiteExtended objects.
        """
        user_id = user_id or self.user_id
        if not user_id:
            raise VRMAuthenticationError(
                "User ID not available. Ensure you are logged in."
            )

        params = {"extended": "1"}
        url = self.paths.USERS_INSTALLATIONS.format(user_id=user_id)
        response_data = await self._request("GET", url, params=params)

        sites_response = UserSitesExtendedResponse(**response_data)
        return sites_response.records

    async def get_consumption_stats(
        self,
        inst_id: int,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> ConsumptionStatsResponse:
        """
        Fetches consumption statistics for a given site.

        Args:
            inst_id: The installation ID.
            start: Optional start datetime (UTC if naive).
            end: Optional end datetime (UTC if naive).

        Returns:
            A ConsumptionStatsResponse object.
        """
        params: Dict[str, Any] = {"type": "consumption"}
        if start:
            params["start"] = datetime_to_epoch(start)
        if end:
            params["end"] = datetime_to_epoch(end)

        url = self.paths.INSTALLATIONS_STATS.format(inst_id=inst_id)
        response_data = await self._request("GET", url, params=params)
        return ConsumptionStatsResponse(**response_data)
