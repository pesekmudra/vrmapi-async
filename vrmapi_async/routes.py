from dataclasses import dataclass


@dataclass(frozen=True)
class VRMRoutes:
    """Holds all VRM API endpoint path templates."""

    AUTH_LOGIN: str = "/auth/login"
    AUTH_LOGOUT: str = "/auth/logout"
    AUTH_DEMO: str = "/auth/loginAsDemo"

    USERS_INSTALLATIONS: str = "/users/{user_id}/installations"
    USERS_ACCESSTOKENS_LIST: str = "/users/{user_id}/accesstokens/list"
    USERS_ACCESSTOKENS_CREATE: str = "/users/{user_id}/accesstokens/create"

    INSTALLATIONS_STATS: str = "/installations/{site_id}/stats"
    INSTALLATIONS_OVERALL_STATS: str = "/installations/{site_id}/overallstats"
    INSTALLATIONS_DIAGNOSTICS: str = "/installations/{site_id}/diagnostics"

    INSTALLATIONS_WIDGETS: str = "/installations/{site_id}/widgets/{widget_type}"
