from datetime import datetime
from typing import List, Optional, Dict, Any

from vrmapi_async.utils import datetime_to_epoch
from vrmapi_async.client.base.api import BaseNamespace
from .schema import (
    Site,
    UserSitesResponse,
    UserSitesExtendedResponse,
    SiteExtended,
    AccessToken,
    UsersListAccessTokensResponse,
)


class UsersNamespace(BaseNamespace):

    async def get_installations(self, user_id: int) -> List[Site]:
        """
        Fetches the NON-EXTENDED list of sites for the user.

        :param user_id: user_id of the user to fetch sites for
        :returns: A list of Site objects
        """
        url = self.routes.USERS_INSTALLATIONS.format(user_id=user_id)
        response_data = await self._request("GET", url)
        return UserSitesResponse(**response_data).records

    async def get_installations_extended(self, user_id: int) -> List[SiteExtended]:
        """
        Fetches the EXTENDED list of sites for the user.

        :param user_id: user_id of the user to fetch sites for
        :returns: A list of SiteExtended objects
        """
        url = self.routes.USERS_INSTALLATIONS.format(user_id=user_id)
        params = {"extended": "1"}
        response_data = await self._request("GET", url, params=params)
        return UserSitesExtendedResponse(**response_data).records

    async def list_all_access_tokens(self, user_id: int) -> List[AccessToken]:
        """
        Lists all access tokens for the user.
        :param user_id: user_id of the user to fetch access tokens for
        :returns: A list of access token dictionaries
        """
        url = self.routes.USERS_ACCESSTOKENS_LIST.format(user_id=user_id)
        response_data = await self._request("GET", url)
        return UsersListAccessTokensResponse(**response_data).tokens

    async def create_access_token(
        self, user_id: int, name: str, expiry: Optional[int | datetime] = None
    ) -> dict:
        """
        Creates a new access token for the user.

        :param user_id: user_id of the user to create an access token for
        :param name: Name for the new access token
        :param expiry: Optional expiry time for the token, can be an int (epoch time) or a datetime object
        :returns: The created access token dictionary
        """
        url = self.routes.USERS_ACCESSTOKENS_CREATE.format(user_id=user_id)
        params: Dict[str, Any] = {"name": name}
        if expiry:
            params["expiry"] = (
                datetime_to_epoch(expiry) if isinstance(expiry, datetime) else expiry
            )

        response_data = await self._request("POST", url, params=params)
        return response_data
